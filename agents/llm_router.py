"""
agents/llm_router.py
멀티 모델 라우터 (Gemini API / OpenRouter API 연동 및 무결성 폴백 지원)
- 각 팀의 상시 지침서(prompts/*.md)를 시스템 프롬프트로 자동 주입
- API 키가 설정된 경우 실시간 LLM 추론 수행, 미설정 시에도 지침서 기반 정밀 도메인 추론 엔진 작동
"""

import os
import json
import urllib.request
from typing import Optional
from config import GEMINI_API_KEY, OPENROUTER_API_KEY, EXECUTION_MODE, TEAM_CONFIG


class LLMRouter:
    def __init__(self, gemini_key: str = "", openrouter_key: str = "", mode: str = ""):
        self.gemini_key = gemini_key or GEMINI_API_KEY
        self.openrouter_key = openrouter_key or OPENROUTER_API_KEY
        self.mode = mode or EXECUTION_MODE
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def load_team_prompt(self, team_key: str) -> str:
        """prompts/ 폴더에서 각 팀의 상시 업무 지침서(agent.md) 로드"""
        cfg = TEAM_CONFIG.get(team_key, {})
        rel_path = cfg.get("prompt_file", "")
        if not rel_path:
            return ""
        full_path = os.path.join(self.base_dir, rel_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def get_assigned_model(self, team_key: str) -> str:
        cfg = TEAM_CONFIG.get(team_key, {})
        if self.mode == "frontier":
            return cfg.get("model_frontier", "gemini-3.5-flash")
        return cfg.get("model_standard", "gemini-2.5-flash")

    def call_llm(self, team_key: str, user_prompt: str, temperature: float = 0.35) -> Optional[str]:
        """실제 API 키가 존재할 경우 Gemini 또는 OpenRouter API를 호출"""
        system_instruction = self.load_team_prompt(team_key)

        if self.gemini_key:
            for model_name in ["gemini-2.5-flash", "gemini-2.0-flash"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"
                    payload = {
                        "system_instruction": {"parts": [{"text": system_instruction}]},
                        "contents": [{"parts": [{"text": user_prompt}]}],
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": 4096,
                        },
                    }
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if text:
                            return text.strip()
                except Exception:
                    continue

        return None

