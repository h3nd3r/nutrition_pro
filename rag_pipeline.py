from langfuse import Langfuse
import openai
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

def retrieve_user_fre():
    load_dotenv()

    # Load documents from a directory
    # Note, when I moved the user_record.md file to the user folder, the query engine would only create responses from one document or the other, but never a combination from both.
    documents = SimpleDirectoryReader("user").load_data()

    # Create an index from the documents
    index = VectorStoreIndex.from_documents(documents)

    # Create a query engine
    query_engine = index.as_query_engine()

    langfuse = Langfuse()

    response = query_engine.query("Please give a comprehensive summary of the information provided in the user's records including the user's goals, preferences, and any other relevant information.")
    return response.response
