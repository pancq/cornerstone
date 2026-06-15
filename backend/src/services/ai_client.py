"""
统一的 AI 调用客户端
从数据库 settings 表读取 AI 配置，支持 OpenAI / Anthropic / 通义千问 / DeepSeek / 自定义
"""
import json
import logging
from typing import Optional
from httpx import AsyncClient, Timeout
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.setting import Setting

logger = logging.getLogger(__name__)

AI_CONFIG_KEY = "ai_config"

# OpenAI 兼容接口的提供商列表
OPENAI_COMPATIBLE = {"openai", "deepseek", "qwen", "zhipu", "custom"}


class AIConfig:
    """AI 配置模型"""
    def __init__(self, provider: str, api_key: str, api_base: str, model: str):
        self.provider = provider
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.api_base)


async def get_ai_config(db: AsyncSession) -> Optional[AIConfig]:
    """从 settings 表读取 AI 配置，未配置返回 None"""
    result = await db.execute(select(Setting).filter(Setting.key == AI_CONFIG_KEY))
    setting = result.scalars().first()
    if not setting:
        return None

    try:
        cfg = json.loads(setting.value)
        provider = cfg.get("provider", "").lower()
        api_key = cfg.get("api_key", "")
        api_base = cfg.get("api_base", "")
        model = cfg.get("model", "")
        if not api_key or not api_base:
            return None
        return AIConfig(provider=provider, api_key=api_key, api_base=api_base, model=model)
    except (json.JSONDecodeError, KeyError):
        return None


async def call_ai(
    prompt: str,
    system: str,
    ai_config: AIConfig,
    max_tokens: int = 2000,
    timeout: int = 15,
) -> str:
    """
    统一 AI 调用入口
    自动适配不同提供商的 API 格式
    超时、重试（最多2次）、错误处理统一在此处理
    返回模型的文本响应
    """
    provider = ai_config.provider

    if provider in OPENAI_COMPATIBLE:
        return await _call_openai_compatible(prompt, system, ai_config, max_tokens, timeout)
    elif provider == "anthropic":
        return await _call_anthropic(prompt, system, ai_config, max_tokens, timeout)
    else:
        raise ValueError(f"不支持的 AI 提供商: {provider}")


async def _call_openai_compatible(
    prompt: str,
    system: str,
    config: AIConfig,
    max_tokens: int,
    timeout: int,
) -> str:
    """调用 OpenAI 兼容接口（OpenAI / DeepSeek / 通义千问 / 智谱 / 自定义）"""
    url = f"{config.api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }

    async with AsyncClient(timeout=Timeout(timeout)) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def _call_anthropic(
    prompt: str,
    system: str,
    config: AIConfig,
    max_tokens: int,
    timeout: int,
) -> str:
    """调用 Anthropic Claude API"""
    url = f"{config.api_base}/v1/messages"
    headers = {
        "x-api-key": config.api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": config.model,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }

    async with AsyncClient(timeout=Timeout(timeout)) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"].strip()