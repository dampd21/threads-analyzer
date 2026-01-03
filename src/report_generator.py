# src/report_generator.py
import os
from datetime import datetime
from typing import List, Dict

class ReportGenerator:
    def __init__(self, username: str, start_date: str, end_date: str):
        self.username = username
        self.start_date = start_date
        self.end_date = end_date
    
    def generate_markdown_report(self, results: List[Dict], summary: Dict, output_dir: str) -> str:
        """
        상세 마크다운 리포트 생성
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 📊 Threads 가이드라인 분석 리포트

## 기본 정보
- **분석 대상**: @{self.username}
- **분석 기간**: {self.start_date} ~ {self.end_date}
- **분석 시각**: {timestamp}
- **총 게시물**: {summary['total_posts']}개

---

## 📈 요약

| 위험 등급 | 게시물 수 | 비율 |
|-----------|-----------|------|
| 🔴 높음 | {summary['high_risk_count']}개 | {self._calc_percent(summary['high_risk_count'], summary['total_posts'])}% |
| 🟡 중간 | {summary['medium_risk_count']}개 | {self._calc_percent(summary['medium_risk_count'], summary['total_posts'])}% |
| 🟢 낮음 | {summary['low_risk_count']}개 | {self._calc_percent(summary['low_risk_count'], summary['total_posts'])}% |
| ✅ 안전 | {summary['safe_count']}개 | {self._calc_percent(summary['safe_count'], summary['total_posts'])}% |

- **반복/중복 게시물**: {summary['duplicate_count']}개
- **평균 위험 점수**: {summary['average_risk_score']}/100

---

## ⚠️ 위험 게시물 상세

"""
        # 위험 점수 높은 순으로 정렬
        high_risk_posts = sorted(
            [r for r in results if r['risk_score'] > 0],
            key=lambda x: x['risk_score'],
            reverse=True
        )
        
        if high_risk_posts:
            for i, post in enumerate(high_risk_posts[:10], 1):
                report += f"""### {i}. {post['risk_level']} (점수: {post['risk_score']}/100)

**날짜**: {post['datetime'][:10] if post['datetime'] else '알 수 없음'}

**내용**:
> {post['text'][:200]}{'...' if len(post['text']) > 200 else ''}

**탐지된 문제**:
"""
                if post['spam_detected']:
                    report += f"- 스팸성 표현: `{', '.join(post['spam_detected'])}`\n"
                if post['exaggeration_detected']:
                    report += f"- 과장 표현: `{', '.join(post['exaggeration_detected'])}`\n"
                if post['broker_detected']:
                    report += f"- 대행/브로커 표현: `{', '.join(post['broker_detected'])}`\n"
                if post['cta_detected']:
                    report += f"- 과도한 유도: `{', '.join(post['cta_detected'])}`\n"
                if post.get('is_duplicate'):
                    report += f"- ⚠️ 중복 게시물 발견\n"
                
                report += f"""
**권고사항**:
"""
                for rec in post['recommendations']:
                    report += f"- {rec}\n"
                
                report += f"\n**링크**: [{post['link']}]({post['link']})\n\n---\n\n"
        else:
            report += "> 위험 게시물이 없습니다! 🎉\n\n"
        
        # 중복 게시물 섹션
        duplicates = [r for r in results if r.get('is_duplicate')]
        if duplicates:
            report += """## 🔄 중복/반복 게시물

반복적인 동일 문구 게시는 스팸으로 분류될 위험이 있습니다.

| 날짜 | 내용 미리보기 | 위험 등급 |
|------|--------------|-----------|
"""
            for dup in duplicates:
                preview = dup['text'][:30] + '...' if len(dup['text']) > 30 else dup['text']
                preview = preview.replace('|', '\\|').replace('\n', ' ')
                date = dup['datetime'][:10] if dup['datetime'] else '-'
                report += f"| {date} | {preview} | {dup['risk_level']} |\n"
            
            report += "\n"
        
        # 개선 권장사항
        report += """---

## 💡 전체 개선 권장사항

### 피해야 할 패턴
1. **동일/유사 문구 반복 게시** - 스팸 탐지 1순위
2. **과장/보장 표현** - "무조건", "100%", "쉽게" 등
3. **브로커/대행 뉘앙스** - "스팩업", "인증 가자", "대행" 등
4. **과도한 CTA** - "DM 주세요", "링크 클릭" 반복

### 권장하는 패턴
1. **정보형 톤** - "요건 충족 시 검토 가능", "케이스별 상이"
2. **공식 기준 언급** - "공식 기관 확인 필요"
3. **경험 공유 톤** - "제 경험으로는...", "참고로..."
4. **다양한 콘텐츠** - 동일 주제도 다른 표현/구성으로

---

## 📎 참고 자료
- [Threads 커뮤니티 가이드라인](https://help.instagram.com/769983657850450)
- [Meta 커뮤니티 스탠다드](https://transparency.meta.com/policies/community-standards/)

---

*이 리포트는 자동 분석 도구에 의해 생성되었으며, 실제 Meta의 판단과 다를 수 있습니다.*
"""
        
        # 파일 저장
        report_path = os.path.join(output_dir, f"report_{self.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report_path
    
    def _calc_percent(self, count: int, total: int) -> float:
        if total == 0:
            return 0
        return round(count / total * 100, 1)


class AlternativeTextGenerator:
    """
    위험 게시물에 대한 대체 문구 생성
    """
    
    REPLACEMENTS = {
        # 스팸성 → 정보형
        "기억해": "참고해 보세요",
        "가자": "검토해 볼 수 있어요",
        "무조건": "일정 요건 충족 시",
        "보장": "가능성이 있어요",
        "100%": "대부분의 경우",
        "바로 가능": "절차를 거치면 가능",
        "쉽게": "준비하면",
        "DM 주세요": "문의 사항이 있으시면",
        "댓글 달면": "궁금하신 점은",
        
        # 과장 → 완화
        "업종만 괜찮으면": "업종 요건을 충족하면",
        "조건만 맞으면": "요건을 충족하는 경우",
        "누구나 가능": "요건에 해당하면 검토 가능",
        "대박": "좋은 결과를 기대할 수 있어요",
        "확실": "가능성이 높아요",
        
        # 브로커 → 정보 공유
        "대행": "관련 정보 안내",
        "스팩업": "법인 준비 사항",
        "인증 가자": "인증 요건 정리",
        "빠르게 처리": "효율적으로 준비",
    }
    
    def generate_alternative(self, original_text: str, detected_keywords: List[str]) -> str:
        """
        원본 텍스트에서 위험 키워드를 대체한 버전 생성
        """
        alternative = original_text
        
        for keyword in detected_keywords:
            if keyword in self.REPLACEMENTS:
                alternative = alternative.replace(keyword, self.REPLACEMENTS[keyword])
        
        return alternative
    
    def generate_safe_versions(self, original_text: str, detected_issues: Dict) -> List[Dict]:
        """
        여러 버전의 안전한 대체 문구 생성
        """
        all_detected = (
            detected_issues.get('spam_detected', []) +
            detected_issues.get('exaggeration_detected', []) +
            detected_issues.get('broker_detected', []) +
            detected_issues.get('cta_detected', [])
        )
        
        if not all_detected:
            return []
        
        versions = []
        
        # 버전 1: 키워드 직접 대체
        v1 = self.generate_alternative(original_text, all_detected)
        versions.append({
            "type": "키워드 대체",
            "text": v1
        })
        
        # 버전 2: 정보형 톤
        v2 = self._convert_to_informative(original_text)
        versions.append({
            "type": "정보형",
            "text": v2
        })
        
        # 버전 3: 경험 공유형
        v3 = self._convert_to_experience(original_text)
        versions.append({
            "type": "경험 공유형",
            "text": v3
        })
        
        return versions
    
    def _convert_to_informative(self, text: str) -> str:
        """
        정보형 톤으로 변환
        """
        # 간단한 변환 로직
        prefix = "[정보 공유] "
        suffix = "\n\n※ 개별 상황에 따라 다를 수 있으니 공식 기준을 확인해 주세요."
        
        # 위험 키워드 제거
        clean = text
        for keyword in self.REPLACEMENTS.keys():
            clean = clean.replace(keyword, self.REPLACEMENTS.get(keyword, ""))
        
        return prefix + clean.strip() + suffix
    
    def _convert_to_experience(self, text: str) -> str:
        """
        경험 공유형으로 변환
        """
        prefix = "제 경험을 공유하자면, "
        suffix = "\n\n물론 케이스마다 다르니 참고만 해주세요."
        
        clean = text
        for keyword in self.REPLACEMENTS.keys():
            clean = clean.replace(keyword, self.REPLACEMENTS.get(keyword, ""))
        
        return prefix + clean.strip() + suffix
