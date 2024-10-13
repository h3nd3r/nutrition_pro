import os
from langfuse import Langfuse
from langfuse.llama_index import LlamaIndexCallbackHandler
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from functions.notion_reader import load_pages

load_dotenv()

user_info_file_path = "user/user_info.md"

class RAGPipeline:

    recipes_index = None

    def __init__(self):
        langfuse_callback_handler = LlamaIndexCallbackHandler()
        Settings.callback_manager = CallbackManager([langfuse_callback_handler])

    def get_user_info(self):
        formatted_user_info = ""

        # read user info from user/user_info.md
        if not os.path.exists(user_info_file_path):
            print(f"File {user_info_file_path} does not exist")
            formatted_user_info = "CONTEXT: No user personal information found"
        else:
            with open(user_info_file_path, "r") as file:
                user_info = file.read()
                formatted_user_info = f"""
                CONTEXT: This is the user's personal information: \n{user_info}.
                """

        return formatted_user_info

    def retrieve_user_rag_data(self):
        # Load documents from a directory
        documents = SimpleDirectoryReader("user").load_data()

        # Create an index from the documents
        index = VectorStoreIndex.from_documents(documents)

        # Create a query engine
        query_engine = index.as_query_engine()

        meal_preferences_query_str = """
            Provide a summary of any relevant information from the user's previous interactions with
            the system with regards to their meal preferences.
        """

        response = query_engine.query(meal_preferences_query_str)
        print(f"response.response meal preferences: {response.response}")
        user_meal_preferences_summary = response.response

        ingredients_list_query_str = """
            Provide a comprehensive list of ingredients that the user has available to them as well as any
            ingredients they may be out of or missing.
        """

        response = query_engine.query(ingredients_list_query_str)
        print(f"response.response ingredients list: {response.response}")
        user_ingredients_list_summary = response.response

        formatted_response = f"""
        CONTEXT: This is the user's information as provided by the RAG pipeline:
        - User meal preferences: {user_meal_preferences_summary}.
        - User ingredients list: {user_ingredients_list_summary}.
        You should use this information as additional context when responding to the user's query.
        """
        print(f"DEBUG: formatted_response from retrieve_user_rag_data: {formatted_response}")
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
