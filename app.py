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

# Debug logging for environment variables
print("=== Environment Variables Check ===")
print(f"OPENAI_API_KEY present: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
print(f"HEYGEN_API_KEY present: {'Yes' if os.getenv('HEYGEN_API_KEY') else 'No'}")
print(f"HEYGEN_API_KEY length: {len(os.getenv('HEYGEN_API_KEY', '')) if os.getenv('HEYGEN_API_KEY') else 0}")
print("=================================")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Validate required environment variables
required_env_vars = ['OPENAI_API_KEY', 'HEYGEN_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# 🔑 Set your OpenAI key
openai.api_key = os.getenv('OPENAI_API_KEY')

# HeyGen Configuration
HEYGEN_AVATAR_ID = "7163d65b16474983818b19cef28c9527"  # Replace with your real avatar ID
HEYGEN_VOICE_ID = "f6e28c412d464c2793e7a208bf10089b"     # Replace with your custom voice ID
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")  # Load from environment variable

# Log HeyGen configuration (redacted for security)
logging.info(f"HeyGen Avatar ID: {HEYGEN_AVATAR_ID}")
logging.info(f"HeyGen Voice ID: {HEYGEN_VOICE_ID}")
logging.info(f"HeyGen API Key present: {'Yes' if HEYGEN_API_KEY else 'No'}")

# Validate HeyGen configuration
if not HEYGEN_AVATAR_ID or not HEYGEN_VOICE_ID:
    raise ValueError("HeyGen Avatar ID and Voice ID must be set")
if not HEYGEN_API_KEY:
    raise ValueError("HeyGen API Key must be set")

# 🧠 GPT prompt tone
SYSTEM_PROMPT = "You are BAYBE, a dry, sarcastic and funny AI clone. You were uploaded from BAYBE's human consciousness. You see the world in a dark way, and act as though you don't really have time for these conversations. Every response is very short and to the point. You are a bit of a nihilist. Not every sentence you say is about code."

def validate_heygen_response(response):
    """Validate the structure of HeyGen API response."""
    if not isinstance(response, dict):
        raise ValueError("HeyGen response must be a dictionary")
    
    if 'data' not in response:
        raise ValueError("HeyGen response missing 'data' field")
    
    if 'video_id' not in response.get('data', {}):
        raise ValueError("HeyGen response missing 'video_id' in data")
    
    return True

def get_gpt_response(user_text):
    """Get response from GPT-4."""
    try:
        chat_completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ]
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"GPT API error: {str(e)}")
        raise

def create_heygen_video(text):
    """Create a video using HeyGen API."""
    headers = {
        "x-api-key": HEYGEN_API_KEY,  # Changed from X-Api-Key to x-api-key
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

    try:
        print("\n=== HeyGen API Request ===")
        print(f"Headers: {headers}")
        print(f"Payload: {payload}")
        print("========================\n")

        response = requests.post(
            "https://api.heygen.com/v2/video/generate",
            headers=headers,
            json=payload
        )
        
        print("\n=== HeyGen API Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        print("==========================\n")

        response.raise_for_status()
        response_json = response.json()
        
        # Validate response
        validate_heygen_response(response_json)
        return response_json
    except requests.exceptions.HTTPError as e:
        print(f"\n=== HeyGen API Error ===")
        print(f"Error: {str(e)}")
        print(f"Response: {e.response.text}")
        print("=======================\n")
        return {'error': f"HeyGen API error: {e.response.text}"}
    except Exception as e:
        print(f"\n=== General Error ===")
        print(f"Error: {str(e)}")
        print("===================\n")
        return {'error': f"HeyGen API error: {str(e)}"}

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests and generate video responses."""
    data = request.json
    logging.info(f"Received chat request: {data}")
    
    if not data or 'message' not in data:
        return jsonify({
            "BAYBE's Response": "Error: No message provided",
            "Video Status": "error"
        }), 400

    try:
        # Step 1: Get GPT response
        user_message = data['message']
        gpt_reply = get_gpt_response(user_message)
        logging.info(f"GPT response: {gpt_reply}")

        # Step 2: Generate HeyGen video
        video_gen_response = create_heygen_video(gpt_reply)

        if "error" in video_gen_response:
            logging.error(f"Video generation failed: {video_gen_response}")
            return jsonify({
                "BAYBE's Response": gpt_reply,
                "Video Status": "error",
                "error": video_gen_response.get('error', 'Failed to generate video')
            })

        video_id = video_gen_response['data']['video_id']
        logging.info(f"Video generation started with ID: {video_id}")

        # Step 3: Poll for video completion
        headers = {
            "X-Api-Key": HEYGEN_API_KEY,
            "accept": "application/json"
        }
        status_url = f"https://api.heygen.com/v2/video/status?video_id={video_id}"

        for attempt in range(20):  # Poll for up to 20 attempts
            try:
                status_response = requests.get(status_url, headers=headers)
                status_response.raise_for_status()
                status_json = status_response.json()
                logging.info(f"Video status check {attempt + 1}: {status_json}")

                if status_json['data']['status'] == "completed":
                    video_url = status_json['data']['video_url']
                    logging.info(f"Video completed: {video_url}")
                    return jsonify({
                        "BAYBE's Response": gpt_reply,
                        "Video Status": "completed",
                        "Video URL": video_url
                    })

                # Exponential backoff with max 5 seconds
                time.sleep(min(1 * (2 ** attempt), 5))
            except requests.exceptions.RequestException as e:
                logging.error(f"Error checking video status: {str(e)}")
                time.sleep(1)

        logging.warning(f"Video generation timed out for ID: {video_id}")
        return jsonify({
            "BAYBE's Response": gpt_reply,
            "Video Status": "processing",
            "Video ID": video_id
        })

    except Exception as e:
        import traceback
        logging.error(f"Error in chat endpoint: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "BAYBE's Response": "Error occurred",
            "Video Status": "error",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)