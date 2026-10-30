"""
config.py
서울신용보증재단 센터 맞춤형 멀티 AI 에이전트 시스템 (total-agent) 환경 설정
- 기존 2대 레포지토리(ai_news_briefing, meeting_copilot) 읽기 전용(Read-Only) 연동 설정
- 5대 AI 팀(리서치팀, 기획팀, 감사팀, 운영팀, 미디어팀) 및 비서실장 모델 배치 설정
"""

import os

# =====================================================================
# 1. 기존 깃허브 레포지토리 읽기 전용(Read-Only) 연동 엔드포인트
#    주의: 절대 POST(쓰기/수정/삭제) 요청을 보내지 않으며 GET 조회만 수행함
# =====================================================================

# [연동 1] AI 뉴스비서 (ai_news_briefing) GAS Web App URL (Read-Only GET)
NEWS_BRIEFING_GAS_URL = os.getenv(
    "NEWS_BRIEFING_GAS_URL",
    "https://script.google.com/macros/s/AKfycbwtgUJ0QfKHPn6HLt2U41OLUog92RFVaKPyLLVwQodq03LMm50qm4dwQk798D3ovFcaHw/exec"
)

# [연동 2] 미팅 코파일럿 (meeting_copilot) GAS Web App & Sheet URL (Read-Only GET)
MEETING_COPILOT_GAS_URL = os.getenv(
    "MEETING_COPILOT_GAS_URL",
    "https://script.google.com/macros/s/AKfycby8RFA7VPYW2K3GMt76VYfQ89KEunBgyB3xMRNL2cx39YeP4RJzJFoC1E6O0DcEdbZLkA/exec"
)
MEETING_COPILOT_SHEET_CSV_URL = os.getenv("MEETING_COPILOT_SHEET_CSV_URL", "")

# =====================================================================
# 2. API 키 및 실행 모드 설정 (평시 가성비 모드 vs 실전 프런티어 모드)
# =====================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# 실행 모드: "standard" (평시/빠른 검증: 경량 모델 중심) | "frontier" (실전 중요 보고서: 최상위 추론 모델 풀가동)
EXECUTION_MODE = os.getenv("TOTAL_AGENT_MODE", "standard")

# =====================================================================
# 3. 5대 실무팀 + 비서실장 조직 구성 및 하이브리드 모델 매핑
# =====================================================================
TEAM_CONFIG = {
    "chief_secretary": {
        "name": "비서실장",
        "role": "총괄 오케스트레이터 & 대안(Plan B/C) 절충",
        "prompt_file": "prompts/chief_secretary.md",
        "model_standard": "gemini-3.5-flash",
        "model_frontier": "claude-opus-5-5",
        "kpi": "상충 의견의 구조적 절충(Plan B 도출) 및 의사결정 이력(Decision Log) 완결성 확보",
    },
    "research": {
        "name": "리서치팀",
        "role": "내·외부 지식 탐색 및 팩트 브리핑 패킷 구성",
        "prompt_file": "prompts/team_research.md",
        "model_standard": "gemini-2.5-flash",
        "model_frontier": "gemini-4-argon",
        "kpi": "뉴스비서(외부 트렌드) + 미팅코파일럿(내부 회의록·사업계획) 2단계 메타데이터 핀셋 매칭 및 출처 정합성 100%",
    },
    "planning": {
        "name": "기획팀",
        "role": "신사업 및 제도개선 초안(Plan A) 발제",
        "prompt_file": "prompts/team_planning.md",
        "model_standard": "gemini-3.5-flash",
        "model_frontier": "gemini-4-argon",
        "kpi": "소상공인 체감 효용 극대화, 최신 정책 시의성 확보, 기존 관행을 깨는 공격적 초안(Plan A) 설계",
    },
    "audit": {
        "name": "감사팀",
        "role": "독립 리스크·규정 검토 및 시의회 감사 레드팀 반박",
        "prompt_file": "prompts/team_audit.md",
        "model_standard": "gemini-3.5-flash",
        "model_frontier": "gpt-6-astra",
        "kpi": "대위변제율(부실률) 상승 억제, 재단 보증규정 위배 및 중복지원 0%, 시의회 행정사무감사 예상 지적사항 도출",
    },
    "operations": {
        "name": "운영팀",
        "role": "지점 창구 업무부하 검증 및 절차 간소화·성과관리",
        "prompt_file": "prompts/team_operations.md",
        "model_standard": "gemini-2.5-flash",
        "model_frontier": "gemini-3.5-flash",
        "kpi": "창구 직원 심사 병목 차단, 비대면/자동화 실행 대안 도출, 목표 진도율 및 정량 성과지표 산출 가능성 확보",
    },
    "media": {
        "name": "미디어팀",
        "role": "공공기관 표준 개조식 보고서 및 멀티 산출물 패키지 제작",
        "prompt_file": "prompts/team_media.md",
        "model_standard": "gemini-3.5-flash",
        "model_frontier": "claude-opus-5-5",
        "kpi": "공공기관 개조식(□, ○, -, •) 규격 100% 준수, 전후 수치 대조 공식 적용, 1장 요약서·PT·보도자료 원클릭 변환",
    },
}

# 산출물 로컬 저장 경로 (기존 레포는 일체 건드리지 않고 total-agent 내부에만 저장)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
