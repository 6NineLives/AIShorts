import os
import uuid
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

async def generate_voice(script):
    try:
        unique_id = uuid.uuid4()
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'audios')
        os.makedirs(assets_dir, exist_ok=True)
        speech_file_path = os.path.join(assets_dir, f"voice_{unique_id}.mp3")
        
        # Import and initialize ElevenLabs
        from elevenlabs.client import ElevenLabs
        from elevenlabs import save
        
        # Initialize client
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        
        # Generate speech
        audio = client.generate(
            text=script,
            voice="flHkNRp1BlvT73UL6gyz",  # Your custom voice ID
            model="eleven_multilingual_v2"
        )
        
        # Save audio
        save(audio, speech_file_path)
        
        logging.info("Voice generated successfully using ElevenLabs.")
        return speech_file_path
    except Exception as e:
        logging.error(f"Error generating voice: {e}")
