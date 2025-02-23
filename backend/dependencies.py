from fastapi.security import APIKeyHeader
from fastapi import Security
from fastapi import HTTPException
from typing import Dict
import aiohttp

API_KEY = "ragflow-E0ZmY5M2E4YmM1MjExZWY4ZWNlMDI0Mm"
API_BASE_URL="http://223.4.250.237"

# API Key 验证
API_KEY_HEADER = APIKeyHeader(name="Authorization")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if not api_key.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    key = api_key.split(" ")[1]
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key

async def forward_request(
    method: str,
    endpoint: str,
    headers: dict = None,
    json_data: dict = None,
    params: dict = None,
) -> Dict:
    url = f"{API_BASE_URL}{endpoint}"
    if headers is None:
        headers = {}
    headers["Authorization"] = f"Bearer {API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.request(
            method, url, headers=headers, json=json_data, params=params
        ) as response:
            return await response.json()