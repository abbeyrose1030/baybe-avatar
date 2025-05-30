from elevenlabs import generate, VoiceSettings
import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
import tempfile
import requests
import base64
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# 🔑 Set your OpenAI key
openai.api_key = os.getenv('OPENAI_API_KEY')

# HeyGen Configuration
HEYGEN_AVATAR_ID = "7163d65b16474983818b19cef28c9527"
HEYGEN_API_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_API_KEY = "ZWFiN2ZlOTgxNWJiNDM3YzlkY2E5MTlhYWY5ZmJjODMtMTc0NTM4Mjk5Mw=="

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
        api_key=os.getenv("ELEVENLABS_API_KEY")
    )
    return audio

def create_heygen_video(text):
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    payload = {
        "video_inputs": [
            {
                "avatar_id": HEYGEN_AVATAR_ID,
                "voice": {
                    "type": "text",
                    "voice_id": "f6e28c412d464c2793e7a208bf10089b",
                    "input_text": text
                },
                "script": {
                    "type": "text",
                    "input": text
                }
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        },
        "caption": False
    }
    print("Sending HeyGen video payload:", payload)  # Debug print
    try:
        response = requests.post(
            "https://api.heygen.com/v2/video/generate",
            headers=headers,
            json=payload
        )
        print("HeyGen video response status:", response.status_code)  # Debug print
        print("HeyGen video response body:", response.text)  # Debug print
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating HeyGen video: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print("HeyGen error response:", e.response.text)
            return {"error": str(e), "details": e.response.text}
        return {"error": str(e)}

@app.route('/chat', methods=['POST'])
def chat():
    print("==== /chat endpoint called ====")
    api_key = request.headers.get('X-Api-Key')
    print(f"Received API key: {api_key}")  # Debug print
    if not api_key or api_key != HEYGEN_API_KEY:
        return jsonify({'error': 'Invalid or missing API key'}), 401

    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Get GPT response
        response = get_gpt_response(data['message'])
        
        # Create HeyGen video using GPT response as script
        video_data = create_heygen_video(response)
        
        return jsonify({
            'response': response,
            'video': video_data
        })
    except Exception as e:
        import traceback
        print("Exception in /chat endpoint:", e)
        traceback.print_exc()
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

@app.route('/video_status/<video_id>', methods=['GET'])
def video_status(video_id):
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "accept": "application/json"
    }
    url = f"https://api.heygen.com/v2/video/status?video_id={video_id}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching HeyGen video status: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print("HeyGen error response:", e.response.text)
            return {"error": str(e), "details": e.response.text}
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
        