from langfuse import Langfuse
from langfuse.llama_index import LlamaIndexCallbackHandler
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from functions.notion_reader import load_pages

load_dotenv()

class RAGPipeline:

    recipes_index = None

    def __init__(self):
        langfuse_callback_handler = LlamaIndexCallbackHandler()
        Settings.callback_manager = CallbackManager([langfuse_callback_handler])

    def retrieve_user_rag_data(self):
        # Load documents from a directory
        documents = SimpleDirectoryReader("user").load_data()

        # Create an index from the documents
        index = VectorStoreIndex.from_documents(documents)

        # Create a query engine
        query_engine = index.as_query_engine()

        query_str = """
            Provide a summary of any relevant information from the user's previous interactions with
            the system with regards to their meal preferences.
        """

        response = query_engine.query(query_str)
        print(f"response.response meal preferences: {response.response}")
        user_meal_preferences_summary = response.response

        formatted_response = f"""
        CONTEXT: This is the user's information as provided by the RAG pipeline: {user_meal_preferences_summary}.
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

        query_str = f"""
        Given the message history, provide one or more favorite recipes that the user may want to consider.
        The message history is: {message_history}
        """

        response = query_engine.query(query_str)
        print(f"response.response: {response.response}")
        
        formatted_response = f"""
            Here are the favorite recipes that the user may want to consider: {response.response}
        """
        return formatted_response
