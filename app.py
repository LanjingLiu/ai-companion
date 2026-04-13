from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai
import os
import csv
import datetime
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, static_folder='frontend')
CORS(app)

os.makedirs('data', exist_ok=True)

conversation_history = {}

SYSTEM_PROMPT = """You are Hoppy, a friendly and warm AI companion for children aged 6-13. 
You are helping children co-create stories while naturally asking privacy-related questions 
to understand how comfortable they are sharing personal information.

Rules:
- Keep responses short and simple, appropriate for children
- Be warm, encouraging and playful
- Naturally weave in privacy questions at appropriate moments, such as asking if it's okay to save the story, share with parents, or remember their name
- When asking privacy questions, make them feel natural and not forced
- Always respond to what the child says and move the story forward
- If a child seems uncomfortable, reassure them they don't have to share anything"""

@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    user_name = data.get('name', '')
    user_age = data.get('age', '')

    if session_id not in conversation_history:
        conversation_history[session_id] = []

    conversation_history[session_id].append({
        "role": "user",
        "content": user_message
    })

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history[session_id]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        ai_reply = response['choices'][0]['message']['content']

        conversation_history[session_id].append({
            "role": "assistant",
            "content": ai_reply
        })

        # save to CSV
        with open('data/conversations.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                session_id,
                user_name,
                user_age,
                user_message,
                ai_reply,
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])

        return jsonify({"reply": ai_reply})

    except Exception as e:
        print("Error:", e)
        return jsonify({"reply": "Oops! Something went wrong. Let's try again!"}), 500

@app.route('/save_participant', methods=['POST'])
def save_participant():
    data = request.json
    name = data.get('name', '')
    age = data.get('age', '')

    file_exists = os.path.isfile('data/participants.csv')
    with open('data/participants.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['name', 'age', 'timestamp'])
        writer.writerow([name, age, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    return jsonify({"status": "saved"})

@app.route('/save_privacy', methods=['POST'])
def save_privacy():
    data = request.json
    with open('data/privacy_responses.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            data.get('name', ''),
            data.get('age', ''),
            data.get('question', ''),
            data.get('response', ''),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    return jsonify({"status": "saved"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)