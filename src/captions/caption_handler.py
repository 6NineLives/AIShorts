import os
import logging
from PIL import Image, ImageFont, ImageDraw
import numpy as np

from .subtitle_generator import SubtitleGenerator
from .video_captioner import VideoCaptioner

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)


class CaptionHandler:
    def __init__(self):
        self.subtitle_generator = SubtitleGenerator()
        self.video_captioner = VideoCaptioner()
        self.default_font = "Dacherry.ttf"

    async def process(self, audio_file: str, captions_color="white", shadow_color="cyan", font_size=60, font=None, width=540):
        subtitles_file = await self.subtitle_generator.generate_subtitles(audio_file)
        caption_clips = self.video_captioner.generate_captions_to_video(
            subtitles_file,
            font=font,
            captions_color=captions_color,
            shadow_color=shadow_color,
            font_size=font_size,
            width=width
        )
        return subtitles_file, caption_clips

    def create_subtitle_clip(self, text, font_size, color, shadow_color, font_path, video_width, video_height):
        try:
            # Load font
            font = ImageFont.truetype(font_path, int(font_size))
            
            # Calculate max characters per line based on video width
            max_chars_per_line = int(video_width / (font_size * 0.6))  # Adjust multiplier as needed
            
            # Split text into lines
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars_per_line:
                    current_line += f" {word}"
                else:
                    lines.append(current_line.strip())
                    current_line = word
            if current_line:
                lines.append(current_line.strip())
            
            # Create text image
            line_height = int(font_size * 1.2)
            text_height = len(lines) * line_height
            text_width = video_width
            
            # Create image with transparent background
            image = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw each line
            for i, line in enumerate(lines):
                # Draw shadow
                draw.text(
                    (5, i * line_height + 5),
                    line,
                    font=font,
                    fill=shadow_color
                )
                # Draw main text
                draw.text(
                    (0, i * line_height),
                    line,
                    font=font,
                    fill=color
                )
            
            # Convert to numpy array
            np_image = np.array(image)
            
            # Create MoviePy clip
            text_clip = ImageClip(np_image, transparent=True)
            
            # Position the text at the bottom center
            position = ('center', video_height - text_height - 50)  # 50px from bottom
            
            return text_clip.set_position(position)
        except Exception as e:
            logging.error(f"Error creating subtitle clip: {e}")
            return None