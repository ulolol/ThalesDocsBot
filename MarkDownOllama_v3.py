import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser.text import SentenceSplitter
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core import StorageContext, load_index_from_storage
import os
import nest_asyncio

#local Imports
import webFetch
import dataPrimer


nest_asyncio.apply()


# Initialize global settings
Settings.llm = Ollama(
    model="phi3-128k:latest",
    base_url="http://localhost:11434",
    request_timeout=120.0,
    ollama_additional_kwargs={
        "system": "You are an expert on ThalesDocs. Your job is to answer technical questions accurately based on the documentation available on ThalesDocs. \
        Always provide detailed, step-wise information in your responses.\
        Ensure that your answers are comprehensive and cover all possible details. \
        Do not ask the user to check the website for more details; include all necessary information in your response. \
        make sure that all info is formatted to be STEP-WISE with details. \
            Always provide detailed breakdown of the responses requested by the user"
    }
)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="nomic-ai/nomic-embed-text-v1", trust_remote_code=True, 
    cache_folder='./HFCache'
)
Settings.node_parser = SentenceSplitter(chunk_size=2048, chunk_overlap=20)

rerank = FlagEmbeddingReranker(model="BAAI/bge-reranker-base", top_n=7)

chatmemory = ChatMemoryBuffer.from_defaults(token_limit=8192)

# Initialize message history
st.header("Chat with Thales Docs 💬 📚")

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about Thales Documentation!"}
    ]


# Load and index data from Markdown files in the 'markdown' directory
@st.cache_resource(show_spinner=False)
def load_data():
    """
    Load and index data from Markdown files in the 'markdown' directory or load 
    an existing index from disk.

    Returns:
        VectorStoreIndex: The loaded or newly created vector store index.
    """
    persistent_dir = "ThalesDocsIndex"  # Define persistent directory

    # Check if the directory exists and is not empty
    if os.path.exists(persistent_dir) and os.listdir(persistent_dir):
        with st.spinner(text="Loading Index from Disk – hang tight!"):
            print(f"Rebuilding Storage Context from Directory: {persistent_dir}...")
            storage_context = StorageContext.from_defaults(persist_dir=persistent_dir)

            print("Loading new Index from Disk...")
            new_index = load_index_from_storage(storage_context, show_progress=True)   

            return new_index

    else:
        with st.spinner(text="Building and Loading Index – hang tight!"):
            # Define the directory containing the Markdown files
            markdown_directory = 'markdown'

            # Initialize SimpleDirectoryReader to read Markdown files
            reader = SimpleDirectoryReader(markdown_directory, required_exts=[".md"])

            # Load documents from the directory
            documents = reader.load_data(show_progress=True, num_workers=4)

            # Create the vector store index from the loaded documents
            index = VectorStoreIndex.from_documents(documents, show_progress=True, use_async=True)

            return index


if __name__ == '__main__':
    #multiprocessing.freeze_support()  # Only necessary if you plan to freeze your script into an executable
    index = load_data()

    # Create the chat engine
    chat_engine = index.as_chat_engine(chat_mode="condense_plus_context", 
    verbose=True, node_postprocessors=[rerank], streaming=True, memory=chatmemory)

    # Prompt for user input and display message history
    if prompt := st.chat_input("Your question"):
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Pass query to chat engine and display response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_engine.chat(prompt)

                #perform a Web Search on ThalesDocs site if data not in Index
                if "The documents provided do not contain information" or \
                    "The index provided does not contain information" in response:
                    response = "Data not found in Index.... \n \
                    Checking ThalesDocs site for latest data...."
                    st.write(response)
                    web_data = webFetch.fetch_and_save_articles(prompt)
                    web_data = dataPrimer.clean_markdown_file(web_data, is_file=False)
                    web_data = web_data[:10000] if len(web_data) > 10000 else web_data
                    response = chat_engine.chat(f"{prompt} \n \
                        Relevant Context: {web_data}")

                st.write(response.response)
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message)