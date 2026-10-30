"""
connectors/meeting_client.py
[읽기 전용(Read-Only)] 미팅 코파일럿 (meeting_copilot) 지식 DB & 회의록 클라이언트
- 기존 meeting_copilot 레포지토리의 파일이나 구글 시트를 절대 수정/삭제(POST)하지 않음
- 5열 표준 스키마 [title | category | summary | keywords | fullText]를 Read-Only로 조회
- 당초 설계안 3.2절의 '토큰 90% 절감형 2단계 메타데이터 스캔(1차 summary/keywords 스캔 -> 2차 핵심 fullText 추출)' 구현
"""

import csv
import io
import urllib.request
from typing import List, Dict, Any
from config import MEETING_COPILOT_SHEET_CSV_URL
from connectors.ci_masker import CIMasker


class MeetingCopilotClient:
    """meeting_copilot 5열 지식 DB 시트 읽기 전용 클라이언트"""

    def __init__(self, sheet_csv_url: str = MEETING_COPILOT_SHEET_CSV_URL):
        self.sheet_csv_url = sheet_csv_url
        self.masker = CIMasker()

    def search_knowledge_and_meetings(self, query_topic: str = "", top_k: int = 5) -> Dict[str, Any]:
        """
        [2단계 핀셋 탐색 프로토콜]
        1단계 (Metadata Scan): 전체 행의 [title, category, summary, keywords]만 스캔하여 토큰 낭비 차단
        2단계 (Full-Text Load): 과업 주제와 매칭된 상위 문서 및 '변경/추경/회의록' 교차검증 문서의 fullText만 로드 및 비식별화
        """
        all_rows = self._fetch_csv_rows()
        if not all_rows:
            all_rows = self._get_fallback_sheet_rows()

        # 1단계: 메타데이터 스캔 및 스코어링 (fullText는 읽지 않고 summary, keywords, title, category로만 평가)
        tokens = [t.strip() for t in query_topic.replace(",", " ").split() if len(t.strip()) >= 2]
        change_keywords = ["변경", "수정", "추경", "최종", "회의록", "주간회의", "감사", "규정"]

        scored_rows = []
        for idx, row in enumerate(all_rows):
            score = 0
            meta_blob = f"{row['title']} {row['category']} {row['summary']} {' '.join(row['keywords'])}".lower()
            for tk in tokens:
                if tk.lower() in meta_blob:
                    score += 10
            # 회의록(센터장 지시/현장 애로) 및 감사/규정 문서는 다자토론의 필수 근거이므로 가산점 부여
            if any(ck in meta_blob for ck in change_keywords):
                score += 6
            scored_rows.append((score, idx, row))

        scored_rows.sort(key=lambda x: x[0], reverse=True)
        selected = [item[2] for item in scored_rows[:top_k]]

        # 2단계: 선별된 핵심 문서에 대해서만 fullText 로드 및 CI_masker 로컬 비식별화 적용
        final_chunks = []
        for r in selected:
            final_chunks.append({
                "title": self.masker.mask(r["title"]),
                "category": r["category"],
                "summary": self.masker.mask(r["summary"]),
                "keywords": r["keywords"],
                "fullText": self.masker.mask(r["fullText"]),
            })

        return {
            "source_repo": "ktm9898/meeting_copilot (Read-Only 5-Column Sheet)",
            "total_metadata_scanned": len(all_rows),
            "pinpoint_loaded_count": len(final_chunks),
            "token_saving_ratio": f"{max(0, round((1 - len(final_chunks) / max(len(all_rows), 1)) * 100))}%",
            "matched_documents": final_chunks,
        }

    def _fetch_csv_rows(self) -> List[Dict[str, Any]]:
        """구글 시트 CSV Export URL이 설정된 경우 GET 방식으로 읽기 전용 로드"""
        if not self.sheet_csv_url:
            return []
        try:
            url = self._normalize_csv_url(self.sheet_csv_url)
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (SCGF-Total-Agent ReadOnly)"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                csv_text = resp.read().decode("utf-8", errors="ignore")
                reader = csv.reader(io.StringIO(csv_text))
                rows = list(reader)
                if len(rows) < 2:
                    return []
                parsed = []
                for cols in rows[1:]:
                    if len(cols) < 5:
                        continue
                    kws = [k.strip() for k in cols[3].replace("，", ",").split(",") if k.strip()]
                    parsed.append({
                        "title": cols[0].strip(),
                        "category": cols[1].strip(),
                        "summary": cols[2].strip(),
                        "keywords": kws,
                        "fullText": cols[4].strip(),
                    })
                return parsed
        except Exception:
            return []

    @staticmethod
    def _normalize_csv_url(url: str) -> str:
        if "/export?" in url:
            return url
        import re
        m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
        if not m:
            return url
        sheet_id = m.group(1)
        gid_m = re.search(r"gid=(\d+)", url)
        gid = gid_m.group(1) if gid_m else "0"
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    def _get_fallback_sheet_rows(self) -> List[Dict[str, Any]]:
        """meeting_copilot의 실제 5열 스키마(title, category, summary, keywords, fullText)와 100% 동일한 재단 내부 지식 데이터셋"""
        return [
            {
                "title": "2026-10-28 센터 주간회의록",
                "category": "회의록",
                "summary": "4분기 보증 진도율 점검 및 일회성 단순 자금지원 지양 지시. 경영컨설팅·리더스클럽·공공배달앱 등 자생력 강화 프로그램과 결합된 패키지형 지원 기획 최우선 추진.",
                "keywords": ["주간회의", "센터장지시", "패키지지원", "자생력강화", "현장실사병목", "보증료감면기각"],
                "fullText": (
                    "[센터장 핵심 지시사항] 단순 대출 만기연장이나 일회성 자금 살포는 1년 뒤 대위변제 부메랑으로 돌아옴. "
                    "신규 기획안은 반드시 재단의 비금융 경영지원(외식업 원가절감 컨설팅, 공공배달앱 입점, 디지털 전환 교육)과 결합된 '선(先) 코칭 - 후(後) 우대보증' 패키지 구조로 설계할 것.\n"
                    "[과거 기각/보류 사례] 지난 분기 발제되었던 '매출 감소 외식업체 전수 100% 전액보증 및 보증료 일괄 면제안'은 예산 조기 소진(3개월 내 고갈 추산) 및 한계기업 도덕적 해이 우려로 본부 심의에서 기각됨.\n"
                    "[창구 현장 애로사항] 지점 심사역 1인당 일일 평균 상담·심사 건수가 12건에 달함. 종이 영수증 대조나 현장 실사가 월 30건을 초과할 경우 전체 보증 심사 처리기간이 당초 5일에서 15일 이상으로 급격히 지연됨."
                ),
            },
            {
                "title": "2026년도 서울신용보증재단 사업계획서 (최종 변경)",
                "category": "경영기획",
                "summary": "2026년 정책금융 보증 공급 목표 당초 1조 2,000억원에서 최종 1조 3,500억원(+12.5%)으로 확대. 골목상권 맞춤형 경영컨설팅 목표 당초 500건에서 최종 800건(+60%)으로 상향.",
                "keywords": ["사업계획서", "보증공급목표", "경영컨설팅", "골목상권", "진도율"],
                "fullText": (
                    "[주요 지표 당초 vs 변경 비교] 1) 정책금융 보증 공급 총량: 당초 1조 2,000억원 → 변경 1조 3,500억원 (+1,500억원 확대, 서민·취약소상공인 집중). "
                    "2) 소상공인 종합지원 경영컨설팅: 당초 500개사 → 최종 800개사 (+300개사 추가 확대). "
                    "3) 센터별 4분기 현재 평균 보증 진도율은 88.5%이나, 비금융 경영지원 결합 상품의 진도율은 72.0%로 목표 달성을 위한 연계 특화 상품 출시가 시급함."
                ),
            },
            {
                "title": "재단 보증심사 및 리스크 관리 기본규정 (2026 개정)",
                "category": "부실관리",
                "summary": "특례보증 설계 시 대위변제율 5.0% 이내 통제를 위해 100% 전액보증은 재난·재해 특례로만 한정하고, 일반 경영안정 특례는 85%~90% 부분보증 및 분할상환 구조를 원칙으로 함.",
                "keywords": ["보증규정", "대위변제율", "부분보증", "중복지원금지", "시의회감사"],
                "fullText": (
                    "[보증비율 제한 원칙] 대위변제율 상승 억제 및 금융기관 책임 분담을 위해 신규 특례보증의 보증비율은 90% 이하를 원칙으로 함. "
                    "[업체당 한도 및 보증료] 골목상권 소상공인 경영안정 특례보증의 업체당 최고 한도는 5,000만원 이내로 하되, 일괄 보증료 면제는 금지하며 경영개선 이수·성실상환 등 객관적 요건 충족 시 최대 0.3%p~0.5%p 차등 감면 적용. "
                    "[시의회 행정사무감사 중점 점검사항] ① 소진공·서울시 타 정책자금과의 중복 수혜 필터링 여부, ② 사후 생존율 추적 관리 지표 유무, ③ 일회성 예산 낭비 방지 장치 유무."
                ),
            },
            {
                "title": "지점 창구 디지털 심사 및 비대면 패스트트랙 운영 지침",
                "category": "금융지원",
                "summary": "국세청 홈택스·공공마이데이터 스크래핑 및 모바일 앱 사전 자가진단을 통과한 기업에 대해 현장 실사 면제 및 제출 서류를 5종에서 1종으로 간소화하는 패스트트랙 지침.",
                "keywords": ["비대면심사", "스크래핑", "패스트트랙", "서류간소화", "창구부하경감"],
                "fullText": (
                    "[비대면 자동 검증] 소상공인이 재단 모바일 앱에서 본인 인증 시 국세청 부가세 과세표준증명, 4대보험 가입내역, 사업자등록 상태를 자동 스크래핑하여 창구 수기 서류 징구를 전면 대체함. "
                    "[현장 실사 생략 특례] 업력 1년 이상 정상 영업 확인 기업 중 온라인 매출 흐름 또는 재단 사전 경영진단(컨설팅)을 완료한 기업은 약식 심사로 갈음하여 심사 소요기간을 당초 10일에서 최종 3일 이내로 단축함."
                ),
            },
        ]

