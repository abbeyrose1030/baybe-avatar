from TTS.api import TTS
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from openai import OpenAI
import tempfile
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import time

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# 🔑 Set your OpenAI key
gpt_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 🧠 GPT prompt tone
SYSTEM_PROMPT = "You are BAYBE, a dry, sarcastic and funny AI clone. You were uploaded from BAYBE's human consciousness. You see the world in a dark way, and act as though you don't really have time for these conversations. Every response is very short and to the point. You are a bit of a nihilist. Not every sentence you say is about code."

# 🎙 Load local Coqui TTS voice
print("Loading TTS model (this might take a sec)...")
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

def get_gpt_response(user_text):
    chat_completion = gpt_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    return chat_completion.choices[0].message.content

client = ElevenLabs(
    api_key=os.getenv('ELEVENLABS_API_KEY')
)

def speak(text):
    print("\nBAYBE:", text)
    audio = client.text_to_speech.convert(
        voice_id="VucGM2AClXcav8Kladjq",
        model_id="eleven_monolingual_v1",
        text=text,
        voice_settings=VoiceSettings(
            stability=0.8,
            similarity_boost=0.9
        )
    )
    from elevenlabs import play
    play(audio)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        response = get_gpt_response(data['message'])
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    print("\n🤖 BAYBE Chat Terminal")
    print("Type 'quit' or 'exit' to end the conversation\n")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye! 👋")
                break
                
            if not user_input:
                continue
                
            response = get_gpt_response(user_input)
            speak(response)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue

if __name__ == "__main__":
    # Check if we're running in production (Render)
    if os.getenv('RENDER'):
        # Run the Flask app
        port = int(os.getenv('PORT', 10000))
        app.run(host='0.0.0.0', port=port)
    else:
        # Run the terminal version
        main()
        