# AI PDF to Video Learning Tool 🎓

A powerful tool that converts PDF documents or text into educational videos with AI-generated narration and relevant visuals.

## Features 🌟
- PDF Processing: Automatically extracts and processes content from PDF documents
- Text-to-Speech: Professional AI voice narration using ElevenLabs
- Dynamic Visuals: Automatically fetches relevant images from Unsplash
- Text Captions: Adds readable captions to video frames
- High-Quality Output: Generates professional MP4 videos
- Dual Input: Supports both PDF documents and direct text input

## Setup & Installation 🚀

1. **Clone & Install:**

bash
git clone https://github.com/yourusername/ai-pdf-to-video.git
cd ai-pdf-to-video
pip install -r requirements.txt

2. **API Keys Setup:**
Create `.streamlit/secrets.toml`:

```toml
[GROQ_API_KEY]
key1 = "your-groq-api-key"

[ELEVENLABS_API_KEY]
key1 = "your-elevenlabs-api-key"

[GOOGLE_API_KEY]
key = "your-google-api-key"

[UNSPLASH_API_KEY]
access_key = "your-unsplash-access-key"
secret_key = "your-unsplash-secret-key"
```

3. **Run Application:**
```bash
streamlit run final.py
```


## Get Your API Keys 🔑
- GROQ: Sign up at https://www.groq.com/
- ElevenLabs: Register at https://elevenlabs.io/
- Google API: Create project at https://console.cloud.google.com/
- Unsplash: Register at https://unsplash.com/developers

## Usage 📝
1. Launch the application
2. Choose input method (PDF or Direct Text)
3. Upload PDF or enter text
4. Review generated script
5. Click "Generate Video"
6. Download your educational video

## Technical Stack 🛠️
- Streamlit: Web interface
- LangChain: PDF processing
- ElevenLabs: Text-to-speech
- MoviePy: Video creation
- Pillow: Image processing
- Unsplash API: Image sourcing

## Author 👨‍💻
Damanjit Singh

## License 📄
MIT License

## Need Help? ❓
- Check API key validity
- Ensure all dependencies are installed
- Verify internet connection
- Confirm PDF is readable
