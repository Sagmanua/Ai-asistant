import ollama
import speech_recognition as sr
import asyncio
import edge_tts
import os
import sys
import subprocess
import signal
from contextlib import contextmanager

# --- Configuration ---
VOICE = "en-US-GuyNeural" 
OUTPUT_FILE = "response.mp3"

# Global variable to track the audio process
audio_process = None

@contextmanager
def ignore_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    os.dup2(devnull, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(devnull)

async def speak(text):
    global audio_process
    print(f"Assistant: {text}")
    
    # Stop any current speaking before starting new one
    stop_speaking()
    
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(OUTPUT_FILE)
    
    # Start playing in the background
    audio_process = subprocess.Popen(
        ["mpg321", "-q", OUTPUT_FILE], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )

def stop_speaking():
    """Kills the background audio process immediately."""
    global audio_process
    if audio_process and audio_process.poll() is None:
        audio_process.terminate()
        audio_process = None

def get_ai_response(user_text):
    print("Thinking...")
    try:
        response = ollama.chat(model='llama3.2:1b', messages=[
            {'role': 'user', 'content': user_text},
        ])
        return response['message']['content']
    except Exception as e:
        return f"Ollama Error: {e}"

async def main_loop():
    r = sr.Recognizer()
    
    # Increase this to let you pause longer between words without being cut off
    r.pause_threshold = 1.5 
    
    is_active = False 
    await speak("System online. Standby mode.")

    while True:
        with ignore_stderr():
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                try:
                    # If active, we give you 15 seconds to talk. 
                    # If standby, we keep it at 3 seconds for quick wake-word detection.
                    limit = 30 if is_active else 3
                    
                    audio = r.listen(source, timeout=None, phrase_time_limit=limit)
                    text = r.recognize_google(audio, language="en-US").lower()
                except Exception:
                    continue

        # --- INTERRUPT LOGIC ---
        if "stop" in text:
            stop_speaking()
            if is_active:
                print("!!! Interrupted: Going to standby.")
                is_active = False
            continue

        # --- WAKE WORD ---
        if "assistant" in text:
            stop_speaking() 
            is_active = True
            print("--- Active (Listening for long sentences) ---")
            
            # Clean the wake word out
            text = text.replace("assistant", "").strip()
            
            # If you ONLY said "Assistant", it will ask what you need
            if not text:
                await speak("I'm listening. Go ahead.")
                continue
            
        # --- RESPONSE LOGIC ---
        if is_active and text:
            print(f"\nYou said: {text}")
            answer = get_ai_response(text)
            await speak(answer)
            
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        stop_speaking()
        print("\nExit.")