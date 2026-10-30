"""
main.py
SCGF Total-Agent (서울신용보증재단 센터 맞춤형 멀티 AI 에이전트 시스템) 실행 진입점
- 5대 AI 팀(리서치팀, 기획팀, 감사팀, 운영팀, 미디어팀) 및 비서실장 오케스트레이션 실행
- 기존 2대 레포(ai_news_briefing, meeting_copilot) Read-Only 안전 연동
"""

import os
import sys
import webbrowser

# 로컬 모듈 경로 등록
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from agents.engine import TotalAgentEngine


def main():
    # 콘솔 UTF-8 출력 설정 (Windows 한글 깨짐 방지)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 72)
    print("  SCGF Total-Agent | 서울신용보증재단 5대 AI 팀 자율 공방 & 품질 선순환 엔진")
    print("  [안전 보장] ai_news_briefing & meeting_copilot 100% Read-Only 조회")
    print("=" * 72)

    topic = "골목상권 외식업 배달수수료 부담 완화 및 자생력 강화 패키지"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        topic = " ".join(sys.argv[1:])

    engine = TotalAgentEngine()
    result = engine.run_pipeline(topic)

    p1 = result["phase1_research"]
    p2 = result["phase2_plan_a"]
    p3_audit = result["phase3_audit"]
    p3_ops = result["phase3_operations"]
    p4 = result["phase4_orchestration"]

    print(f"\n[STEP 1 | {p1['team']}] 내·외부 지식 2단계 메타데이터 핀셋 탐색 완료")
    print(f"  - 뉴스비서 스캔: {p1['scan_stats']['news_scanned']}건 중 핵심 {p1['scan_stats']['news_selected']}건 선별")
    print(f"  - 미팅코파일럿 스캔: {p1['scan_stats']['meeting_docs_scanned']}건 중 {p1['scan_stats']['meeting_docs_loaded']}건 핀셋 로드")

    print(f"\n[STEP 2 | {p2['team']}] 공격적 초기 기획안(Plan A) 발제")
    print(f"  - 발제안: {p2['proposal_title']}")
    print(f"  - 초기 완성도 점수: {p2['initial_quality_score']['total']}점 ({p2['initial_quality_score']['comment']})")

    print(f"\n[STEP 3A | {p3_audit['team']}] 리스크·규정 반박 및 필수 안전장치(Hard Constraints) 발행")
    print(f"  - 위험 지수 판정: {p3_audit['risk_score']}")
    for hc in p3_audit["hard_constraints"]:
        print(f"    * {hc}")

    print(f"\n[STEP 3B | {p3_ops['team']}] 지점 창구 업무부하 검증 및 간소화 대안(Alternative Process) 발행")
    print(f"  - 창구 부하 판정: {p3_ops['workload_score']}")
    for ap in p3_ops["alternative_processes"]:
        print(f"    * {ap}")

    print(f"\n[STEP 4 | {p4['team']}] 구조적 변화량(Diff) 절충 및 의사결정 로그(Decision Log) 통합")
    print(f"  - 최종 채택안: {p4['plan_b']['title']}")
    print(f"  - 품질 향상 증명: {p4['plan_b']['upgraded_quality_score']['delta']}")

    print(f"\n[STEP 5 | 미디어팀] 공공기관 표준 개조식 보고서 및 4종 산출물 패키지 생성 완료")
    print(f"  - 보고서 저장 경로: {result['saved_report_path']}")
    print("=" * 72)

    if "--open-web" in sys.argv:
        web_path = os.path.join(BASE_DIR, "web", "index.html")
        webbrowser.open(f"file:///{web_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
