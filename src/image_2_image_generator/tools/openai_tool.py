import os
import time
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import List, Optional, Type


class WaveSpeedEditInput(BaseModel):
    images: List[str] = Field(..., description="List of image URLs to edit")
    prompt: str = Field(..., description="Instruction describing how to edit the image")
    quality: Optional[str] = Field(default="medium", description="Quality: low, medium, high")
    resolution: Optional[str] = Field(default="1k", description="Resolution: 1k, 2k, 4k")
    output_format: Optional[str] = Field(default="png", description="Output format: png, jpeg, webp")
    aspect_ratio: Optional[str] = Field(default=None, description="e.g. '1:1', '16:9'")


class WaveSpeedImageEditTool(BaseTool):
    name: str = "wavespeed_image_edit"
    description: str = (
        "Edits one or more images using natural language instructions via WaveSpeed's "
        "GPT-Image-2 API. Provide image URLs and a prompt describing the desired edit. "
        "Returns the URL of the edited image."
    )
    args_schema: Type[BaseModel] = WaveSpeedEditInput

    def _run(
        self,
        images: List[str],
        prompt: str,
        quality: str = "medium",
        resolution: str = "1k",
        output_format: str = "png",
        aspect_ratio: Optional[str] = None,
    ) -> str:
        api_key = os.environ.get("WAVESPEED_API_KEY")
        if not api_key:
            return "Error: WAVESPEED_API_KEY environment variable not set."

        payload = {
            "images": images,
            "prompt": prompt,
            "quality": quality,
            "resolution": resolution,
            "output_format": output_format,
            "enable_sync_mode": False,
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://api.wavespeed.ai/api/v3/openai/gpt-image-2/edit",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("data", {})
        get_url = result.get("urls", {}).get("get")

        if not get_url:
            return f"Error: No polling URL returned. Response: {data}"

        for _ in range(120):
            time.sleep(3)
            poll_response = requests.get(get_url, headers=headers)
            poll_response.raise_for_status()
            poll_data = poll_response.json()
            poll_result = poll_data.get("data", poll_data)
            status = poll_result.get("status")

            if status == "completed":
                outputs = poll_result.get("outputs", [])
                if outputs:
                    return f"Image edited successfully. Output URL: {outputs[0]}"
                return "Error: Job completed but no output found."
            elif status == "failed":
                return f"Error: Job failed. Details: {poll_result.get('error')}"

        return "Error: Timed out waiting for image generation."