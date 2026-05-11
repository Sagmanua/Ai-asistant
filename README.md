# AI assistant 
## Use 
This is a sript is create that you can do your own AI assisant and conect your own AI. It work more loke "Ok Google" or "Siri".
Your can ask what you want and it answer you 

## Prerequisites

Before running the script, ensure you have the following installed:

1. AI asistant 
In my case is Ollama you can use what you what 
Download and install Ollama. Once installed, pull the model used in the script:
```
ollama pull llama3.2:1b
```

2. System Dependencies (Linux/macOS)
The script uses mpg321 to play audio files.

* Ubuntu/Debian: sudo apt-get install mpg321

* macOS: brew install mpg321

* Windows: You may need to replace mpg321 in the code with a local player like ffplay (from FFmpeg) or a Python library like playsound.


## How it work 
You need to run a sript of `app.py` you can here `System online. Standby mode` that mean that sript is work
after than you can said `Asistant` you can here this `I'm listening. Go ahead.`

if you want to stop when bot is talk to your respond just said `Stop` it dont turn off sript just stop audio answer of your questing 

## Setings 

### seting be defult
`Assistant` - call a Asistant that can help you 

`Stop` - stop convercion of sript but dont off it 


### code setings 

`text = r.recognize_google(audio, language="en-US").lower()` here you can change the language of what will be detect by sript 

`VOICE = "en-US-GuyNeural"` this is what actor is will be use to answer 

`r.pause_threshold = 1.5` pause longer between words without being cut off

`limit = 30 if is_active else 3` what time sript will be listening a sript 

`OUTPUT_FILE = "response.mp3"`in what file is saving answear 

`if "assistant" in text:` word that start of listening a questing 

`if "stop" in text:` word that stop of talking of Assistant 


this is where you can change a model of AI 
```
response = ollama.chat(model='llama3.2:1b', messages=[
    {'role': 'user', 'content': user_text},
])
```


##  Installation
1. Clone the repository:

Bash
git clone https://github.com/yourusername/voice-assistant.git
cd voice-assistant
2. Create a virtual environment (Recommended):

Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
2. Install Python packages:

Bash
pip install ollama speechrecognition edge-tts asyncio
2. Note: You may also need PyAudio for microphone support:
Bash```
pip install pyaudio
```