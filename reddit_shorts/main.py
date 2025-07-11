import os
import tempfile
import json
import requests
import base64
from datetime import datetime
import subprocess
import asyncio
import aiohttp
from typing import List, Dict, Any

# Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
SPEECHIFY_API_KEY = os.getenv('SPEECHIFY_API_KEY', '').strip()
SPEECHIFY_API_URL = 'https://api.sws.speechify.com/v1/audio/speech'

# Voice IDs for different characters
VOICE_IDS = {
    'JOE_ROGAN': 'emily',
    'BARACK_OBAMA': 'emily',
    'BEN_SHAPIRO': 'emily',
    'DONALD_TRUMP': 'emily',
    'JOE_BIDEN': 'emily',
    'KAMALA_HARRIS': 'emily',
    'ANDREW_TATE': 'emily',
    'JORDAN_PETERSON': 'emily',
}

async def get_available_voices():
    """Get available voices from Speechify API"""
    if not SPEECHIFY_API_KEY:
        raise Exception("SPEECHIFY_API_KEY not configured")
    
    headers = {
        'Authorization': f'Bearer {SPEECHIFY_API_KEY}'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.sws.speechify.com/v1/voices', headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get voices: {response.status} - {error_text}")
            
            data = await response.json()
            return data.get('voices', [])

async def generate_transcript(topic: str, agent_a: str, agent_b: str) -> List[Dict[str, str]]:
    """Generate AI conversation transcript using Groq"""
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not configured")
    
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    system_prompt = f"""Create a dialogue for a short-form conversation on the topic of {topic}. The conversation should be between two agents, {agent_a.replace('_', ' ')} and {agent_b}, who should act as extreme, over-the-top caricatures of themselves with wildly exaggerated personality traits and mannerisms. {agent_a.replace('_', ' ')} and {agent_b.replace('_', ' ')} should both be absurdly vulgar and crude in their language, cursing excessively and making outrageous statements to the point where it becomes almost comically over-the-top. The dialogue should still provide insights into {topic} but do so in the most profane and shocking way possible. Limit the dialogue to a maximum of 7 exchanges, aiming for a concise transcript that would last for 1 minute. The agentId attribute should either be {agent_a} or {agent_b}. The text attribute should be that character's line of dialogue. Make it as edgy and controversial as possible while still being funny. Remember, {agent_a} and {agent_b} are both {agent_a.replace('_', ' ')} and {agent_b.replace('_', ' ')} behaving like they would in real life, but more inflammatory. The JSON format WHICH MUST BE ADHERED TO ALWAYS is as follows: {{ "transcript": [ {{"agentId": "the exact value of {agent_a} or {agent_b} depending on who is talking", "text": "their line of conversation in the dialog"}} ] }}"""
    
    user_prompt = f"generate a video about {topic}. Both the agents should talk about it in a way they would, but extremify their qualities and make the conversation risque so that it would be interesting to watch and edgy."
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "model": "llama3-70b-8192",
        "temperature": 0.5,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                raise Exception(f"Groq API error: {response.status}")
            
            data = await response.json()
            content = data['choices'][0]['message']['content']
            parsed = json.loads(content)
            return parsed.get('transcript', [])

async def generate_audio(voice_id: str, person: str, line: str, index: int, output_dir: str) -> str:
    """Generate audio using Speechify TTS"""
    if not SPEECHIFY_API_KEY:
        raise Exception("SPEECHIFY_API_KEY not configured")
    
    # Debug: Check API key (first 10 characters)
    print(f"Using Speechify API key: {SPEECHIFY_API_KEY[:10]}...")
    
    # Use a default voice if the specific voice_id is not set
    if not voice_id or voice_id == 'your_joe_rogan_voice_id':
        voice_id = 'en_us_002'  # Default voice
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {SPEECHIFY_API_KEY}'
    }
    
    payload = {
        'input': line,
        'voice_id': voice_id,
        'audio_format': 'mp3'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(SPEECHIFY_API_URL, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Speechify API error: {response.status} - {error_text}")
            
            data = await response.json()
            if not data.get('audio_data'):
                raise Exception('No audio data received from Speechify')
            
            # Convert base64 to audio file
            audio_buffer = base64.b64decode(data['audio_data'])
            audio_path = os.path.join(output_dir, f'{person}-{index}.mp3')
            
            with open(audio_path, 'wb') as f:
                f.write(audio_buffer)
            
            return audio_path

def create_video_from_audio(audio_files: List[str], output_path: str, background_music: str = None):
    """Create video from audio files using ffmpeg"""
    # Create a temporary file listing all audio files
    temp_list = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    for audio_file in audio_files:
        temp_list.write(f"file '{audio_file}'\n")
    temp_list.close()
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg', '-y',  # Overwrite output
        '-f', 'concat',
        '-safe', '0',
        '-i', temp_list.name,
        '-c', 'copy',
        '-shortest'
    ]
    
    # Add background music if provided
    if background_music and os.path.exists(background_music):
        cmd.extend([
            '-i', background_music,
            '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:weights=1,0.3[a]',
            '-map', '[a]'
        ])
    
    cmd.append(output_path)
    
    # Execute ffmpeg
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return False
    finally:
        os.unlink(temp_list.name)

async def run_local_video_generation(filter=False, voice='en_us_002', background_video=None, background_music=None, title=None, story=None):
    """
    Generate video using AI-powered transcript and TTS
    """
    if not title or not story:
        raise Exception("Title and story are required")
    
    # Create temporary directory for audio files
    temp_dir = tempfile.mkdtemp()
    voice_dir = os.path.join(temp_dir, 'voice')
    os.makedirs(voice_dir, exist_ok=True)
    
    try:
        # Get available voices first
        print("Getting available voices...")
        try:
            available_voices = await get_available_voices()
            print(f"Found {len(available_voices)} available voices")
            
            # Use first available voice as fallback
            fallback_voice = available_voices[0]['voice_id'] if available_voices else 'en_us_002'
        except Exception as e:
            print(f"Warning: Could not get available voices: {e}")
            fallback_voice = 'en_us_002'
        
        # Generate transcript using AI
        print("Generating transcript...")
        transcript = await generate_transcript(story, 'JOE_ROGAN', 'BEN_SHAPIRO')
        
        # Generate audio for each line
        print("Generating audio...")
        audio_files = []
        for i, entry in enumerate(transcript):
            agent_id = entry['agentId']
            text = entry['text']
            voice_id = VOICE_IDS.get(agent_id, fallback_voice)
            
            # Use fallback if voice_id is not set or is placeholder
            if not voice_id or voice_id.startswith('your_') or voice_id == 'your_joe_rogan_voice_id':
                voice_id = fallback_voice
            
            print(f"Generating audio for {agent_id} with voice {voice_id}")
            audio_path = await generate_audio(voice_id, agent_id, text, i, voice_dir)
            audio_files.append(audio_path)
        
        # Create final video
        print("Creating video...")
        video_filename = f"generated_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        video_path = os.path.join(temp_dir, video_filename)
        
        # For now, create audio-only video (you can enhance this with visual elements)
        success = create_video_from_audio(audio_files, video_path, background_music)
        
        if success and os.path.exists(video_path):
            # Copy to a permanent location
            final_path = os.path.join('uploads', video_filename)
            os.makedirs('uploads', exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(video_path, final_path)
            
            return final_path
        else:
            raise Exception("Failed to create video")
            
    except Exception as e:
        print(f"Error in video generation: {e}")
        raise
    finally:
        # Cleanup temporary files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True) 