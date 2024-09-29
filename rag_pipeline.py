from langfuse import Langfuse
from langfuse.llama_index import LlamaIndexCallbackHandler
from langfuse.openai import openai
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager

def retrieve_user_rag_data():
    load_dotenv()

    langfuse_callback_handler = LlamaIndexCallbackHandler()
    Settings.callback_manager = CallbackManager([langfuse_callback_handler])

    # Load documents from a directory
    documents = SimpleDirectoryReader("user").load_data()

    # Create an index from the documents
    index = VectorStoreIndex.from_documents(documents)

    # Create a query engine
    query_engine = index.as_query_engine()

    query_str = """
        Provide a comprehensive synopsis of the user's important information.  This will be used
        to provide context when interacting with the user. 
    """
    
    response = query_engine.query(query_str)
    print(f"response.response: {response.response}")
    user_summary = response.response

    query_str = """
        Provide a a summary of any relevent information from the user's previous interactions with
        the system from the alerts, meal preferences, and chat records. 
    """

    response = query_engine.query(query_str)
    print(f"response.response: {response.response}")
    user_interactions_summary = response.response

    formatted_response = f"""
    CONTEXT: This is the user's information as provided by the RAG pipeline: {user_summary + user_interactions_summary}. 
    You should use this information as additional context when responding to the user's query.
    """
    return formatted_response