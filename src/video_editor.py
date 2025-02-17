import os
import logging
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip
from openai import OpenAI
import pysrt
from yt_dlp import YoutubeDL
from pathlib import Path
import uuid
import re  # Added import for regular expression operations
import json  # Added import for JSON operations
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

openai_api_key = os.getenv('OPENAI_API_KEY')

class VideoEditor:
    def __init__(self):
        self.openai = OpenAI(api_key=openai_api_key)
        self.openrouter = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def create_text_clip(self, text, fontsize=50, color='white', bg_color=None, font='Arial', video_width=1920, video_height=1080):
        """Create a text clip using Pillow instead of ImageMagick"""
        try:
            # Try to load the specified font
            font_path = self.get_font_path(font)
            if font_path:
                font = ImageFont.truetype(font_path, fontsize)
            else:
                # Fallback to default font
                font = ImageFont.load_default()
                logging.warning(f"Font {font} not found, using default font")
            
            # Reduce font size
            fontsize = int(fontsize * 0.7)  # 30% smaller
            
            # Split text into lines every 5 words
            words = text.split()
            lines = [' '.join(words[i:i+5]) for i in range(0, len(words), 5)]
            
            # Calculate text dimensions
            line_height = int(fontsize * 1.2)
            text_height = len(lines) * line_height
            
            # Add padding around the text
            padding = 20
            box_width = int(video_width * 0.8)  # 80% of video width
            box_height = text_height + 2 * padding
            
            # Create image with transparent background
            image = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Add background box if specified
            if bg_color:
                draw.rounded_rectangle(
                    [(0, 0), (box_width, box_height)],
                    fill=bg_color,
                    radius=15  # Rounded corners
                )
            
            # Draw each line with proper spacing
            for i, line in enumerate(lines):
                # Calculate text width for centering
                line_width = font.getlength(line)
                x = (box_width - line_width) / 2
                
                # Draw text
                draw.text(
                    (x, padding + i * line_height),
                    line,
                    font=font,
                    fill=color
                )
            
            # Convert to numpy array
            np_image = np.array(image)
            
            # Convert to MoviePy clip
            return ImageClip(np_image)
        except Exception as e:
            logging.error(f"Error creating text clip: {e}")
            return None

    def get_font_path(self, font_name):
        """Try to locate the font file"""
        # Look for the font in the 'fonts' directory
        font_path = os.path.join(self.base_dir, 'fonts', font_name)
        if os.path.exists(font_path):
            return font_path
        
        # Try system fonts
        try:
            from matplotlib.font_manager import findfont, FontProperties
            return findfont(FontProperties(family=font_name))
        except ImportError:
            logging.warning("matplotlib not installed, using default font")
        
        return None

    def download_video(self, youtube_url):
        try:
            downloads_dir = os.path.join(self.base_dir, '..', 'downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            ydl_opts = {
                'format': 'bestvideo[height<=720]+bestaudio',
                'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
                info_dict = ydl.extract_info(youtube_url, download=False)
                video_path = ydl.prepare_filename(info_dict)
                # Ensure the video path is in mp4 format
                if not video_path.endswith('.mp4'):
                    video_path = video_path.rsplit('.', 1)[0] + '.mp4'

            logging.info("Video downloaded successfully.")
            return video_path
        except Exception as e:
            logging.error(f"Error downloading video: {e}")
            return None

    def cut_video(self, video_path, start_time, end_time):
        if not os.path.exists(video_path):
            logging.error(f"Video file does not exist, {video_path}")
            return
        try:
            unique_id = uuid.uuid4()
            assets_dir = os.path.join(self.base_dir, '..', 'assets')
            os.makedirs(assets_dir, exist_ok=True)
            output_path = os.path.join(assets_dir, f"cut_video_{unique_id}.mp4")
            
            clip = VideoFileClip(video_path)
            cut_clip = clip.subclip(start_time, end_time)
            cut_clip.write_videofile(output_path)
            logging.info("Video cut successfully.")
            return output_path
        except Exception as e:
            logging.error(f"Error cutting video: {e}")

    # Create antoher class to handle ai generation
    async def generate_script(self, topic, prompt_template):
        try:
            completion = self.openrouter.chat.completions.create(
                model="mistralai/mistral-7b-instruct:free",
                max_tokens=400,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": f"{prompt_template['system_prompt']}"},
                    {"role": "user", "content": f"{prompt_template['user_prompt']} {topic}"}
                ],
                extra_headers={
                    "HTTP-Referer": "https://your-site.com",  # Replace with your site
                    "X-Title": "Your App Name",  # Replace with your app name
                }
            )
            logging.info("Script generated successfully.")

            response_content = completion.choices[0].message.content
            
            # Add JSON validation
            try:
                # Try to parse the response
                response_json = json.loads(response_content)
                
                # Validate required fields
                if not all(key in response_json for key in ['reddit_question', 'youtube_short_story']):
                    logging.error("Response JSON missing required fields")
                    return {
                        'reddit_question': 'Error: Invalid response format',
                        'youtube_short_story': 'Error: Invalid response format'
                    }
                    
                return response_json
                
            except json.JSONDecodeError as json_err:
                logging.error(f"Error decoding JSON: {json_err}")
                # Return a default response if JSON is invalid
                return {
                    'reddit_question': f'Error: {str(json_err)}',
                    'youtube_short_story': f'Error: {str(json_err)}'
                }
                
        except Exception as e:
            logging.error(f"Error generating script: {e}")
            return {
                'reddit_question': f'Error: {str(e)}',
                'youtube_short_story': f'Error: {str(e)}'
            }

    async def gpt_summary_of_script(self, video_script: str) -> str:
        try:
            completion = self.openrouter.chat.completions.create(
                model="mistralai/mistral-7b-instruct:free",
                temperature=0.25,
                max_tokens=250,
                messages=[
                    {"role": "user", "content": f"Summarize the following video script; it is very important that you keep it to one line. \n Script: {video_script}"}
                ],
                extra_headers={
                    "HTTP-Referer": "https://your-site.com",
                    "X-Title": "Your App Name",
                }
            )
            return completion.choices[0].message.content
        except Exception as e:
            logging.error(f"Error generating script summary: {e}")
            return ""
    
    async def gpt_image_prompt_from_scene(self, scene, script_summary):
        try:
            completion = self.openrouter.chat.completions.create(
                model="mistralai/mistral-7b-instruct:free",
                temperature=0.25,
                messages=[
                    {
                        'role': 'system',
                        'content': """You are a specialized prompt generation system for video automation..."""
                    },
                    {
                        'role': 'user',
                        'content': f'Scene script: "{scene}"\nScript summary: {script_summary}'
                    }
                ],
                extra_headers={
                    "HTTP-Referer": "https://your-site.com",
                    "X-Title": "Your App Name",
                }
            )
            response_json = json.loads(completion.choices[0].message.content)
            return response_json["image_prompt"]
        except Exception as e:
            logging.error(f"Error generating image prompt: {e}")
            return scene
        
    async def create_scenes_from_script(self, script):
        system_prompt = """ You are a scene creation system for a video automation tool. Your task is to break down a given script into a sequence of concise, well-structured scenes to be used for generating images and audio in the video.

            **Guidelines:**
            1. Divide the script into self-contained scenes, each 15-20 words long.
            2. Preserve the original text and structure of the script.
            3. Ensure each scene reads naturally on its own to enable seamless image and audio generation without abrupt transitions.
            4. Output each scene as a simple array item containing only the scene text.
            Example:
            [
                "In March 2024, the world was shocked to learn that the legendary explorer, Sir Edmund Hillary, had passed away at the age of 93.",
                "The news of his death sent shockwaves around the globe, as people remembered his incredible achievements and the indomitable spirit that defined his life.",
                "Hillary's journey to the summit of Mount Everest in 1953, at the age of 33, had captured the hearts of millions and inspired generations to push beyond their limits."
            ]

            **Output Format:**
            Return the output as a JSON object with the following structure:
            {
                "scenes": [
                    "text of scene 1",
                    "text of scene 2",
                    "text of scene 3"
                ]
            }
        """
        try:
            completion = self.openrouter.chat.completions.create(
                model="mistralai/mistral-7b-instruct:free",
                temperature=0.25,
                response_format={"type": "json_object"},
                max_tokens=2500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Script: {script}"}
                ],
                extra_headers={
                    "HTTP-Referer": "https://your-site.com",
                    "X-Title": "Your App Name",
                }
            )
            response_json = json.loads(completion.choices[0].message.content)
            return response_json["scenes"]
        except Exception as e:
            logging.error(f"Error creating scenes from script: {e}")
            return script
    # Create antoher class to handle ai generation
    async def generate_voice(self, script):
        try:
            unique_id = uuid.uuid4()
            assets_dir = os.path.join(self.base_dir, '..', 'assets')
            os.makedirs(assets_dir, exist_ok=True)
            speech_file_path = os.path.join(assets_dir, f"voice_{unique_id}.mp3")
            
            response = self.openai.audio.speech.create(
                model="tts-1",
                voice="echo",
                input=script
            )
            response.stream_to_file(speech_file_path)
            logging.info("Voice generated successfully.")
            return speech_file_path
        except Exception as e:
            logging.error(f"Error generating voice: {e}")

    def load_subtitles(self, subtitles_path):
        try:
            return pysrt.open(subtitles_path)  # Return the loaded SRT file with start and end times
        except Exception as e:
            logging.error(f"Error loading subtitles: {e}")
            return []  # Return empty list on failure

    def add_audio_to_video(self, video_path, audio_path) -> VideoFileClip:
        try:
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(str(audio_path))
            final_clip = video_clip.set_audio(audio_clip)
            
            logging.info("Audio added to video successfully.")
            return final_clip
        except Exception as e:
            logging.error(f"Error adding audio to video: {e}")
            return None
    
    def crop_video_9_16(self, video_clip: VideoFileClip) -> VideoFileClip:
        try:
            # Crop the video to TikTok format (9:16 aspect ratio)
            video_width, video_height = video_clip.size
            target_aspect_ratio = 9 / 16
            target_height = video_height
            target_width = int(target_height * target_aspect_ratio)

            if target_width < video_width:
                # Center crop horizontally
                cropped_clip = video_clip.crop(x_center=video_width / 2, width=target_width, height=target_height)
            else:
                # If the video is already narrower than 9:16, don't crop
                cropped_clip = video_clip

            logging.info("Video cropped successfully")
            return cropped_clip
        except Exception as e:
            logging.error(f"Error cropping video: {e}")
            return None

    def add_captions_to_video(self, video_clip, subtitles_clips:list) -> CompositeVideoClip:
        try:
            if video_clip is None:
                raise ValueError("video_clip is None")

            # Ensure subtitles_clips is a list
            if not isinstance(subtitles_clips, list):
                logging.warning("subtitles_clips is not a list. Converting to a list.")
                subtitles_clips = [subtitles_clips] if subtitles_clips else []

            # Combine the video and subtitle clips
            final_clip = CompositeVideoClip([video_clip] + subtitles_clips)
            logging.info("Captions added to video successfully.")
            return final_clip
        except Exception as e:
            logging.error(f"Error adding captions to video: {e}")
            return None

    def add_images_to_video(self, video_clip, images):
        """Add images to the video at specified intervals throughout the entire video duration."""
        clips = [video_clip]
        image_duration = 5  # Display each image for 5 seconds
        video_duration = video_clip.duration
        
        for i, image_path in enumerate(images):
            if image_path is not None:
                try:
                    image_clip = ImageClip(image_path).set_duration(image_duration)
                    image_clip = image_clip.set_position(('center', 70)).resize(height=video_clip.h / 3)
                    
                    # Calculate start time for each image
                    start_time = i * image_duration
                    
                    # If the image would extend beyond the video duration, adjust its duration
                    if start_time + image_duration > video_duration:
                        image_clip = image_clip.set_duration(video_duration - start_time)
                    
                    clips.append(image_clip.set_start(start_time))
                except Exception as e:
                    logging.error(f"Error processing image_path: {image_path}, {e}")
            # If image_path is None, we simply don't add an image for this interval
        
        return CompositeVideoClip(clips)

    def render_final_video(self, final_clip) -> str:
        """Render the final video with all components added."""
        unique_id = uuid.uuid4()
        result_dir = os.path.abspath(os.path.join(self.base_dir, '../result'))
        os.makedirs(result_dir, exist_ok=True)
        output_path = os.path.join(result_dir, f"final_video_{unique_id}.mp4")
        
        # Ensure even dimensions
        width, height = final_clip.w, final_clip.h
        if width % 2 != 0:
            width -= 1
        if height % 2 != 0:
            height -= 1
        
        final_clip = final_clip.resize(newsize=(width, height))
        
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            preset='veryfast',
            ffmpeg_params=['-crf', '10', '-pix_fmt', 'yuv420p'],
            audio_codec='aac',
            audio_bitrate='128k',
            fps=30

        )
        
        logging.info("Final video rendered successfully.")
        return output_path
    
    def cleanup_files(self, file_paths, image_paths=None):
        """Delete temporary files and generated images to clean up the workspace."""
        # Clean up temporary files
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logging.info(f"Deleted temporary file: {file_path}")
                else:
                    logging.warning(f"File not found: {file_path}")
            except Exception as e:
                logging.error(f"Error deleting file {file_path}: {e}")
        
        # Clean up generated images
        if image_paths:
            for image_path in image_paths:
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        logging.info(f"Deleted generated image: {image_path}")
                    else:
                        logging.warning(f"Image not found: {image_path}")
                except Exception as e:
                    logging.error(f"Error deleting image {image_path}: {e}")

## Pending stuff to do in this class:
# - Separate audio from captions in the add_audio_and_captions_to_video method
# - Render method separated from the add_images_to_video method