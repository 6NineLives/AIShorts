import logging
import os
import pysrt
import uuid
import whisper
from whisper.utils import get_writer
import re

from .utils import convert_seconds_to_srt_time

class SubtitleGenerator:
    def __init__(self):
        # Load the Whisper model (you can choose between 'tiny', 'base', 'small', 'medium', 'large')
        self.model = whisper.load_model("base")
        self.convert_seconds_to_srt_time = convert_seconds_to_srt_time
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    async def generate_subtitles(self, audio_file: str):
        try:
            subtitles = await self.speech_to_text(audio_file)
            srt_file = pysrt.SubRipFile()

            for index, (start, end, text) in enumerate(subtitles):
                srt_file.append(pysrt.SubRipItem(index=index + 1, start=start, end=end, text=text))
            
            unique_id = uuid.uuid4()
            output_dir = os.path.join(self.base_dir, 'assets')
            output_file = os.path.join(output_dir, f'subtitles_{unique_id}.srt')
            srt_file.save(output_file)
            
            logging.info("Subtitles generated and saved successfully.")
            return output_file  # Return the path to the saved SRT file
        except Exception as e:
            logging.error(f"Error generating subtitles: {e}")
            return None

    async def speech_to_text(self, audio_file: str):
        try:
            logging.info(f"Starting transcription for {audio_file}")
            result = self.model.transcribe(audio_file, word_timestamps=True, verbose=True)
            
            if not result.get('segments'):
                logging.error("No segments found in transcription result")
                return []
            
            logging.info(f"Transcription completed with {len(result['segments'])} segments")
            
            subtitles = []
            
            # Process all segments
            for segment in result['segments']:
                for word_info in segment['words']:
                    word_start_time = self.convert_seconds_to_srt_time(word_info['start'])
                    word_end_time = self.convert_seconds_to_srt_time(word_info['end'])
                    
                    # Apply text corrections
                    corrected_word = self.process_text_corrections(word_info['word'].strip())
                    
                    # Create a subtitle for each word
                    subtitles.append((word_start_time, word_end_time, corrected_word))
            
            logging.info(f"Generated {len(subtitles)} word-by-word subtitles")
            return subtitles
        except Exception as e:
            logging.error(f"Error in speech-to-text transcription: {e}")
            return []

    async def generate_subtitles_for_translation(self, audio_file):
        try:
            subtitles = await self.speech_to_text_for_translation(audio_file)
            srt_file = pysrt.SubRipFile()

            for index, (start, end, text) in enumerate(subtitles):
                srt_file.append(pysrt.SubRipItem(index=index + 1, start=start, end=end, text=text))
            
            unique_id = uuid.uuid4()
            output_dir = os.path.join(self.base_dir, 'assets')
            output_file = os.path.join(output_dir, f'subtitles_{unique_id}.srt')
            srt_file.save(output_file)
            
            logging.info("Subtitles generated and saved successfully.")
            return output_file  # Return the path to the saved SRT file
        except Exception as e:
            logging.error(f"Error generating subtitles: {e}")
            return None

    async def speech_to_text_for_translation(self, audio_file):
        try:
            audio_file = open(audio_file, "rb")  # Open the audio file
            transcript = self.openai.audio.transcriptions.create(  # Use OpenAI's transcription method
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
            subtitles = []
            current_words = []
            subtitle_start_time = None

            for word_info in transcript.words:
                word_start_time = self.convert_seconds_to_srt_time(word_info.start)
                word_end_time = self.convert_seconds_to_srt_time(word_info.end)
                
                # Apply text corrections
                corrected_word = self.process_text_corrections(word_info.word.strip())
                
                current_words.append(corrected_word)

                if subtitle_start_time is None:
                    subtitle_start_time = word_start_time

                current_words.append(word_info.word.strip())

                #check if current subtitle is long enough or if the next word is too long
                if len(current_words) >= 8:
                    formatted_text = " ".join(current_words[:4]) + "\n" + " ".join(current_words[4:])
                    subtitles.append((subtitle_start_time, word_end_time, formatted_text))
                    current_words = []
                    subtitle_start_time = None

            # Handle any remaining word
            if current_words:
                formatted_text = " ".join(current_words[:4])
                if len(current_words) > 4:
                    formatted_text += "\n" + " ".join(current_words[4:])
                subtitles.append((subtitle_start_time, word_end_time, formatted_text))

            logging.info(f"Speech-to-text transcription completed.")
            return subtitles
        except Exception as e:
            logging.error(f"Error in speech-to-text transcription: {e}")
            return []

    def generate_captions_to_video(self, subtitles_path, font=None, captions_color='#BA4A00', 
                                  shadow_color='white', font_size=60, width=540):
        try:
            font = self.get_font_path(font) if font else self.default_font
            subtitle_clips = []
            shadow_offset = font_size / 10

            logging.info(f"Processing subtitles from: {subtitles_path}")

            if isinstance(subtitles_path, str):
                subtitles = pysrt.open(subtitles_path)
            elif isinstance(subtitles_path, list):
                subtitles = [pysrt.SubRipItem(index=i, start=s, end=e, text=t) 
                            for i, (s, e, t) in enumerate(subtitles_path, 1)]
            else:
                logging.error(f"Invalid subtitles format: {type(subtitles_path)}")
                return []

            # Sort subtitles by start time to ensure correct order
            subtitles = sorted(subtitles, key=lambda x: x.start.ordinal)

            for subtitle in subtitles:
                try:
                    if isinstance(subtitle, pysrt.SubRipItem):
                        start_time, end_time, text = subtitle.start, subtitle.end, subtitle.text.upper()
                    elif isinstance(subtitle, tuple) and len(subtitle) == 3:
                        start_time, end_time, text = subtitle
                        text = text.upper()
                    else:
                        continue

                    shadow_text = self.create_shadow_text(
                        text, 
                        fontsize=font_size, 
                        font=font, 
                        color=captions_color, 
                        shadow_color=shadow_color, 
                        shadow_offset=shadow_offset,
                        blur_color='black',
                        width=width
                    )
                    
                    start_seconds = start_time.ordinal / 1000
                    end_seconds = end_time.ordinal / 1000
                    duration = end_seconds - start_seconds
                    
                    subtitle_clip = (shadow_text
                                   .set_start(start_seconds)
                                   .set_duration(duration)
                                   .set_position(('center', 0.4), relative=True))
                    subtitle_clips.append(subtitle_clip)
                    
                    logging.debug(f"Added subtitle: {text} ({start_seconds}s - {end_seconds}s)")

                except Exception as e:
                    logging.error(f"Error processing subtitle {subtitle}: {e}")
                    continue

            logging.info(f"Successfully generated {len(subtitle_clips)} subtitle clips")
            return subtitle_clips
        except Exception as e:
            logging.error(f"Error adding captions to video: {e}")
            return []

    def process_text_corrections(self, text):
        # Split text into words while preserving punctuation
        words = re.findall(r'\w+|\W+', text)
        
        # Process each word
        corrected_words = []
        for word in words:
            # Fix 6b6t variations (case insensitive)
            if re.match(r'^6b[^a-zA-Z]*$', word, re.IGNORECASE):
                word = '6B6T'
            
            # Remove commas and spaces from numbers
            if any(char.isdigit() for char in word):
                word = re.sub(r'[,\s]', '', word)
            
            corrected_words.append(word)
        
        # Reconstruct the text while preserving original spacing/punctuation
        return ''.join(corrected_words)
