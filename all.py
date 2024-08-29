import streamlit as st
import psycopg2
from psycopg2 import sql

# Set the page configuration first
st.set_page_config(
    page_title="RAG",
    page_icon="/users/francksidi/downloads/logo.png",  # Ensure the icon path is correct
    layout="wide",
)

# Display the logo using st.image
st.image("/users/francksidi/downloads/logo.png", use_column_width=True)

# Sidebar input for database IP
db_ip = st.sidebar.text_input('Database IP', '')

if db_ip:
    # Database connection
    conn = psycopg2.connect(
        user="postgres",
        password="admin",
        host=db_ip,
        port=5432,
        database="postgres"
    )
    
    # Main input fields for both functionalities
    st.header("Process Files")

    # Option 1: Upload files directly
    st.subheader("Upload PDF Files to Process")
    dataset_name = st.text_input('Enter dataset name for uploaded files:', '')
    uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
    truncate = st.checkbox('Truncate table before upload')

    if st.button('Upload and Process Files'):
        if uploaded_files and dataset_name:
            with conn.cursor() as cur:
                try:
                    # Truncate table if checkbox is selected
                    if truncate:
                        cur.execute(sql.SQL("DROP TABLE IF EXISTS edb_{}").format(sql.Identifier(dataset_name)))
                        cur.execute(sql.SQL("CREATE TABLE edb_{} (id bigserial PRIMARY KEY, filename varchar(1024), content TEXT, embedding vector(1024))").format(sql.Identifier(dataset_name)))
                    
                    for uploaded_file in uploaded_files:
                        # Example of calling a Python function for processing
                        # Here we assume you have a similar Python function in your database or defined in your script
                        cur.execute(
                            sql.SQL("SELECT process_files_in_directory(%s, %s)"), 
                            (dataset_name, uploaded_file.name)
                        )
                    conn.commit()
                    st.success("Files processed and data inserted successfully.")
                except Exception as e:
                    st.error(f"An error occurred while processing files: {e}")
                finally:
                    cur.close()
                    conn.close()
        else:
            st.warning("Please upload files and enter a dataset name.")

    # Option 2: Specify a directory for processing
    st.subheader("Process Files from a Directory")
    directory_path = st.text_input('Enter the directory path to process files:', '')
    dataset_name_for_directory = st.text_input('Enter dataset name for directory files:', '')

    if st.button('Process Directory Files'):
        if directory_path and dataset_name_for_directory:
            with conn.cursor() as cur:
                try:
                    # Call the pl-python3u function
                    cur.execute(
                        """
                        SELECT process_files_in_directory(%s, %s);
                        """, (dataset_name_for_directory, directory_path)
                    )
                    conn.commit()
                    st.success("Files processed and data inserted successfully.")
                except Exception as e:
                    st.error(f"An error occurred while processing directory files: {e}")
                finally:
                    cur.close()
                    conn.close()
        else:
            st.warning("Please enter a directory path and dataset name.")
else:
    st.warning("Please enter the database IP to connect.")
