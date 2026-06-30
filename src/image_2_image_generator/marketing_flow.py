import os
import time
import requests
from crewai.flow.flow import Flow, start, listen
from pydantic import BaseModel


class PosterState(BaseModel):
    image_url: str = ""
    object_description: str = ""
    poster_prompt: str = ""
    job_id: str = ""
    poll_url: str = ""
    result_url: str = ""
    error: str = ""


class MarketingPosterFlow(Flow[PosterState]):

    @start()
    def build_prompt(self):
        if self.state.poster_prompt:
            print(f"[prompt] Using user prompt")
            return

        desc = self.state.object_description or "the product"
        self.state.poster_prompt = (
            f"Transform this image of {desc} into a high-end marketing poster. "
            f"Add a bold, vibrant background with professional lighting, "
            f"dramatic shadows, and a sleek modern composition. "
            f"Include subtle decorative elements and make it look like a premium "
            f"advertisement suitable for a magazine or billboard. "
            f"Keep the {desc} as the hero of the image, sharp and well-lit."
        )
        print(f"[prompt] {self.state.poster_prompt}")

    @listen(build_prompt)
    def submit_job(self):
        # Mock mode — set MOCK=true in .env to skip WaveSpeed
        if os.environ.get("MOCK") == "true":
            self.state.result_url = "https://via.placeholder.com/1024x1792.png?text=Mock+Poster"
            print("[mock] Returning mock result")
            return
        if self.state.error:
            return

        api_key = os.environ.get("WAVESPEED_API_KEY")
        if not api_key:
            self.state.error = "WAVESPEED_API_KEY not set."
            return

        image_url = self.state.image_url
        print(f"[submit] Using image URL: {image_url}")

        payload = {
            "images": [image_url],
            "prompt": self.state.poster_prompt,
            "quality": "high",
            "resolution": "2k",
            "output_format": "png",
            "aspect_ratio": "9:16",
            "enable_sync_mode": False,
        }

        response = requests.post(
            "https://api.wavespeed.ai/api/v3/openai/gpt-image-2/edit",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        print(f"[submit] Status code: {response.status_code}")
        print(f"[submit] Response: {response.text}")
        response.raise_for_status()

        data = response.json()
        result = data.get("data", {})
        self.state.job_id = result.get("id", "")
        self.state.poll_url = result.get("urls", {}).get("get", "")
        print("PROMPT SENT TO API:")
        print(self.state.poster_prompt)
        print(f"[submit] Job ID: {self.state.job_id}")
        print(f"[submit] Poll URL: {self.state.poll_url}")

    @listen(submit_job)
    def poll_result(self):
        if self.state.error or not self.state.poll_url:
            return

        api_key = os.environ.get("WAVESPEED_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}"}

        print(f"[poll] Waiting for result...")
        for attempt in range(120):
            time.sleep(3)
            response = requests.get(self.state.poll_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            result = data.get("data", data)
            status = result.get("status")
            print(f"[poll] Attempt {attempt + 1}: {status}")

            if status == "completed":
                outputs = result.get("outputs", [])
                if outputs:
                    self.state.result_url = outputs[0]
                else:
                    self.state.error = "Completed but no output returned."
                return
            elif status == "failed":
                error_detail = result.get("error") or result.get("message") or str(result)
                self.state.error = f"Job failed: {error_detail}"
                print(f"[poll] Full failed response: {result}")
                return

        self.state.error = "Timed out waiting for result."

    @listen(poll_result)
    def show_result(self):
        if self.state.error:
            print(f"[error] {self.state.error}")
        else:
            print(f"\n✅ Marketing poster ready!")
            print(f"🖼️  URL: {self.state.result_url}")