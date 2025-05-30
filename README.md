# BAYBE Avatar

A chatbot with voice capabilities that can be integrated with HeyGen's virtual avatar platform.

## Features

- GPT-4 powered responses with a unique personality
- ElevenLabs voice synthesis
- Flask web server for API integration
- Ready for HeyGen avatar integration

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   ```

## Running Locally

```bash
python app.py
```

## API Endpoints

- `POST /chat`: Send a message to the chatbot
  - Request body: `{"message": "your message here"}`
  - Response: `{"response": "chatbot's response"}`

## Deployment

This application is configured for deployment on Render.com. See the Render documentation for setup instructions. 