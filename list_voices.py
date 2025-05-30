from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key="sk_97eae68f8d8d6b878f4c252247ad7226a205aedb52473ea5")  # Replace with your real API key

voices = client.voices.get_all()

for voice in voices.voices:
    print(f"Name: {voice.name} | ID: {voice.voice_id}")