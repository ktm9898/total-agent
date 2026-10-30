"""
connectors/ci_masker.py
서울신용보증재단 데이터 보안 & 비식별화 모듈
- 회의록, 상담록, 재무제표 텍스트 내 개인/기업 식별정보(CI) 로컬 마스킹
- 외부 LLM 전송 전 필수 전처리 파이프라인
"""

import re

class CIMasker:
    def __init__(self):
        # 1. 사업자등록번호 (10자리: 000-00-00000)
        self.biz_no_pattern = re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{5}\b')
        
        # 2. 법인/주민등록번호 (13자리: 000000-0000000)
        self.corp_rrn_pattern = re.compile(r'\b\d{6}[-\s]?[1-4]\d{6}\b')
        
        # 3. 휴대전화번호 (010-0000-0000)
        self.phone_pattern = re.compile(r'\b01[016789][-\s]?\d{3,4}[-\s]?\d{4}\b')
        
        # 4. 일반 유선전화번호 (02-000-0000 등)
        self.tel_pattern = re.compile(r'\b(02|0[3-6][1-5])[-\s]?\d{3,4}[-\s]?\d{4}\b')
        
        # 5. 계좌번호 (주요 은행 11~14자리)
        self.account_pattern = re.compile(r'\b\d{3,6}[-\s]?\d{2,6}[-\s]?\d{3,6}\b')

        # 6. 상호명 패턴 (주식회사, (주), 상사, 식당, 공업 등)
        self.company_pattern = re.compile(r'(?:\(주\)|주식회사\s*)?([가-힣A-Za-z0-9]{2,15})(?:상사|식당|카페|치킨|베이커리|철강|기획|스튜디오|유통|건설|공업|상회)')

    def mask(self, text: str) -> str:
        """텍스트 내 모든 민감 정보를 [비식별화 태그]로 변환"""
        if not text:
            return ""

        masked = text

        # 사업자번호 마스킹 -> [사업자번호_001]
        biz_matches = list(set(self.biz_no_pattern.findall(masked)))
        for i, m in enumerate(biz_matches, start=1):
            masked = masked.replace(m, f"[사업자번호_{i:02d}]")

        # 법인/주민등록번호 마스킹 -> [식별번호_001]
        corp_matches = list(set(self.corp_rrn_pattern.findall(masked)))
        for i, m in enumerate(corp_matches, start=1):
            masked = masked.replace(m, f"[식별번호_{i:02d}]")

        # 전화번호 마스킹
        phone_matches = list(set(self.phone_pattern.findall(masked)))
        for i, m in enumerate(phone_matches, start=1):
            masked = masked.replace(m, f"[연락처_{i:02d}]")

        tel_matches = list(set(self.tel_pattern.findall(masked)))
        for i, m in enumerate(tel_matches, start=1):
            masked = masked.replace(m, f"[전화번호_{i:02d}]")

        # 상호명 마스킹
        def replace_company(match):
            name = match.group(0)
            return f"[관내업체_{abs(hash(name)) % 1000:03d}]"

        masked = self.company_pattern.sub(replace_company, masked)

        return masked

if __name__ == "__main__":
    # 간단한 자체 테스트
    masker = CIMasker()
    sample = """
    용산센터 주간회의: (주)한강유통(사업자 123-45-67890, 대표 연락처 010-1234-5678) 대표님이
    매출 감소로 5천만원 특례보증을 신청함. 법인번호 110111-1234567 확인 완료.
    """
    print("=== 원본 ===")
    print(sample)
    print("=== 마스킹 결과 ===")
    print(masker.mask(sample))
