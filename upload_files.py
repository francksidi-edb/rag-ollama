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

# Input for the database IP
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
    
    # Input for the directory path
    directory_path = st.text_input('Enter the directory path to process files:', '')

    # Input for dataset name
    dataset_name = st.text_input('Enter dataset name:', '')

    if directory_path and dataset_name:
        # Button to trigger the processing
        if st.button('Process Files'):
            with conn.cursor() as cur:
                try:
                    # Call the pl-python3u function
                    cur.execute(
                        """
                        SELECT process_files_in_directory(%s, %s);
                        """, (dataset_name, directory_path)
                    )
                    conn.commit()
                    st.success("Files processed and data inserted successfully.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                finally:
                    cur.close()
                    conn.close()
else:
    st.warning("Please enter the database IP to connect.")
