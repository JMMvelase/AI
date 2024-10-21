from flask import Flask, render_template, request, jsonify
import pyttsx3
import speech_recognition as sr
import google.generativeai as genai
import threading
import os

app = Flask(__name__)

# Initialize TTS Engine
engine = pyttsx3.init()
engine.setProperty('voice', engine.getProperty('voices')[1].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Configure generative AI API
api_key = os.environ.get('API_KEY')
if not api_key:
    raise ValueError("API_KEY environment variable not set")
genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192
    }
)
chat_session = model.start_chat(history=[])

recognizer = sr.Recognizer()

# Function to process speech input
def recognize_speech():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I didn't understand that."
    except sr.RequestError as e:
        return f"Error: {e}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    response = chat_session.send_message(user_input)
    return jsonify({'response': response.text.replace('*', '')})

@app.route('/tts', methods=['POST'])
def tts():
    text = request.json.get('text', '')
    stop_event = threading.Event()
    tts_thread = threading.Thread(target=engine.say, args=(text,))
    tts_thread.start()
    return jsonify({'status': 'speaking'})

if __name__ == '__main__':
    app.run(debug=True)
