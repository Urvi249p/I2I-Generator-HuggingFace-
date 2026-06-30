import os
import sys
import re
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get("API_URL", "http://localhost:8000")

# --- Page Config ---
st.set_page_config(
    page_title="AI Image to Poster",
    page_icon="🎨",
    layout="centered",
)

st.title("🎨 AI Image to Marketing Poster")
st.markdown("Paste a Google Drive image link and transform it into a stunning poster using AI.")


def extract_drive_url(drive_link: str) -> str:
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"/open\?id=([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, drive_link)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return drive_link


STYLE_PRESETS = {
    "Marketing Poster": (
        "Transform this image into a high-end marketing poster. "
        "Add a bold, vibrant background with professional lighting, "
        "dramatic shadows, and a sleek modern composition. "
        "Include subtle decorative elements and make it look like a premium "
        "advertisement suitable for a magazine or billboard. "
        "Keep the object as the hero of the image, sharp and well-lit."
    ),
    "Surreal Illusion": (
        "Transform this into a surreal illusional artwork. "
        "The object melts and flows like liquid, with infinite reflections "
        "spiraling inward. Plain pure white background. "
        "Photorealistic, ultra detailed, mind-bending optical illusion style."
    ),
    "Minimalist": (
        "Transform this into a clean minimalist product shot. "
        "Pure white background, soft shadows, centered composition. "
        "Simple, elegant, high-end luxury feel."
    ),
    "Vintage": (
        "Transform this into a vintage retro advertisement poster. "
        "Warm muted tones, aged paper texture, retro typography style. "
        "1950s advertisement aesthetic, classic and nostalgic."
    ),
    "Custom": "",
}

# --- Inputs ---
st.markdown("---")

drive_link = st.text_input(
    "🔗 Paste Google Drive Image Link",
    placeholder="https://drive.google.com/file/d/YOUR_FILE_ID/view?usp=sharing",
)

if drive_link:
    direct_url = extract_drive_url(drive_link)
    if direct_url != drive_link:
        st.success("✅ Drive link detected — converted to direct URL.")
        try:
            st.image(direct_url, caption="Input Image Preview", use_column_width=True)
        except Exception:
            st.warning("Could not preview image — it will still be processed.")
    else:
        direct_url = drive_link
        st.info("Using URL as-is.")

object_description = st.text_input(
    "🏷️ Describe the object in the image",
    placeholder="e.g. a coffee mug, a pair of shoes, a perfume bottle",
)

style = st.selectbox("🎭 Choose a Style", list(STYLE_PRESETS.keys()))

if style == "Custom":
    custom_prompt = st.text_area(
        "✏️ Enter your custom prompt",
        placeholder="Describe how you want the image transformed...",
        height=120,
    )
else:
    custom_prompt = ""
    st.info(f"**Preset prompt:** {STYLE_PRESETS[style]}")

# --- Run Button ---
st.markdown("---")
run = st.button("🚀 Generate Poster", use_container_width=True)

if run:
    if not drive_link:
        st.error("Please paste a Google Drive image link.")
        st.stop()
    if not object_description:
        st.error("Please describe the object in the image.")
        st.stop()
    if style == "Custom" and not custom_prompt.strip():
        st.error("Please enter a custom prompt.")
        st.stop()

    final_prompt = custom_prompt.strip() if style == "Custom" else STYLE_PRESETS[style]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Input Image**")
        st.image(direct_url, use_column_width=True)

    with st.spinner("🎨 Generating poster... this may take a minute..."):
        try:
            response = requests.post(
                f"{API_URL}/generate",
                json={
                    "image_url": direct_url,
                    "object_description": object_description,
                    "poster_prompt": final_prompt,
                },
                timeout=400,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    if data.get("success"):
        with col2:
            st.markdown("**Generated Poster**")
            st.image(data["result_url"], use_column_width=True)

        st.success("✅ Poster generated successfully!")

        img_response = requests.get(data["result_url"])
        st.download_button(
            label="📥 Download Poster",
            data=img_response.content,
            file_name="poster_output.png",
            mime="image/png",
            use_container_width=True,
        )
    else:
        st.error(f"❌ Failed: {data.get('error')}")