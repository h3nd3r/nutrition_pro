# NutritionPro aka "What's For Dinner?" Chat Application

This Chainlit-based application serves as a personal nutritional assistant, leveraging large language models (LLMs) to 
provide support in recommending nutritious suggestions for what to eat for dinner. It includes features such as user_info 
input, tracking past conversations, and adaptive responses.

## Features

- **Record Tracking and Ingestion**: Automatically assesses interactions and updates a record for the user, specifically
dinner log, meal preferences, and available ingredients list. This, in turns, feeds into the RAG pipeline to provide
additional context to the LLM.
- **Adaptive Responses**: Uses conversation history and user records to provide context-aware responses.
- **Streamed Responses**: Delivers model responses in real-time as they are generated.
- **Image Ingestion**: Supports image ingestion as another user input to the LLM. This allows user to upload images, such as
their pantry/fridge items, restaurant menu items, or a photo of their dinner plate.
- **Trader Joe's Ingredients**: Utilized web scraping to fetch ingredients from Trader Joes' website.
- **Notion Integration**: Utilizes Notion API to fetch favorite recipes from user's account.
- **Kroger Integration**: Utilizes Kroger API to get a list of items on promo from their local Kroger affiliated grocery store.

## Prerequisites

- Python 3.7+
- API keys for OpenAI (main LLM model) and Langfuse (for tracing and logging)

## Installation and Setup

1. **Clone the Repository**:
   ```sh
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a Virtual Environment**:
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

## Configuration

1. **API Keys**: 
   - Copy the `.env.sample` file and rename it to `.env`
   - Replace the placeholder values with your actual API keys

2. **System Prompts Flag**:
   - Adjust the `ENABLE_SYSTEM_PROMPT` flag as needed.

3. **Customize Prompts**:
   - Modify the prompt templates in the `prompts.py` file to suit your nutrition coaching context.

## Running the Application

1. **Activate the Virtual Environment** (if not already activated):
   ```sh
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

2. **Run the Chainlit App**:
   ```sh
   chainlit run app.py -w
   ```

3. Open your browser and navigate to the URL displayed in the terminal.

## Usage

- Start a conversation with a personalized nutrition coach by typing a message.
- The application will process your input, update your user record, and provide a contextual response.
- User records are automatically updated and stored in `user/user_record.md`.
- If the user completed a new user questionnaire (`user/user_info.md`), it will be used to provide context to the LLM.

## Key Components

- `app.py`: Main application file containing the Chainlit setup and message handling logic.
- `prompts.py`: Contains prompt templates for system instructions and assessments.
- `user_record.py`: Handles reading, writing, and formatting of user records.
- `rag_pipeline.py`: Handles the retrieval of user-specific information from a user_info.md file.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your proposed changes.

## License

This project is licensed under the MIT License.