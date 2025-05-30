from elevenlabs import generate, VoiceSettings
import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
import tempfile

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# 🔑 Set your OpenAI key
openai.api_key = os.getenv('OPENAI_API_KEY')

# 🧠 GPT prompt tone
SYSTEM_PROMPT = "You are BAYBE, a dry, sarcastic and funny AI clone. You were uploaded from BAYBE's human consciousness. You see the world in a dark way, and act as though you don't really have time for these conversations. Every response is very short and to the point. You are a bit of a nihilist. Not every sentence you say is about code."

def get_gpt_response(user_text):
    chat_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    return chat_completion.choices[0].message.content

def generate_audio(text):
    audio = generate(
        text=text,
        voice="VucGM2AClXcav8Kladjq",
        model="eleven_monolingual_v1",
        voice_settings=VoiceSettings(
            stability=0.8,
            similarity_boost=0.9
        )
    )
    return audio

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        response = get_gpt_response(data['message'])
        audio = generate_audio(response)
        
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
            temp_audio.write(audio)
            temp_audio_path = temp_audio.name
        
        return jsonify({
            'response': response,
            'audio_url': f'/audio/{os.path.basename(temp_audio_path)}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>', methods=['GET'])
def get_audio(filename):
    try:
        return send_file(
            os.path.join(tempfile.gettempdir(), filename),
            mimetype='audio/mpeg'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
        