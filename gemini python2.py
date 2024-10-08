import os
import pyttsx3
import speech_recognition as sr
import google.generativeai as genai  # Assuming this module exists in your environment
import pygame
from pygame.locals import *
import textwrap  # Import textwrap module for wrapping text
import threading  # Import threading for handling TTS interruption
import cv2  # OpenCV for video handling

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Set properties for the text-to-speech engine
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Initialize Pygame for avatar display
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Avatar Chat')

# Load avatar video using OpenCV
video_path = '/mnt/data/345400814-c8b5c59f-0483-42ef-b3ee-4cffae6c7a52.mp4'
video = cv2.VideoCapture(video_path)

# Font setup for displaying text
pygame.font.init()
font = pygame.font.SysFont('Arial', 24)

# Configure generative AI API
api_key = os.environ.get('API_KEY')
if not api_key:
    raise ValueError("API_KEY environment variable not set")
genai.configure(api_key=api_key)

# Generation configuration for the chat session
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Instantiate the generative model for chat
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Create an initial chat session with some history
chat_session = model.start_chat(
    history=[{
        "role": "user",
        "parts": ["profound definition"]
    }, {
        "role": "model",
        "parts": [
            "## Profound Definition:\n\n**Profound** is a word that describes something **deep, intense, and significant**. ..."
        ]
    }]
)

# Initialize the recognizer for speech input
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Function to display avatar video and text on Pygame screen
def display_avatar_and_text(text):
    screen.fill((255, 255, 255))  # Clear screen

    # Read a frame from the video
    ret, frame = video.read()
    if ret:
        frame = cv2.resize(frame, (400, 400))  # Resize the video frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))  # Convert to a Pygame surface
        screen.blit(frame, (screen_width // 2 - 200, 50))  # Display video frame
    
    # Render text using textwrap to wrap lines
    lines = textwrap.wrap(text, width=60)
    y = 500
    for line in lines:
        text_surface = font.render(line, True, (0, 0, 0))
        screen.blit(text_surface, (50, y))
        y += font.get_height() + 5

    pygame.display.flip()  # Update display

# Function to handle text-to-speech in a separate thread
def speak_text(text, stop_event):
    engine.connect('started-utterance', lambda name: stop_event.clear())
    engine.connect('finished-utterance', lambda name, completed: stop_event.set())
    engine.say(text)
    engine.runAndWait()

# Function to handle the speaking in a separate thread
def speak_and_display(text):
    display_avatar_and_text(text)
    stop_event = threading.Event()
    tts_thread = threading.Thread(target=speak_text, args=(text, stop_event))
    tts_thread.start()
    return tts_thread, stop_event

# Main interaction loop
running = True
tts_thread, stop_event = None, None

# Initial greeting
initial_text = "Hi there! Do you have a question for me?"
tts_thread, stop_event = speak_and_display(initial_text)

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
    
    # Listening for user input
    if (tts_thread is None or not tts_thread.is_alive()) and (not stop_event or stop_event.is_set()):
        with microphone as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            # Recognizing speech using Google Web Speech API
            user_input = recognizer.recognize_google(audio)
            print("You said:", user_input)

            if any(phrase in user_input.lower() for phrase in ['okay thank', 'stop']):
                if tts_thread and tts_thread.is_alive():
                    engine.stop()
                    stop_event.set()
                    tts_thread.join()
                    tts_thread, stop_event = None, None
                response_text = "Alright then. Do you have another question you would like to ask?"
            else:
                # Sending user input to the chat session
                response = chat_session.send_message(user_input)
                response_text = response.text.replace("*", "")

            # Displaying response using avatar video in Pygame window
            tts_thread, stop_event = speak_and_display(response_text)

        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            error_text = "Sorry, I didn't catch that. Could you please repeat?"
            tts_thread, stop_event = speak_and_display(error_text)
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            error_text = "I'm having trouble connecting to the speech recognition service. Please try again later."
            tts_thread, stop_event = speak_and_display(error_text)

# Release video capture and close Pygame window
video.release()
pygame.quit()
