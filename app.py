import os
from datetime import datetime

import streamlit as st
from PIL import Image
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables
load_dotenv()  
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configuration des filtres de sécurité
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# Page setup
st.set_page_config(
    page_title="Image to Text and Story Generator",
    page_icon=None,
    layout="centered"
)

st.title("Image to Text and Story Generator")
st.write(
    "Upload an image, get a detailed description, then generate a story or blog inspired by it."
)

@st.cache_resource
def load_model():
    return genai.GenerativeModel("gemini-flash-latest")

model = load_model()

# Prompt helpers
TONE_GUIDE = {
    "Neutral": "Write in a clear, neutral tone.",
    "Academic": "Write in an academic, structured tone.",
    "Playful": "Write in a light, playful tone.",
    "Poetic": "Write in a poetic and reflective tone."
}

LENGTH_GUIDE = {
    "Short": "Keep it concise (about 150–250 words).",
    "Medium": "Moderate length (about 300–500 words).",
    "Long": "More detailed (about 600–900 words)."
}

CONTENT_TYPE_GUIDE = {
    "Story": "Write a narrative story with a beginning, middle, and end.",
    "Blog": "Write a blog-style piece with a hook, clear structure, and a takeaway."
}

def safe_generate(parts, temperature=0.6, max_output_tokens=900):
    """
    Wrapper around Gemini generation with enhanced error handling.
    """
    try:
        response = model.generate_content(
            parts,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens
            },
            safety_settings=safety_settings
        )
        
        # Vérifier si la réponse a du contenu
        if not response.candidates:
            return "Error: No response generated. The content may have been blocked by safety filters."
        
        candidate = response.candidates[0]
        
        # Vérifier le finish_reason
        if candidate.finish_reason.name == "STOP":
            # Génération normale et complète
            return response.text
        elif candidate.finish_reason.name == "MAX_TOKENS":
            # Tokens maximaux atteints - récupérer ce qui existe
            try:
                return response.text + "\n\n[Note: Response was truncated due to length limit]"
            except:
                return "Error: Response exceeded maximum length and could not be retrieved."
        elif candidate.finish_reason.name == "SAFETY":
            # Bloqué par les filtres de sécurité
            safety_info = "\n".join([f"- {rating.category.name}: {rating.probability.name}" 
                                      for rating in candidate.safety_ratings])
            return f"Error: Content blocked by safety filters.\n\nSafety ratings:\n{safety_info}"
        else:
            # Autre raison
            return f"Error: Generation stopped. Reason: {candidate.finish_reason.name}"
            
    except Exception as e:
        return f"Error during generation: {e}"

def image_to_text(img: Image.Image) -> str:
    prompt = (
        "Describe this image in detail. Mention key objects, setting, actions, "
        "colors, emotions, and any visible text. Be precise but readable."
    )
    return safe_generate([prompt, img], temperature=0.2, max_output_tokens=800)

def image_and_query(
    img: Image.Image,
    query: str,
    tone: str,
    length: str,
    content_type: str
) -> str:
    style = TONE_GUIDE.get(tone, TONE_GUIDE["Neutral"])
    size = LENGTH_GUIDE.get(length, LENGTH_GUIDE["Medium"])
    form = CONTENT_TYPE_GUIDE.get(content_type, CONTENT_TYPE_GUIDE["Story"])

    prompt = f"""
You are given an image and a user prompt.
Task:
1) Use the image as inspiration.
2) Follow the user prompt closely.
3) {form}
4) {style}
5) {size}
Output only the final text.

User prompt:
{query}
""".strip()

    return safe_generate([prompt, img], temperature=0.7, max_output_tokens=1500)

# UI
uploaded_image = st.file_uploader(
    "Upload an image (jpg, jpeg, png)",
    type=["jpg", "jpeg", "png"]
)

user_prompt = st.text_area(
    "What do you want to generate from this image?",
    placeholder="Example: Write a short story about a person returning home after a long journey."
)

col1, col2, col3 = st.columns(3)
with col1:
    tone = st.selectbox("Tone", list(TONE_GUIDE.keys()), index=0)
with col2:
    length = st.selectbox("Length", list(LENGTH_GUIDE.keys()), index=1)
with col3:
    content_type = st.selectbox("Type", list(CONTENT_TYPE_GUIDE.keys()), index=0)

generate = st.button("Generate")

# Session history to allow multiple runs
if "records" not in st.session_state:
    st.session_state.records = []

if generate:
    if not uploaded_image:
        st.warning("Please upload an image first.")
    elif not user_prompt.strip():
        st.warning("Please write a prompt before generating.")
    else:
        try:
            img = Image.open(uploaded_image).convert("RGB")
        except Exception:
            st.error("Could not read the image. Try another file.")
            st.stop()

        st.image(img, caption="Uploaded image", use_container_width=True)

        with st.spinner("Generating description and text..."):
            extracted_details = image_to_text(img)
            generated_text = image_and_query(
                img=img,
                query=user_prompt.strip(),
                tone=tone,
                length=length,
                content_type=content_type
            )

        st.subheader("Extracted image description")
        st.write(extracted_details)

        st.subheader(f"Generated {content_type.lower()}")
        st.write(generated_text)

        # Log this run
        st.session_state.records.append({
            "timestamp": datetime.utcnow().isoformat(),
            "filename": uploaded_image.name,
            "tone": tone,
            "length": length,
            "type": content_type,
            "prompt": user_prompt.strip(),
            "image_description": extracted_details,
            "generated_text": generated_text
        })

# Results table + download
if st.session_state.records:
    st.divider()
    st.subheader("History")

    df = pd.DataFrame(st.session_state.records)
    st.dataframe(df, use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download all results as CSV",
        data=csv_bytes,
        file_name="image_text_results.csv",
        mime="text/csv"
    )

    if st.button("Clear history"):
        st.session_state.records = []
        st.rerun()
