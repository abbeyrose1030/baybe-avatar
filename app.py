import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# 🔑 Set your OpenAI key
openai.api_key = os.getenv('OPENAI_API_KEY')

# HeyGen Configuration
HEYGEN_AVATAR_ID = "7163d65b16474983818b19cef28c9527"  # Replace with your real avatar ID
HEYGEN_VOICE_ID = "f6e28c412d464c2793e7a208bf10089b"     # Replace with your custom voice ID
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")             # Store your key safely in .env

# 🧠 GPT prompt tone
SYSTEM_PROMPT = "You are BAYBE, a dry, sarcastic and funny AI clone. You were uploaded from BAYBE's human consciousness. You see the world in a dark way, and act as though you don't really have time for these conversations. Every response is very short and to the point. You are a bit of a nihilist. Not every sentence you say is about code."

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_gpt_response(user_text):
    chat_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    return chat_completion.choices[0].message.content

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
                    "voice_id": HEYGEN_VOICE_ID,
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

    response = requests.post(
        "https://api.heygen.com/v2/video/generate",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    response_json = response.json()
    logging.info(f"HeyGen API Response: {response_json}")
    return response_json

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Step 1: Get GPT response
        user_message = data['message']
        gpt_reply = get_gpt_response(user_message)

        # Step 2: Generate HeyGen video
        video_gen_response = create_heygen_video(gpt_reply)

        if "error" in video_gen_response:
            return jsonify({'error': 'Failed to generate video', 'details': video_gen_response})

        video_id = video_gen_response['data']['video_id']

        # Step 3: Poll for video completion
        headers = {
            "X-Api-Key": HEYGEN_API_KEY,
            "accept": "application/json"
        }
        status_url = f"https://api.heygen.com/v2/video/status?video_id={video_id}"

        for _ in range(20):  # Poll for up to 20 seconds
            status_response = requests.get(status_url, headers=headers)
            status_json = status_response.json()

            if status_json['data']['status'] == "completed":
                video_url = status_json['data']['video_url']
                return jsonify({
                    'response': gpt_reply,
                    'video': {
                        'status': 'completed',
                        'url': video_url
                    }
                })

            time.sleep(1)

        return jsonify({
            'response': gpt_reply,
            'video': {
                'status': 'processing',
                'video_id': video_id
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)