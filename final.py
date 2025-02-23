import sys
import os
print("Python path:", sys.executable)
print("Current working directory:", os.getcwd())

os.environ['KMP_DUPLICATE_LIB_OK']='True'
import streamlit as st
import os
import random
import requests
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import create_retrieval_chain
from elevenlabs.client import ElevenLabs
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, ImageClip, concatenate_videoclips
from PIL import Image
from io import BytesIO
st.set_page_config(
    page_title="AI PDF to Video Converter 🎥",
    page_icon="🎓",
    layout="wide"
)

# Load API keys
groq_api_keys = list(st.secrets["GROQ_API_KEY"].values())
selected_groq_api_key = random.choice(groq_api_keys)

elevenlabs_api_keys = list(st.secrets["ELEVENLABS_API_KEY"].values())
selected_elevenlabs_api_key = random.choice(elevenlabs_api_keys)

google_api_key = st.secrets["GOOGLE_API_KEY"]["key"]
unsplash_api_key = st.secrets["UNSPLASH_API_KEY"]["access_key"]

# Set Google API key as environment variable
os.environ["GOOGLE_API_KEY"] = google_api_key

# Background educational video  
video_url = "https://drive.google.com/uc?export=download&id=1chLHAx1nXGPviEve25aRd95_IKk-cycC"
video_path = "education_video.mp4"

# Download background video
try:
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(video_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
except Exception as e:
    st.error(f"Error downloading video: {e}")
    st.stop()

def fetch_relevant_images(text, num_images=18):
    """Fetch relevant images from Unsplash based on text content."""
    try:
        # Better keyword extraction
        # Remove common words and get more meaningful keywords
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was', 'were'}
        words = text.lower().split()
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        # Get the most frequent meaningful words
        from collections import Counter
        word_freq = Counter(keywords)
        top_keywords = [word for word, count in word_freq.most_common(8)]
        
        search_query = " ".join(top_keywords)
        st.write(f"Searching for images related to: {search_query}")  # Debug info
        
        headers = {
            "Authorization": f"Client-ID {unsplash_api_key}"
        }
        response = requests.get(
            f"https://api.unsplash.com/search/photos",
            params={
                "query": search_query,
                "per_page": num_images,
                "orientation": "portrait",   
                "content_filter": "high"  # Get high-quality images
            },
            headers=headers
        )
        
        if response.status_code == 200:
            images = []
            for photo in response.json()["results"]:
                img_url = photo["urls"]["regular"]
                img_response = requests.get(img_url)
                img = Image.open(BytesIO(img_response.content))
                img.save(f"temp_image_{len(images)}.jpg")
                images.append(f"temp_image_{len(images)}.jpg")
            return images
        return []
    except Exception as e:
        st.error(f"Error fetching images: {e}")
        return []

def create_video_with_images(text_content, audio_path, background_video_path):
    """Create video with background, images, and audio."""
    try:
        # Get relevant images
        images = fetch_relevant_images(text_content)
        
        # Create video clips
        video_clip = VideoFileClip(background_video_path)
        audio_clip = AudioFileClip(audio_path)
        
        # Create image clips
        image_clips = []
        if images:
            duration_per_image = audio_clip.duration / (len(images) + 1)  # +1 for background video
            for img_path in images:
                # Open and resize image using Lanczos resampling (replacement for ANTIALIAS)
                img = Image.open(img_path)
                img = img.resize((video_clip.w, video_clip.h), Image.Resampling.LANCZOS)
                img.save(img_path)
                
                img_clip = (ImageClip(img_path)
                          .set_duration(duration_per_image)
                          .set_pos(('center', 'center')))
                image_clips.append(img_clip)
        
        # Rest of the function remains the same
        if image_clips:
            final_video = concatenate_videoclips([
                video_clip.subclip(0, duration_per_image),
                *image_clips
            ])
        else:
            final_video = video_clip
            
        # Set audio
        final_video = final_video.set_audio(audio_clip)
        
        # Trim to match audio duration
        final_video = final_video.subclip(0, audio_clip.duration)
        
        # Save final video
        final_video_path = "educational_video.mp4"
        final_video.write_videofile(final_video_path, codec="libx264", audio_codec="aac")
        
        # Cleanup temporary image files
        for img_path in images:
            try:
                os.remove(img_path)
            except:
                pass
            
        return final_video_path
    except Exception as e:
        st.error(f"Error creating video: {e}")
        return None

# AI Prompt for Teaching
prompt = ChatPromptTemplate.from_template(
    """
    You are an expert educator. Convert the EXACT content from the provided document into a clear educational speaking.
    
    ## 🛑 Important Rules:
    - ONLY use information that is directly present in the provided document
    - DO NOT add any new information or examples not found in the document
    - DO NOT create fictional scenarios or products
    - Maintain the original meaning and facts from the document
    
    ## 📝 Formatting Guidelines:
    - Break down complex concepts into simple explanations
    - Use clear transitions between topics
    - Keep the tone educational and professional
    
    ### Document Content to Convert:
    {context}
    """
)

llm = ChatGroq(groq_api_key=selected_groq_api_key, model_name="gemma2-9b-it")

def process_pdf(uploaded_file):
    """Extracts text from the uploaded PDF and generates a structured script."""
    if uploaded_file is None:
        st.error("⚠️ Please upload a PDF file")
        return None

    with open("temp_uploaded.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    loader = PyPDFLoader("temp_uploaded.pdf")
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    final_documents = text_splitter.split_documents(docs)

    context = " ".join([doc.page_content for doc in final_documents])
    document_chain = create_stuff_documents_chain(llm, prompt)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
    retriever = FAISS.from_documents(final_documents, embeddings).as_retriever()
    
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    response = retrieval_chain.invoke({'input': "all", 'context': context})
    return response['answer']

# Page Config
st.markdown("""
    <h1 style='text-align: center; padding: 1rem; margin-bottom: 2rem;'>
        🎓 AI PDF to Video Learning Tool
    </h1>
    <p style='text-align: center; font-size: 1.2rem; margin-bottom: 2rem;'>
        Transform your PDF documents into engaging educational videos
    </p>
""", unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])


# Add option to choose input type
with col1:
    st.markdown("### 📚 Upload Content")
    
    # Input type selection
    input_type = st.radio("Choose your input method:", ["PDF Document", "Direct Text"], horizontal=True)
    
    

with col2:
    st.markdown("### 🎯 Features")
    st.markdown("""
        - ✨ AI-powered text processing
        - 🗣️ Professional voice narration
        - 🖼️ Automatic image selection
        - 📝 Dynamic text captions
        - 🎥 High-quality video output
    """)
teaching_script=None
if input_type == "PDF Document":
    # Existing PDF upload logic
    uploaded_file = st.file_uploader("📂 Upload a PDF Document", type=["pdf"])
    if uploaded_file is not None:
        teaching_script = process_pdf(uploaded_file)
else:
    # New direct text input option
    teaching_script = st.text_area("Enter your text content:", height=200)

if teaching_script:
    st.text_area("Generated Script", teaching_script, height=200)

    if st.button("Generate Video Lesson"):
        try:
            # Generate audio from script
            client = ElevenLabs(api_key=selected_elevenlabs_api_key)
            audio_generator = client.text_to_speech.convert(
                text=teaching_script,
                voice_id="pNInz6obpgDQGcFmaJgB",
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            
            # Save the audio file
            audio_path = "teaching_audio.mp3"
            with open(audio_path, "wb") as f:
                f.write(b"".join(audio_generator))

            # Create video with images and audio
            final_video_path = create_video_with_images(teaching_script, audio_path, video_path)
            
            if final_video_path:
                st.success("Educational video generated successfully! 🎉")
                st.video(final_video_path)
                
                with open(final_video_path, "rb") as f:
                    st.download_button("Download Video", f, file_name="educational_video.mp4")
            
        except Exception as e:
            st.error(f"Error generating video: {e}")

st.markdown(
    """
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: black;
            color: white;
            text-align: center;
        }
    </style>
    <div class="footer">
        <p>Made by Damanjit Singh</p>
    </div>
    """,
    unsafe_allow_html=True
)
