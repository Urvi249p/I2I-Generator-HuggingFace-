import os
import sys
import requests
from dotenv import load_dotenv

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from image_2_image_generator.marketing_flow import MarketingPosterFlow

load_dotenv()


def download_image(url: str, save_path: str) -> None:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"📥 Downloaded to: {save_path}")


if __name__ == "__main__":
    flow = MarketingPosterFlow()
    flow.kickoff(inputs={
        "image_url": "https://drive.google.com/uc?export=download&id=1LSknUjm9oacbZtxMY1PRPLFPWGG7EGD7",
        "object_description": "a coffee mug",
        "poster_prompt": "Transform this into a surreal illusional artwork. The object melts and flows like liquid, with infinite reflections spiraling inward. Plain pure white background. Photorealistic, ultra detailed, mind-bending optical illusion style.",
    })
    '''
    flow.kickoff(inputs={
        "image_url": "https://drive.google.com/uc?export=download&id=1pcpiPFouAQ4se6KpJJVuMO1kJTtHNMRz",
        "object_description": "a pot with other objects",
    })'''

    if flow.state.result_url:
        print(f"\n✅ Poster URL: {flow.state.result_url}")
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poster_output1.png")
        download_image(flow.state.result_url, output_path)
    else:
        print(f"\n❌ Failed: {flow.state.error}")