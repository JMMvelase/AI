import os
import pyttsx3
import speech_recognition as sr
import google.generativeai as genai
import pygame
from pygame.locals import QUIT
import textwrap
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY not found in .env file")

# Configure Gemini with system instruction
genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="You are a helpful, friendly AI assistant who speaks clearly and concisely."
)
chat_session = model.start_chat(history=[])

# Init TTS engine
engine = pyttsx3.init()
engine.setProperty('voice', engine.getProperty('voices')[1].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Init Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Avatar Chat")
font = pygame.font.SysFont('Arial', 24)

# Load avatar images
mouth_closed = pygame.image.load('Rem.jpg').convert_alpha()
mouth_open = pygame.image.load('Rem.jpg').convert_alpha()

# Setup Speech Recognition
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Global flag to animate mouth
speaking_flag = threading.Event()

def display_avatar_and_text(text, mouth_state="closed"):
    screen.fill((255, 255, 255))
    avatar = mouth_open if mouth_state == "open" else mouth_closed
    screen.blit(avatar, (350, 50))

    y = 300
    for line in textwrap.wrap(text, width=60):
        screen.blit(font.render(line, True, (0, 0, 0)), (50, y))
        y += 30

    pygame.display.flip()

def animate_mouth():
    while speaking_flag.is_set():
        display_avatar_and_text(current_text, "open")
        time.sleep(0.2)
        display_avatar_and_text(current_text, "closed")
        time.sleep(0.2)

def speak_text(text, stop_event):
    def on_start(name): 
        stop_event.clear()
        speaking_flag.set()
        threading.Thread(target=animate_mouth).start()
    def on_end(name, completed): 
        speaking_flag.clear()
        stop_event.set()

    engine.connect('started-utterance', on_start)
    engine.connect('finished-utterance', on_end)
    engine.say(text)
    engine.runAndWait()

def speak_and_display(text):
    global current_text
    current_text = text
    stop_event = threading.Event()
    thread = threading.Thread(target=speak_text, args=(text, stop_event))
    display_avatar_and_text(text, "open")
    thread.start()
    return thread, stop_event

# Initial greeting
running = True
tts_thread, stop_event = speak_and_display("Hi there! Do you have a question for me?")

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # Wait for TTS to finish before listening
    if (tts_thread is None or not tts_thread.is_alive()) and stop_event and stop_event.is_set():
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Listening...")
            audio = recognizer.listen(source)

        try:
            user_input = recognizer.recognize_google(audio)
            print("User said:", user_input)

            if any(phrase in user_input.lower() for phrase in ["okay thank", "stop"]):
                response_text = "Alright then. Do you have another question you would like to ask?"
            else:
                response = chat_session.send_message(user_input)
                response_text = response.text.replace("*", "")

            tts_thread, stop_event = speak_and_display(response_text)

        except sr.UnknownValueError:
            tts_thread, stop_event = speak_and_display("Sorry, I didn't catch that. Could you please repeat?")
        except sr.RequestError:
            tts_thread, stop_event = speak_and_display("There was an error connecting to the speech recognition service.")

    elif not tts_thread.is_alive():
        display_avatar_and_text("", "closed")

pygame.quit()
