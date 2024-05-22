import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser.text import SentenceSplitter
import openai
from llama_index.readers.web import BeautifulSoupWebReader


openai.api_key = 'YOUR-OPENAI-API-KEY-HERE'

# Initialize global settings
Settings.llm = OpenAI(model="gpt-4o", api_key=openai.api_key, 
system_prompt="""
    You are an expert on ThalesDocs. Your job is to answer technical questions accurately based on the documentation available on ThalesDocs.
    Always provide detailed, step-wise information in your responses.
    Ensure that your answers are comprehensive and cover all possible details.
    Do not ask the user to check the website for more details; include all necessary information in your response.
    """)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)

# Initialize message history
st.header("Chat with Thales Docs 💬 📚")

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about Thales Documentation!"}
    ]

# Load and index data from ThalesDocs
@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing ThalesDocs – hang tight!"):
        # Define the URL for ThalesDocs
        URL = "https://www.thalesdocs.com"
        
        # Use BeautifulSoupWebReader to fetch and parse the content
        loader = BeautifulSoupWebReader()
        documents = loader.load_data(urls=[URL])
        
        # Create the vector store index
        index = VectorStoreIndex.from_documents(documents)
        return index

index = load_data()

# Create the chat engine
chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

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
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message)