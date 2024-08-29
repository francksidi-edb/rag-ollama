CREATE OR REPLACE FUNCTION process_files_in_directory(
    dataset_name VARCHAR,
    directory_path VARCHAR
) RETURNS VOID AS $$

import os
import time
import pdfplumber
import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader

# Initialize timing for the function start
function_start_time = time.time()

# Load the model with caching using the SD dictionary
model_loading_start = time.time()
if 'cached_model' not in SD:
    try:
        # Assuming ollama.embeddings directly initializes or needs a model loading function
        SD['cached_model'] = ollama.embeddings(model="mxbai-embed-large", prompt="")
        plpy.notice("Model 'mxbai-embed-large' loaded and cached successfully.")
    except Exception as e:
        plpy.error(f"Failed to load model: {str(e)}")

model_loading_end = time.time()
plpy.notice(f"Model loading time: {model_loading_end - model_loading_start:.2f} seconds.")

# Use the cached model
model = SD['cached_model']

# Prepare the SQL insert statement
insert_plan = plpy.prepare(f"""
    INSERT INTO edb_{dataset_name} (content, embedding, filename)
    VALUES ($1, $2, $3)
""", ["text", "vector", "text"])

# List all files in the specified directory
file_list = os.listdir(directory_path)

# Process each file
for filename in file_list:
    file_path = os.path.join(directory_path, filename)

    # Check if the file is a PDF
    if filename.lower().endswith('.pdf'):
        file_processing_start = time.time()

        try:
            # Load the PDF and process it
            loader = PyPDFLoader(file_path)
            document = loader.load()

            # Split the document into chunks
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                model_name="gpt-4",
                chunk_size=100,
                chunk_overlap=10,
            )
            chunks = text_splitter.split_documents(document)

            # Process each chunk and store the vectors in the database
            for row in chunks:
                try:
                    # Get embeddings using the cached model
                    response = ollama.embeddings(model="mxbai-embed-large", prompt=row.page_content.replace('\x00', ''))
                    embedding = response["embedding"]

                    # Attempt to encode the content to UTF-8
                    content_utf8 = row.page_content.replace('\x00', '').encode('utf-8', 'ignore').decode('utf-8')

                    # Insert the processed data using the prepared plan
                    plpy.execute(insert_plan, [content_utf8, embedding, filename])

                except Exception as e:
                    plpy.warning(f"Failed to process chunk in file {filename}: {str(e)}")

        except Exception as e:
            plpy.warning(f"Failed to process file {filename}: {str(e)}")

        # Log processing time for each file
        file_processing_end = time.time()
        plpy.notice(f"Processed file {filename} in {file_processing_end - file_processing_start:.2f} seconds.")

# Final timing
end_time = time.time()
plpy.notice(f"Total processing time: {end_time - function_start_time:.2f} seconds.")

$$ LANGUAGE plpython3u;
