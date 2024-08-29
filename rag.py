import streamlit as st
import psycopg2
import ollama
from psycopg2 import sql

st.logo("logo.png", link="https://www.enterprisedb.com/")
st.set_page_config(
    page_title="RAG",
    page_icon="logo.png",
    layout="wide",
)

# Input for the database IP
db_ip = st.sidebar.text_input('dbip', '')

if len(db_ip) > 0:
    conn = psycopg2.connect(
        user="postgres",
        password="edb",
        host=db_ip,
        port=5432,  # The port you exposed in docker-compose.yml
        database="testdb"
    )

    options = []
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name 
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name LIKE 'edb_%'
            """
        )
        
        for row in cur.fetchall():
            options.append(row[0])
        cur.close()
    
    selected_dataset = st.sidebar.selectbox(
        "select dataset",
        options,
    )
    
    # Initialize chat history
    debug_response = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if user_question := st.chat_input("What's on your mind?"):
        # Add user message to chat history
        with st.chat_message("user"):
            st.session_state.messages.append({"role": "user", "content": user_question})
            st.markdown(user_question)
    
        with st.chat_message("assistant"):
            my_bar = st.progress(0, text="Searching the knowledgebase...")
            with my_bar:
                # Get query embedding
                query_embedding = ollama.embeddings(model="mxbai-embed-large", prompt=user_question)
                query_result = ""
                
                with conn.cursor() as cur:
                    # Execute the similarity search query
                    cur.execute(
                        sql.SQL("""SELECT id, content, 1-(embedding <=> %s::vector) DIST
                            FROM {}
                            WHERE (1-(embedding <=> %s::vector)) > 0.6
                            ORDER BY DIST DESC LIMIT 20;""").format(sql.Identifier(selected_dataset)),
                        [query_embedding["embedding"], query_embedding["embedding"]]
                    )
                    
                    for row in cur.fetchall():
                        query_result = query_result + "|" + row[1]
                        debug_response += f"****{row[0]}####{row[2]}>>>>> {row[1]}"
                        
                    debug_response = debug_response.replace('"', '').replace("'", "").replace(":", "").replace("\n", "")
                    conn.close()
                
                # Generate the response using the retrieved data
                tmp = [{"role": "user", "content": f"Use this retrieved data: {query_result}. to answer this question: {user_question}"}]
                my_bar.progress(5, text="generating augmented response")
                output = ollama.chat(
                    model='llama3.1',
                    messages=tmp,
                    stream=True,
                )
                
                response = ""
                progress = 5
                for chunk in output:
                    response += chunk['message']['content']
                    progress = min((100, progress + 1))
                    my_bar.progress(progress, text="streaming augmented response")
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                my_bar.empty()
                st.markdown(response)
    
    # Debugging script
    js2 = f"""
    <script>
        function debug(message_to_log){{
            if(message_to_log!='')
               console.log("EDB response "+message_to_log);
        }}
        
        debug("{debug_response}");
    </script>
    """
    
    st.components.v1.html(js2)
