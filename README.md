# TurboReelGPT

**Hey there!** TurboReel is a experimental video engine that uses AI to completely automate the process of creating short videos. Checkout the [demo video](https://www.youtube.com/watch?v=CdoTjeDDrbM) to see what it can do.

[![Video Preview](https://i.ytimg.com/vi/CdoTjeDDrbM/hq720.jpg)](https://www.youtube.com/watch?v=CdoTjeDDrbM)

Let me try to explain what makes TurboReel different from other AI video generators. 

Since I was a kid, I've always wanted to become a Youtuber, but editing video is hard, and not to mention you need a good PC. 

This is a limitation for thousands of people. Thanks to LLMs there is a lot of problems that unlocked. Video generation is one of them. In a few years, I belive that video generation will be as easy as writing an article.

TurboReelGPT is my attempt at making that a reality.

If you would like to see a world where anyone can make awesome videos, please consider supporting this project.

[!["Buy Me A Coffee :)"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/pedroeut19)

This helps support development and consumption of services like OpenAI, ElevenLabs, etc.

## 🚀 Roadmap (not set in stone)

- [ ] Improve story stelling
- [ ] Improve video quality
- [ ] Dockerize it
- [ ] Documentation
- [ ] Add translation feature, to reach a wider audience
- [ ] Create more formats (Educational, Product Demo, etc)
- [ ] Find trending audios and videos on the internet and use them to generate videos
- [ ] Video editing software

## 💡 Getting Started

Ready to dive in? Here’s how to get started with TurboReelGPT:

1. **Clone the Repo**:
   ```bash
   git clone https://github.com/tacosyhorchata/turboreelgpt.git
   ```

2. **Head to the Project Folder**:
   ```bash
   cd turboreelgpt
   ```

3. **Make Sure You’ve Got Python**: Grab Python 3.10.x from [python.org](https://www.python.org/downloads/release/python-31012/).

4. **Install FFmpeg and ImageMagick**:
   - **For Windows**: Download the binaries from [FFmpeg](https://ffmpeg.org/download.html) and [ImageMagick](https://imagemagick.org/script/download.php). Just add them to your system's PATH.
   - **For macOS**: Use Homebrew (if you haven’t tried it yet, now’s the time!):
     ```bash
     brew install ffmpeg imagemagick
     ```
   - **For Linux**: Just use your package manager:
     ```bash
     sudo apt-get install ffmpeg imagemagick
     ```

5. **Get the Required Python Packages**:
   ```bash
   pip install -r requirements.txt
   ```
6. **Grab Your API Keys**: You’ll need keys for OPENAI (for generating scripts) and PEXELS (for fetching images). Get your PEXELS API key [here](https://www.pexels.com/api/key/).

7. **Set Up Your Config**: Create a `.env` file in the root folder. Clone `.env-example` and fill it in with your OPENAI_API_KEY and PEXELS_API_KEY.

8. **Gradio UI**: Run:
   ```bash
   python3 GUI.py
   ```
Fill in all the inputs and generate your video!

![GUI Preview](https://drive.google.com/uc?export=view&id=1t_K6zgJrJl5ATv585i1VDF6-YwJ5htI-)

   **Heads Up**: This project uses YT-DLP for downloading YouTube videos, and it requires cookies to work properly. Automating this in a VM might not be the best idea.
   
## 🤗 Want to Help?

We’d love your help! If you’re excited to contribute to TurboReelGPT, here’s how you can jump in:

1. **Fork the Repo**.
2. **Create a New Branch** for your feature or fix.
3. **Make Your Changes and Commit Them**.
4. **Push Your Branch** and submit a pull request.
5. **Wait for Review**: We’ll do our best to review your PR as soon as possible. Joining our Discord server is the best way to get in touch with us.

## 💬 Join Our Discord
Let’s connect! Join us and other creators on our [Discord server](https://discord.gg/bby6DYsCPu)

## Don't forget to star the repo! Starring helps a lot!

[![Star History Chart](https://api.star-history.com/svg?repos=TacosyHorchata/TurboReelGPT&type=Date)](https://star-history.com/#TacosyHorchata/TurboReelGPT&Date)
