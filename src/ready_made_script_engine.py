import yaml
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, CompositeAudioClip, ColorClip
import random
from openai import OpenAI
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

from .image_handler import ImageHandler
from .video_editor import VideoEditor
from .captions.caption_handler import CaptionHandler

# Update the config loading to use the correct path
current_dir = os.path.dirname(os.path.abspath(__file__))

# Accessing configuration values
openai_api_key = os.getenv('OPENAI_API_KEY')
pexels_api_key = os.getenv('PEXELS_API_KEY')

openai = OpenAI(api_key=openai_api_key)

class ReadyMadeScriptGenerator:
    def __init__(self):
        self.video_editor: VideoEditor = VideoEditor()
        self.image_handler: ImageHandler = ImageHandler(pexels_api_key, openai_api_key)
        self.caption_handler: CaptionHandler = CaptionHandler()
        self.server_info = self.load_server_info()

    def load_server_info(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            info_path = os.path.join(current_dir, '..', 'prompt_templates', 'info.yaml')
            with open(info_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logging.error(f"Error loading server info: {e}")
            return None

    async def generate_script_from_info(self, topic: str = None):
        if not self.server_info:
            return None
        
        # Load paragraph template
        current_dir = os.path.dirname(os.path.abspath(__file__))
        paragraph_path = os.path.join(current_dir, '..', 'prompt_templates', 'paragraph.yaml')
        
        try:
            # Load paragraph content
            with open(paragraph_path, 'r') as file:
                paragraph_content = file.read()
                
                # Split into sentences and select random 200 words
                sentences = [s.strip() for s in paragraph_content.split('.') if s.strip()]
                start_index = random.randint(0, len(sentences) - 1)
                selected_text = []
                word_count = 0
                
                for i in range(start_index, len(sentences)):
                    words = sentences[i].split()
                    if word_count + len(words) > 200:
                        break
                    selected_text.append(sentences[i])
                    word_count += len(words)
                
                paragraph_template = '. '.join(selected_text) + '.'
                
            # Extract key info from server_info
            server_name = self.server_info['server_info']['name']
            tagline = self.server_info['server_info']['tagline']
            key_features = ', '.join(self.server_info['server_info']['key_features'])
            gameplay_exp = ', '.join(self.server_info['server_info']['gameplay_experience'])
            tech_details = self.server_info['server_info']['technical_specs']['performance']
            
            # Create dynamic prompt
            prompt = f"""
            Create a fresh and engaging script for a Minecraft server advertisement. 
            Use the following information as a guide:

            Server Name: {server_name}
            Tagline: {tagline}
            Key Features: {key_features}
            Gameplay Experience: {gameplay_exp}
            Technical Details: {tech_details}

            Paragraph Template: {paragraph_template}

            The script should:
            - Be 100-150 words
            - Focus on the topic: {topic if topic else 'general server features'}
            - Combine information from both the server info and paragraph template
            - Highlight how the server's features enhance the {topic} experience
            - Mention Java/Bedrock compatibility
            - Emphasize the server's capacity and performance
            - Include a strong call to action
            - Maintain a consistent and engaging tone
            """

            # Generate script
            completion = self.video_editor.openrouter.chat.completions.create(
                model="mistralai/mistral-7b-instruct:free",
                temperature=0.7,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content
        
        except Exception as e:
            logging.error(f"Error generating script: {e}")
            return None

    def gpt_summary_of_script(self, video_script: str) -> str:
        try:
            completion = self.video_editor.openrouter.chat.completions.create(
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

    async def create_hook_text_clip(self, hook: str, video_height: int = 720) -> tuple[TextClip, str]:
        try:
            # Generate audio
            hook_audio_path = await self.video_editor.generate_voice(hook)
            hook_audio_clip = AudioFileClip(hook_audio_path)
            hook_audio_duration = hook_audio_clip.duration
            hook_audio_clip.close()

            # Create text clip using Pillow
            text_clip = self.video_editor.create_text_clip(
                text=hook,
                fontsize=int(video_height * 0.03),
                color='black',
                bg_color='white',
                font='Arial'
            ).set_duration(hook_audio_duration)

            return text_clip, hook_audio_path
        except Exception as e:
            logging.error(f"Error creating hook clip: {e}")
            return None, None
        
    async def generate_hook(self, video_script: str) -> str:
        """Generate a hook for the video script."""
        try:

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                temperature=0.25,
                max_tokens=250,
                messages=[
                    {"role": "user", "content": f"Generate a hook for the following video script; it is very important that you keep it to one line. \n Script: {video_script}"}
                ]
            )
            hook = response.choices[0].message.content

            return hook
        except Exception as e:
            logging.error(f"Error generating hook: {e}")
            return ""

    async def generate_video(self, video_path_or_url: str = '', 
                            video_path: str = '', 
                            video_url: str = '', 
                            video_script: str = '',
                            video_hook: str = '',
                            captions_settings: dict = {}, # font, color, font_size, shadow_color
                            add_images: bool = True
                            ) -> dict:
        """Generate a video based on the provided topic or ready-made script.

        Args:
            video_path_or_url (str): 'video_path' or 'video_url', depending on which one is provided.
            video_path (str): The path of the video if provided.
            video_url (str): The URL of the video to download.
            video_script (str): The script of the video.        
            captions_settings (dict): The settings for the captions. (font, color, etc)

        Returns:
            dict: A dictionary with the status of the video generation and a message.
        """
        clips_to_close = []
        try:
            if not video_path_or_url:
                logging.error("video_path_or_url cannot be empty.")
                return {"status": "error", "message": "video_path_or_url cannot be empty."}
                

            if not video_path and not video_url:
                logging.error("Either video_path or video_url must be provided.")
                return {"status": "error", "message": "Either video_path or video_url must be provided."}

            if not video_script:
                video_script = await self.generate_script_from_info()
                if not video_script:
                    return {"status": "error", "message": "Failed to generate script from server info"}
            
            if len(video_script) > 1300:
                logging.error("The video script should not be longer than 1300 characters.")
                return {"status": "error", "message": "The video script should not be longer than 1300 characters."}
            
            if len(video_hook) > 80:
                logging.error("The video hook should not be longer than 80 characters.")
                return {"status": "error", "message": "The video hook should not be longer than 80 characters."}

            """ Download or getting video """
            video_path: str = video_path if video_path_or_url == 'video_path' else self.video_editor.download_video(video_url)
            if not video_path:
                logging.error("No video path provided.")
                return {"status": "error", "message": "No video path provided."}
            # Get video dimensions
            with VideoFileClip(video_path) as video:
                video_width, video_height = video.w, video.h

            """ Handle Script Generation and Process """
            # Load prompt template
            current_dir = os.path.dirname(os.path.abspath(__file__))   
            prompt_template_path = os.path.join(current_dir, '..', 'prompt_templates', 'reddit_thread.yaml')
            if not os.path.exists(prompt_template_path):
                logging.error(f"Prompt template file {prompt_template_path} not found.")
                raise FileNotFoundError(f"Prompt template file {prompt_template_path} not found.")
            # Generate the script or use the provided script
            hook = video_hook if video_hook else await self.generate_hook(video_script)
            youtube_short_story = video_script
            if not youtube_short_story:
                logging.error("Failed to generate script.")
                return {"status": "error", "message": "Failed to generate script."}

            """ Define video length for each clip (question and story) """
            # Initialize Reddit clips
            # Create the Reddit question clip with the actual video width
            hook_text_clip, hook_audio_path = await self.create_hook_text_clip(hook, video_height)
            hook_audio_clip = AudioFileClip(hook_audio_path)
            hook_audio_duration = hook_audio_clip.duration
            clips_to_close.append(hook_audio_clip)
            # Initialize Background video
            background_video_clip = VideoFileClip(video_path)
            clips_to_close.append(background_video_clip)
            background_video_length = background_video_clip.duration
            ## Initialize Story Audio
            story_audio_path = await self.video_editor.generate_voice(youtube_short_story)
            if not story_audio_path:
                logging.error("Failed to generate audio.")
                return {"status": "error", "message": "Failed to generate audio."}

            story_audio_clip = AudioFileClip(story_audio_path)
            clips_to_close.append(story_audio_clip)
            story_audio_length = story_audio_clip.duration
        
            # Calculate video times to cut clips
            max_start_time: float = background_video_length - story_audio_length - hook_audio_duration
            start_time: float = random.uniform(0, max_start_time)
            end_time: float = start_time + hook_audio_duration + story_audio_length
            
            """ Cut video once """
            cut_video_path: str = self.video_editor.cut_video(video_path, start_time, end_time)
            cut_video_clip = VideoFileClip(cut_video_path)
            clips_to_close.append(cut_video_clip)

            """ Handle hook video """
            hook_video = cut_video_clip.subclip(0, hook_audio_duration)
            hook_video = hook_video.set_audio(hook_audio_clip)
            hook_video = self.video_editor.crop_video_9_16(hook_video)

            # Add the text clip to the video
            hook_video = CompositeVideoClip([
                hook_video,
                hook_text_clip.set_position(('center', 'center'))
            ])

            """ Handle story video """
            story_video = cut_video_clip.subclip(hook_audio_duration)
            story_video = story_video.set_audio(story_audio_clip)
            story_video = self.video_editor.crop_video_9_16(story_video)

            font_size = video_width * 0.025

            # Generate subtitles
            story_subtitles_path, story_subtitles_clips = await self.caption_handler.process(
                story_audio_path,
                captions_settings.get('color', 'white'),
                captions_settings.get('shadow_color', 'black'),
                captions_settings.get('font_size', font_size),
                captions_settings.get('font', 'LEMONMILK-Bold.otf')
            )

            video_context = self.gpt_summary_of_script(youtube_short_story)
            story_image_paths = self.image_handler.get_images_from_subtitles(story_subtitles_path, video_context, story_audio_length) if add_images else []
            story_video = self.video_editor.add_images_to_video(story_video, story_image_paths)
            
            story_video = self.video_editor.add_captions_to_video(story_video, story_subtitles_clips)
            # Combine clips
            combined_clips = CompositeVideoClip([
                hook_video,
                story_video.set_start(hook_audio_duration)
            ])

            final_video_output_path = self.video_editor.render_final_video(combined_clips)
            
            # Cleanup: Ensure temporary files are removed
            self.video_editor.cleanup_files([story_audio_path, cut_video_path, story_subtitles_path, hook_audio_path], story_image_paths)
            
            logging.info(f"FINAL OUTPUT PATH: {final_video_output_path}")
            return {"status": "success", "message": "Video generated successfully.", "output_path": final_video_output_path}
        
        except Exception as e:
            logging.error(f"Error in video generation: {e}")
            return {"status": "error", "message": f"Error in video generation: {str(e)}"}
        finally:
            # Close all clips
            for clip in clips_to_close:
                clip.close()


