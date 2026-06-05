import ollama
import speech_recognition as sr
import asyncio
import edge_tts
import os
import sys
import subprocess
import json
from datetime import datetime
from contextlib import contextmanager

# --- Configuration ---
VOICE = "en-US-GuyNeural"  # Change to "ru-RU-DmitryNeural" if you want fluent Russian speech
OUTPUT_FILE = "response.mp3"
TRAIN_FILE = "train.jsonl"
LOG_FILE = "chat_log.json"

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
    
    stop_speaking()
    
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(OUTPUT_FILE)
    
    audio_process = subprocess.Popen(
        ["mpg321", "-q", OUTPUT_FILE], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )

def stop_speaking():
    global audio_process
    if audio_process and audio_process.poll() is None:
        audio_process.terminate()
        audio_process = None

def load_local_knowledge():
    """Loads the JSONL file containing quick preset reactions/events."""
    knowledge = []
    if not os.path.exists(TRAIN_FILE):
        return knowledge
    
    try:
        with open(TRAIN_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    knowledge.append(json.loads(line))
    except Exception as e:
        print(f"Error loading {TRAIN_FILE}: {e}")
    return knowledge

def get_local_response(user_text, knowledge_base):
    """Checks if the user's input matches any event keywords in the JSONL."""
    user_text_lower = user_text.lower()
    for item in knowledge_base:
        event_trigger = item.get("event", "").lower()
        if event_trigger in user_text_lower or user_text_lower in event_trigger:
            return item.get("reaction")
    return None

def get_ai_response(user_text):
    print("Thinking...")
    try:
        response = ollama.chat(model='llama3.2:1b', messages=[
            {'role': 'user', 'content': user_text},
        ])
        return response['message']['content']
    except Exception as e:
        return f"Ollama Error: {e}"

def log_interaction(user_input, assistant_output, source):
    """Appends the conversation exchange to a JSON log file."""
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source, # Tells you if it came from 'jsonl' or 'ollama'
        "user": user_input,
        "assistant": assistant_output
    }
    
    logs = []
    # Load existing logs if file exists
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.append(log_entry)
    
    # Save back to file with nice formatting
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

async def main_loop():
    r = sr.Recognizer()
    r.pause_threshold = 1.5 
    is_active = False 
    
    knowledge_base = load_local_knowledge()
    print(f"Loaded {len(knowledge_base)} quick reactions from {TRAIN_FILE}.")
    
    await speak("System online. Standby mode.")

    while True:
        with ignore_stderr():
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                try:
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
            print("--- Active ---")
            text = text.replace("assistant", "").strip()
            
            if not text:
                await speak("I'm listening. Go ahead.")
                continue
            
        # --- RESPONSE & LOGIC ---
        if is_active and text:
            print(f"\nYou said: {text}")
            
            # 1. Try local JSONL file
            answer = get_local_response(text, knowledge_base)
            source_type = "jsonl"
            
            # 2. Fall back to Ollama AI
            if not answer:
                answer = get_ai_response(text)
                source_type = "ollama"
                
            # 3. Log the interaction to the file
            log_interaction(text, answer, source_type)
            
            await speak(answer)
            
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        stop_speaking()
        print("\nExit.")