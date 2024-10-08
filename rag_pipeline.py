# from langfuse import Langfuse
# from langfuse.llama_index import LlamaIndexCallbackHandler
# from langfuse.openai import openai
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager

from langchain.callbacks import LangChainTracer
from langchain.callbacks.manager import CallbackManager as LangChainCallbackManager
from llama_index.core.callbacks import CallbackManager as LlamaIndexCallbackManager
from notion_reader import load_pages

load_dotenv()

class RAGPipeline:

    recipes_index = None

    def __init__(self):
        # Set up LangChain tracer
        self.tracer = LangChainTracer()
        langchain_callback_manager = LangChainCallbackManager([self.tracer])
        
        # Set up LlamaIndex callback manager with LangChain tracer
        self.callback_manager = CallbackManager([self.tracer])
        
        # Update the global Settings for LlamaIndex
        Settings.callback_manager = self.callback_manager

    def retrieve_user_rag_data(self):
        # load_dotenv()

        # langfuse_callback_handler = LlamaIndexCallbackHandler()
        # Settings.callback_manager = CallbackManager([langfuse_callback_handler])

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

    def index_user_favorite_recipes(self):
        # Load the user's favorite recipes from Notion
        documents = load_pages()

        # Create an index from the documents
        self.recipes_index = VectorStoreIndex.from_documents(documents)
        print(f"DEBUG: recipes_index done")

    def query_user_favorite_recipes(self, message_history):
        # Create a query engine
        query_engine = self.recipes_index.as_query_engine()

        query_str = """
            Given the message history, provide one or more favorite recipes that the user may want to consider.
            The message history is: {message_history}
        """

        response = query_engine.query(query_str)
        print(f"response.response: {response.response}")
        
        formatted_response = f"""
            Here are the favorite recipes that the user may want to consider: {response.response}
        """
        return formatted_response
