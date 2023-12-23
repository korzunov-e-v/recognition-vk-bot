import asyncio
import json

import aiohttp

from src.config import service_settings

VK_API_URL = "https://api.vk.com/method/"


async def _get_audio_upload_url() -> str:
    headers = {"Authorization": f"Bearer {service_settings.vk_api_token}"}
    async with aiohttp.ClientSession() as session:
        upload_url_response = await session.get(
            url=VK_API_URL + "asr.getUploadUrl",
            headers=headers,
            params={"v": "5.199"},
        )
        upload_url_response_json = await upload_url_response.json()
        upload_url = upload_url_response_json["response"]["upload_url"]
        return upload_url


async def recognize_audio_file(file_path: str) -> str:
    headers = {"Authorization": f"Bearer {service_settings.vk_api_token}"}

    upload_url = await _get_audio_upload_url()
    async with aiohttp.ClientSession() as session:
        upload_response = await session.post(
            upload_url,
            data={"file": open(file_path, "rb")},
        )
        upload_response_json = await upload_response.json()

    process_params = {"audio": json.dumps(upload_response_json), "model": "spontaneous", "v": "5.199"}
    async with aiohttp.ClientSession() as session:
        process_response = await session.post(
            url=VK_API_URL + "asr.process",
            headers=headers,
            params=process_params,
        )
        process_response_json = await process_response.json()
        task_id = process_response_json["response"]["task_id"]

    check_status_response_json = None
    status = "processing"
    async with aiohttp.ClientSession() as session:
        while status == "processing":
            check_status_params = {"task_id": task_id, "v": "5.199"}
            check_status_response = await session.post(
                url=VK_API_URL + "asr.checkStatus",
                headers=headers,
                params=check_status_params,
            )
            check_status_response_json = await check_status_response.json()
            status = check_status_response_json["response"]["status"]
            await asyncio.sleep(0.34)

    if status == "finished":
        text = check_status_response_json["response"]["text"]
        return text
    else:
        raise Exception("Ошибка распознавания")
