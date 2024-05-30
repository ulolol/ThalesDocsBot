from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser.text import SentenceSplitter

import os
import nest_asyncio

nest_asyncio.apply()

Settings.embed_model = HuggingFaceEmbedding(
    model_name="nomic-ai/nomic-embed-text-v1", trust_remote_code=True, 
    cache_folder='./HFCache'
)
Settings.node_parser = SentenceSplitter(chunk_size=2048, chunk_overlap=20)


if __name__ == '__main__':
    # Define the directory containing the Markdown files
    markdown_directory = 'markdown'

    # Initialize SimpleDirectoryReader to read Markdown files
    reader = SimpleDirectoryReader(markdown_directory, required_exts=[".md"])

    # Load documents from the directory
    documents = reader.load_data(show_progress=True, num_workers=12)

    # Create the vector store index from the loaded documents
    index = VectorStoreIndex.from_documents(documents, show_progress=True, 
    insert_batch_size=2048)        


    # Persist index to disk
    print(f"Saving Index to Disk Directory: {markdown_directory}...")
    index.storage_context.persist("ThalesDocsIndex")

    # Rebuild storage context
    print("Rebuilding Storage Context...")
    storage_context = StorageContext.from_defaults(persist_dir="ThalesDocsIndex")

    # Load index from the storage context
    print("Loading new Index from Disk...")
    new_index = load_index_from_storage(storage_context, show_progress=True)