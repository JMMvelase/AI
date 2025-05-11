from flask import Flask, render_template, request, jsonify
import pyttsx3
import threading
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

# Configure TTS
engine = pyttsx3.init()
engine.setProperty('voice', engine.getProperty('voices')[1].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Configure Gemini
api_key = os.environ.get('API_KEY')
if not api_key:
    raise ValueError("API_KEY not set")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")
chat_session = model.start_chat(history=[])

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    response = chat_session.send_message(user_input)
    clean_text = response.text.replace('*', '')
    return jsonify({'response': clean_text})

@app.route('/tts', methods=['POST'])
def tts():
    text = request.json.get('text', '')
    threading.Thread(target=lambda: engine.say(text) or engine.runAndWait()).start()
    return jsonify({'status': 'speaking'})

if __name__ == '__main__':
    app.run(debug=True)
