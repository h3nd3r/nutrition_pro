import os
from dotenv import load_dotenv
from notion_client import Client
from typing import List
from llama_index.core.schema import Document
import random
import pdb
load_dotenv()

notion = Client(auth=os.getenv("NOTION_API_KEY"))

# Retrieve all children page IDs associated with the parent page
def retrieve_children_page_ids():
    parent_id = os.getenv("NOTION_PARENT_PAGE_ID")
    print(f"DEBUG: parent_id: {parent_id}")

    try:
        # get all pages incl parent and children
        data = notion.search(query="")

        children_page_ids = []
        # Extract id and title for each page
        for page in data.get('results', []):
            page_id = page.get('id', '')

            # sometimes the id has hyphens, so we need to standardize
            page_id_no_hyphens = page_id.replace("-", "")
            parent_id_no_hyphens = parent_id.replace("-", "")

            if page_id and page_id_no_hyphens != parent_id_no_hyphens:
                properties = page.get('properties', {})
                title_property = properties.get('title', {})
                title_list = title_property.get('title', [])
                title = ''
                if title_list:
                    title = title_list[0].get('plain_text', '')
                page_data = {
                    "page_id": page_id,
                    "title": title
                }
                children_page_ids.append(page_data)

        print(f"DEBUG: children_page_ids: {children_page_ids}")
        return children_page_ids
    except Exception as e:
        print(f"DEBUG: Error, failed to retrieve children page ids: {e}")
        raise Exception(f"Error: Failed to retrieve children page ids: {e}")

# Retrieve a random page's content from the workspace
def retrieve_random_page_content():
    try:
        children_page_ids = retrieve_children_page_ids()

        if not children_page_ids:
            print("DEBUG: No child pages found.")
            return "Error: Failed to retrieve content for a random page."

        random_page_id = random.choice(children_page_ids).get("page_id", '')
        if random_page_id:
            return retrieve_page_content(random_page_id)
        else:
            print("DEBUG: No random page id found.")
            return f"Error: Failed to retrieve content for a random page."
    except Exception as e:
        print(f"DEBUG: Error in retrieve_random_page_content: {e}")
        return f"Error: Failed to retrieve content for a random page."

# Load pages from the workspace into a list[Document]
# TODO: implement max_pages and pagination
def load_pages() -> List[Document]:
    try:
        children_page_ids = retrieve_children_page_ids()

        if not children_page_ids:
            print("DEBUG: No child pages found.")
            return []
        
        pages = []
        for page in children_page_ids:
            page_content = retrieve_page_content(page.get("page_id", ''))
            if page_content:
                pages.append(Document(text=page_content, metadata={"page_id": page.get("page_id", ''), "title": page.get("title", '')}))

        # print(f"DEBUG: pages: {pages}")
        return pages
    except Exception as e:
        print(f"DEBUG: Error in load_pages: {e}")
        return []

# Retrieve page content associated with the page_id
def retrieve_page_content(page_id):
    block_id = page_id # The page_id is also the id of the page's root block
    try:
        blocks = notion.blocks.children.list(block_id=block_id)

        formatted_content = ""
        for block in blocks.get('results', []):
            block_type = block.get('type', '')
            if block_type == 'paragraph':
                rich_text = block.get('paragraph', {}).get('rich_text', [])
                if rich_text:
                    text = rich_text[0].get('plain_text', '')
                    if text:
                        formatted_content += f"{text}\n"
            elif block_type in ['heading_1', 'heading_2', 'heading_3']:
                rich_text = block.get(block_type, {}).get('rich_text', [])
                if rich_text:
                    text = rich_text[0].get('plain_text', '')
                    if text:
                        formatted_content += f"{text}\n"
            elif block_type == 'bulleted_list_item':
                rich_text = block.get('bulleted_list_item', {}).get('rich_text', [])
                if rich_text:
                    text = rich_text[0].get('plain_text', '')
                    if text:
                        formatted_content += f"{text}\n"
            elif block_type == 'numbered_list_item':
                rich_text = block.get('numbered_list_item', {}).get('rich_text', [])
                if rich_text:
                    text = rich_text[0].get('plain_text', '')
                    if text:
                        formatted_content += f"{text}\n"
            else:
                # there are other block types, but we don't need them for this mvp
                print(f"DEBUG: Unsupported block type: {block_type}")

        # print(f"DEBUG: formatted_content: {formatted_content}")
        return formatted_content
    except Exception as e:
        print(f"Error: Failed to retrieve page content: {e}")
        return f"Error: Failed to retrieve page content for page_id: {page_id}"


# To test the function, uncomment the following line:
# retrieve_page_content("117082cd-fa9d-80e3-8173-e54a018de451")
# retrieve_random_page_content()
# load_pages()
