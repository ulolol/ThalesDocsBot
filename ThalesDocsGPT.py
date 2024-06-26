import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser.text import SentenceSplitter
import openai
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from llama_index.core.memory import ChatMemoryBuffer

#local Imports
import webFetch
import dataPrimer


openai.api_key = 'OpenAI API Key'

# Initialize global settings
Settings.llm = OpenAI(model="gpt-4o", api_key=openai.api_key, 
system_prompt="""
    You are an expert on ThalesDocs. Your job is to answer technical questions accurately based on the documentation available on ThalesDocs.
    Always provide detailed, step-wise information in your responses.
    Ensure that your answers are comprehensive and cover all possible details.
    Do not ask the user to check the website for more details; include all necessary information in your response.
    """)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
Settings.node_parser = SentenceSplitter(chunk_size=2048, chunk_overlap=20)

rerank = FlagEmbeddingReranker(model="BAAI/bge-reranker-base", top_n=7)

chatmemory = ChatMemoryBuffer.from_defaults(token_limit=4096)

# Initialize message history
st.header("Chat with Thales Docs 💬 📚")

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about Thales Documentation!"}
    ]


# Load and index data from ThalesDocs
@st.cache_resource(show_spinner=False)
def load_data():
    """
    Load and index data from Markdown files in the 'markdown' directory.

    This function reads Markdown files, loads their content, and builds a vector store index based on the documents.

    Returns:
        VectorStoreIndex: The vector store index created from the loaded documents.
    """
    with st.spinner(text="Building and Loading Index – hang tight!"):
        # Define the directory containing the Markdown files
        markdown_directory = '../markdown'

        # Initialize SimpleDirectoryReader to read Markdown files
        reader = SimpleDirectoryReader(markdown_directory, required_exts=[".md"])

        # Load documents from the directory
        documents = reader.load_data(show_progress=True, num_workers=12)

        # Create the vector store index from the loaded documents
        index = VectorStoreIndex.from_documents(documents, show_progress=True, 
        insert_batch_size=2048)
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
                    #Use only first 3000 chars as context, to prevent 
                    #too much data being sent to GPT
                    web_data = web_data[:3000] if len(web_data) > 3000 else web_data
                    response = chat_engine.chat(f"{prompt} \n \
                        Relevant Context: {web_data}")

                st.write(response.response)
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message)