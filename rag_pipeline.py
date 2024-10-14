import os
import openai
from langfuse import Langfuse
from langfuse.llama_index import LlamaIndexCallbackHandler
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from functions.notion_reader import load_pages
from config import MODEL_CONFIGURATIONS, CONFIG_KEY

load_dotenv()

user_info_file_path = "user/user_info.md"

config = MODEL_CONFIGURATIONS[CONFIG_KEY]
gen_kwargs = {
    "model": config["model"],
    "temperature": 0.3,
    "max_tokens": 500
}

class RAGPipeline:

    recipes_index = None
    client = wrap_openai(openai.Client(api_key=config["api_key"], base_url=config["endpoint_url"]))

    def __init__(self):
        langfuse_callback_handler = LlamaIndexCallbackHandler()
        Settings.callback_manager = CallbackManager([langfuse_callback_handler])

    @traceable
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

    @traceable
    def retrieve_user_rag_data(self):
        # Load documents from a directory
        documents = SimpleDirectoryReader("user").load_data()

        # Create an index from the documents
        index = VectorStoreIndex.from_documents(documents)

        # Create a query engine
        query_engine = index.as_query_engine()

        meal_preferences_query_str = """
            Provide a summary of the user's meal preferences based on the user's previous interactions
            with the system, as specified in the Meal Preferences section of the user's record.
        """

        response = query_engine.query(meal_preferences_query_str)
        print(f"response.response meal preferences: {response.response}")
        user_meal_preferences_summary = response.response

        ingredients_list_query_str = """
            Provide a comprehensive list of ingredients that the user has available to them, taking into account
            any ingredients they may be out of or missing.

            For example: if user mentioned they have steak in the prior conversation, but they are out of steak now,
            then the ingredients list should reflect that the user is out of steak.
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

    @traceable
    def index_user_favorite_recipes(self):
        # Load the user's favorite recipes from Notion
        documents = load_pages()

        # Create an index from the documents
        self.recipes_index = VectorStoreIndex.from_documents(documents)
        print(f"DEBUG: recipes_index done")

    @traceable
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

    # Use the user's dinner log and message history to provide feedback on
    # how they're doing in meeting their nutrition goals
    @traceable
    def query_user_nutritional_goals_performance(self, message_history, num_days=7):
        # Load documents from a directory
        documents = SimpleDirectoryReader("user").load_data()

        # Create an index from the documents
        index = VectorStoreIndex.from_documents(documents)

        # Create a query engine
        query_engine = index.as_query_engine()

        dinner_log_query_str = f"""
        Given the user's Dinner Log from the user's record, provide a comprehensive list of their dinner log
        within the last {num_days} days (or less if the history is less than {num_days} days).
        """

        dinner_log_summary_response = query_engine.query(dinner_log_query_str)
        dinner_log_summary = dinner_log_summary_response.response
        print(f"response.response dinner log summary response: {dinner_log_summary}")

        query_str = f"""
        Given the user's Dinner Log from the user's record and the message history, analyze the user's eating habits and
        provide feedback on how they're doing in meeting their nutritional goals in the last {num_days} days (or less if
        the history is less than {num_days} days).
        The user's Dinner Log is: {dinner_log_summary}
        The message history is: {message_history}
        """

        response = self.client.chat.completions.create(messages=[{"role": "system", "content": query_str}], **gen_kwargs)
        try:
            feedback_output = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error: retrieving feedback on user's nutritional goals performance: {e}")
            feedback_output = "No feedback available"

        formatted_response = f"""
        CONTEXT: Based on user's Dinner Log and message history, this is the feedback on how the user's doing in meeting their
        nutritional goals: {feedback_output}
        """
        print(f"DEBUG: formatted_response from query_user_nutritional_goals_performance: {formatted_response}")
        return formatted_response