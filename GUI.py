import gradio as gr
from src.reddit_story_engine import RedditStoryGenerator
from src.ready_made_script_engine import ReadyMadeScriptGenerator
import asyncio
import logging
import traceback
import os

reddit_story_generator = RedditStoryGenerator()
ready_made_script_generator = ReadyMadeScriptGenerator()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_video_reddit(video_source, video_file, video_url, video_topic, add_images):
    try:
        video_path = video_file.name if video_file else None
        params = {
            "video_path_or_url": video_source,
            "video_path": video_path,
            "video_url": video_url,
            "video_topic": video_topic,
            "add_images": add_images
        }
        result = asyncio.run(reddit_story_generator.generate_video(**params))
        return result  # Return the result dictionary and None for the button update
    except Exception as e:
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

def generate_video_ready_made(video_source, video_hook, video_file, video_url, video_script, add_images):
    try:
        video_path = video_file.name if video_file else None
        params = {
            "video_path_or_url": video_source,
            "video_path": video_path,
            "video_url": video_url,
            "video_hook": video_hook,
            "video_script": video_script,
            "add_images": add_images
        }
        result = asyncio.run(ready_made_script_generator.generate_video(**params))
        return result  # Return only the result dictionary
    except Exception as e:
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

def generate_videos_batch(video_source, video_file, video_url, video_topics_text, add_images):
    try:
        video_path = video_file.name if video_file else None
        
        # Parse the topics from the text input (one topic per line)
        video_topics = [topic.strip() for topic in video_topics_text.split('\n') if topic.strip()]
        
        if not video_topics:
            return {"status": "error", "message": "No topics provided. Please enter at least one topic."}
        
        params = {
            "video_path_or_url": video_source,
            "video_path": video_path,
            "video_url": video_url,
            "video_topics": video_topics,
            "add_images": add_images
        }
        
        result = asyncio.run(reddit_story_generator.generate_videos_batch(**params))
        return result
    except Exception as e:
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

with gr.Blocks() as iface:
    gr.Markdown("# TurboReel Video Generator")
    gr.Image("public/turboreel_logo.png", label="TurboReel Logo", width="full", height=60)

    with gr.Tabs():
        with gr.TabItem("Reddit Story Videos"):

            ##title
            gr.Markdown("Generate videos based on popular Reddit stories and topics.")
            
            with gr.Row():
                reddit_video_source = gr.Radio(["video_path", "video_url"], label="Video Source")
            
            with gr.Group():
                reddit_video_file = gr.File(label="Select File", visible=False, file_types=["video"])
                reddit_video_url = gr.Textbox(label="YouTube URL", visible=False)
            
            reddit_video_topic = gr.Textbox(label="Video Topic", placeholder="Enter a topic")
            reddit_add_images = gr.Checkbox(label="Add Images", value=True)
            reddit_output = gr.Textbox(label="Result")
            reddit_download_btn = gr.File(label="Download Generated Video", visible=False)
            reddit_submit_btn = gr.Button("Generate Reddit Story Video")

        with gr.TabItem("Ready-Made Script Videos"):
            ##title
            gr.Markdown("Generate videos using your own custom scripts and hooks.")

            with gr.Row():
                ready_made_video_source = gr.Radio(["video_path", "video_url"], label="Video Source")
            
            with gr.Group():
                ready_made_video_file = gr.File(label="Select File", visible=False, file_types=["video"])
                ready_made_video_url = gr.Textbox(label="YouTube URL", visible=False)
            
            ready_made_video_hook = gr.Textbox(label="Video Hook", placeholder="Enter a one-liner hook. This is the first thing that will be seen by the user. It's important because it will determine if the user watches the video or not. \n\nIf no hook is provided, we will generate one for you.", max_length=80)
            ready_made_video_script = gr.Textbox(label="Video Script", lines=5, placeholder="Enter a script", max_length=1000)
            ready_made_add_images = gr.Checkbox(label="Add Images", value=True)
            ready_made_output = gr.Textbox(label="Result")
            ready_made_download_btn = gr.File(label="Download Generated Video", visible=False)
            ready_made_submit_btn = gr.Button("Generate Ready-Made Script Video")

        with gr.TabItem("Batch Reddit Videos"):
            gr.Markdown("Generate multiple Reddit story videos from a single source video.")
            
            with gr.Row():
                batch_video_source = gr.Radio(["video_path", "video_url"], label="Video Source")
            
            with gr.Group():
                batch_video_file = gr.File(label="Select File", visible=False, file_types=["video"])
                batch_video_url = gr.Textbox(label="YouTube URL", visible=False)
            
            batch_video_topics = gr.Textbox(
                label="Video Topics (one per line)", 
                lines=5, 
                placeholder="Enter one topic per line. Each topic will generate a separate video."
            )
            batch_add_images = gr.Checkbox(label="Add Images", value=True)
            batch_output = gr.Textbox(label="Result")
            batch_download_btn = gr.File(label="Download Generated Videos", visible=False)
            batch_submit_btn = gr.Button("Generate Batch Videos")

    def update_visibility(video_src):
        return (
            gr.update(visible=video_src == "video_path"),
            gr.update(visible=video_src == "video_url")
        )

    reddit_video_source.change(
        fn=update_visibility,
        inputs=[reddit_video_source],
        outputs=[reddit_video_file, reddit_video_url]
    )

    ready_made_video_source.change(
        fn=update_visibility,
        inputs=[ready_made_video_source],
        outputs=[ready_made_video_file, ready_made_video_url]
    )

    batch_video_source.change(
        fn=update_visibility,
        inputs=[batch_video_source],
        outputs=[batch_video_file, batch_video_url]
    )

    def process_result(result):
        if isinstance(result, str):
            try:
                result = eval(result)
            except:
                return {"status": "error", "message": result}, gr.update(visible=False), None

        if result["status"] == "success":
            output_message = f"Status: {result['status']}\nMessage: {result['message']}\nOutput Path: {result['output_path']}"
            return output_message, gr.update(visible=False), gr.update(value=result['output_path'], visible=True)
        else:
            return f"Status: {result['status']}\nMessage: {result['message']}", gr.update(visible=False), None

    def process_batch_result(result):
        if isinstance(result, str):
            try:
                result = eval(result)
            except:
                return {"status": "error", "message": result}, gr.update(visible=False), None

        if result["status"] == "success":
            # Format the output message
            output_message = f"Status: {result['status']}\nMessage: {result['message']}\n\nIndividual Results:\n"
            
            # Add details for each video
            for i, video_result in enumerate(result.get('results', [])):
                topic = video_result.get('topic', f'Topic {i+1}')
                status = video_result.get('status', 'unknown')
                message = video_result.get('message', 'No message')
                output_path = video_result.get('output_path', 'No output path')
                
                output_message += f"\n{i+1}. Topic: {topic}\n   Status: {status}\n   Message: {message}\n   Path: {output_path}\n"
            
            # Create a list of successful video paths for download
            successful_videos = [r.get('output_path') for r in result.get('results', []) 
                                if r.get('status') == 'success' and 'output_path' in r]
            
            if successful_videos:
                # For simplicity, we'll just provide the first successful video for download
                # In a real implementation, you might want to zip all videos or provide multiple download buttons
                return output_message, gr.update(visible=False), gr.update(value=successful_videos[0], visible=True)
            else:
                return output_message, gr.update(visible=False), None
        else:
            return f"Status: {result['status']}\nMessage: {result['message']}", gr.update(visible=False), None

    reddit_submit_btn.click(
        generate_video_reddit,
        inputs=[reddit_video_source, reddit_video_file, reddit_video_url, reddit_video_topic, reddit_add_images],
        outputs=reddit_output
    ).then(
        process_result,
        inputs=reddit_output,
        outputs=[reddit_output, reddit_submit_btn, reddit_download_btn]
    )

    ready_made_submit_btn.click(
        generate_video_ready_made,
        inputs=[ready_made_video_source, ready_made_video_hook, ready_made_video_file, ready_made_video_url, ready_made_video_script, ready_made_add_images],
        outputs=ready_made_output
    ).then(
        process_result,
        inputs=ready_made_output,
        outputs=[ready_made_output, ready_made_submit_btn, ready_made_download_btn]
    )

    batch_submit_btn.click(
        generate_videos_batch,
        inputs=[batch_video_source, batch_video_file, batch_video_url, batch_video_topics, batch_add_images],
        outputs=batch_output
    ).then(
        process_batch_result,
        inputs=batch_output,
        outputs=[batch_output, batch_submit_btn, batch_download_btn]
    )

if __name__ == "__main__":
    iface.launch()
