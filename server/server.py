from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

os.environ["OPENAI_API_KEY"] = "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"

app = Flask(__name__)
CORS(app)


def create_llama_index():
    try:
        index_dir = 'index'  # Specify the directory your index will be stored
        os.makedirs(index_dir, exist_ok=True)

        from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
        documents = SimpleDirectoryReader("uploads").load_data()
        index = GPTVectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=index_dir)
        if not os.path.exists(index_dir) or not os.listdir(index_dir):
            return jsonify({'error':  "Error: in indexing document"})
        return jsonify({'result': 'File indexed successfully'})
    except Exception as e:
        return jsonify({'error':  f"An error occurred: {e}"})

# this creates a custom prompt to be used in quering the index


def get_custom_prompt():
    try:
        from llama_index.prompts import Prompt
        return Prompt("""\
Rephrase the conversation and subsequent message into 
a self-contained question while including all relevant details. 
Conclude the question with: Only refer to this document.

<Chat History> 
{chat_history}

<Follow Up Message>
{question}

<Standalone question>
""")
    except Exception as e:
        # If an error occurs during the try block, catch it here
        return jsonify({'error':  f"An error occurred: {e}"})

# creates chat history


def getChatHistory(history='[]'):
    try:
        from llama_index.llms import ChatMessage, MessageRole
        history = json.loads(history)

        # initialize chart history
        custom_chat_history = []
        roles = {"left_bubble": "ASSISTANT", "right_bubble": "USER"}
        for chat in history:
            position = chat['position']
            role = MessageRole[roles[position]]
            content = chat['message']
            custom_chat_history.append(
                ChatMessage(
                    # can be USER or ASSISTANT
                    role=role,
                    content=content
                )
            )
        return custom_chat_history
    except Exception as e:
        # If an error occurs during the try block, catch it here
        return jsonify({'error':  f"An error occurred: {e}"})


def query_index():
    # retrive open ai key
    try:
        from llama_index import StorageContext, load_index_from_storage
        from llama_index.chat_engine import CondenseQuestionChatEngine

        index_dir = 'index'

        if not os.path.exists(index_dir) or not os.listdir(index_dir):
            return jsonify({'error':  f"Index directory '{index_dir}' does not exist or is empty."})
        data = request.get_json()
        prompt = data.get('prompt')
        chatHistory = data.get('chatHistory')
        
        storage_context = StorageContext.from_defaults(persist_dir=index_dir)
        index = load_index_from_storage(storage_context)
        query_engine = index.as_query_engine()
        chat_engine = CondenseQuestionChatEngine.from_defaults(
            query_engine=query_engine,
            condense_question_prompt=get_custom_prompt(),
            chat_history=getChatHistory(chatHistory),
            verbose=True
        )

        response_node = chat_engine.chat(prompt)  # chat here
        return jsonify({'result':  response_node.response})

    except Exception as e:
        return jsonify({'error':  f"An error occurred: {e}"})


@app.route('/')
def hello_world():
    return jsonify({'result':  "Hello world"})


@app.route('/ask_ai', methods=['POST'])
def query_endpoint():
    response = query_index()
    return response


@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        upload_dir = 'uploads'  # Specify the directory where you want to save uploaded files
        os.makedirs(upload_dir, exist_ok=True)

        file.save(os.path.join(upload_dir, "data.txt"))

        return create_llama_index()


if __name__ == '__main__':
    app.run()
