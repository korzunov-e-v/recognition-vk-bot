import json

import aiohttp

from src.config import service_settings

VISION_URL = "https://smarty.mail.ru"
ENDPOINT = "/api/v1/objects/detect"

META = {"meta": json.dumps({"mode": ["scene", "object2"], "images": [{"name": "file_0"}]})}


async def recognize_image(file_path: str) -> dict:
    data = {"file_0": open(file_path, "rb")}
    data.update(META)
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            url=VISION_URL + ENDPOINT,
            params={"oauth_token": service_settings.vision_api_token, "oauth_provider": "mcs"},
            data=data,
            timeout=30,
        )
        upload_response_json = await response.json()
    return upload_response_json["body"]
