# src/analyzer.py
# Meta 커뮤니티 규정 기반 분석기

from difflib import SequenceMatcher
from guidelines import COMMUNITY_GUIDELINES, SEVERITY_SCORES, COMBINATION_BONUS

class GuidelineAnalyzer:
    def __init__(self):
        self.guidelines = COMMUNITY_GUIDELINES
        self.severity_scores = SEVERITY_SCORES
        self.combination_bonus = COMBINATION_BONUS
    
    def analyze_post(self, post: dict) -> dict:
        """
        단일 게시물을 공식 가이드라인 기준으로 분석
        """
        text = post.get("text", "")
        
        analysis = {
            "username": post.get("username", ""),
            "text": text,
            "datetime": post.get("datetime", ""),
            "link": post.get("link", ""),
            "likes": post.get("likes", 0),
            "replies": post.get("replies", 0),
            "reposts": post.get("reposts", 0),
            
            # 위반 분석 결과
            "violations": [],  # 감지된 위반 목록
            "violation_details": [],  # 상세 설명
            
            # 종합 점수
            "risk_score": 0,
            "risk_level": "✅ 안전",
            "official_policy_refs": [],  # 관련 공식 정책 참조
            "recommendations": []
        }
        
        # 각 카테고리별 위반 검사
        detected_subcategories = []
        
        for category, category_data in self.guidelines.items():
            for subcategory, subcat_data in category_data.get("subcategories", {}).items():
                violation = self._check_violation(text, subcat_data)
                
                if violation["is_violation"]:
                    detected_subcategories.append((category, subcategory))
                    
                    base_score = self.severity_scores.get(category, {}).get(subcategory, 50)
                    
                    analysis["violations"].append({
                        "category": category,
                        "subcategory": subcategory,
                        "matched_indicators": violation["matched_indicators"],
                        "matched_keywords": violation["matched_keywords"],
                        "base_score": base_score
                    })
                    
                    analysis["violation_details"].append(
                        f"[{category}/{subcategory}] {', '.join(violation['matched_indicators'][:2])}"
                    )
                    
                    analysis["official_policy_refs"].append(
                        f"커뮤니티 규정 > {category.replace('_', ' ')} > {subcategory.replace('_', ' ')}"
                    )
        
        # 위험 점수 계산
        analysis["risk_score"] = self._calculate_risk_score(detected_subcategories, analysis["violations"])
        analysis["risk_level"] = self._get_risk_level(analysis["risk_score"])
        
        # 권고사항 생성
        analysis["recommendations"] = self._generate_recommendations(analysis["violations"])
        
        return analysis
    
    def _check_violation(self, text: str, subcat_data: dict) -> dict:
        """
        특정 하위 카테고리에 대한 위반 여부 검사
        """
        result = {
            "is_violation": False,
            "matched_indicators": [],
            "matched_keywords": []
        }
        
        text_lower = text.lower()
        
        # 키워드 매칭
        for keyword in subcat_data.get("keywords", []):
            if keyword.lower() in text_lower:
                result["matched_keywords"].append(keyword)
        
        # 인디케이터(문맥 패턴) 매칭
        for indicator in subcat_data.get("indicators", []):
            # 인디케이터의 핵심 단어들이 텍스트에 있는지 확인
            indicator_words = [w for w in indicator.split() if len(w) > 2]
            match_count = sum(1 for w in indicator_words if w.lower() in text_lower)
            
            # 핵심 단어의 30% 이상 매칭되면 해당 인디케이터 적용
            if len(indicator_words) > 0 and match_count / len(indicator_words) >= 0.3:
                result["matched_indicators"].append(indicator)
        
        # 키워드 2개 이상 또는 인디케이터 1개 이상 매칭 시 위반
        if len(result["matched_keywords"]) >= 1 or len(result["matched_indicators"]) >= 1:
            result["is_violation"] = True
        
        return result
    
    def _calculate_risk_score(self, detected_subcategories: list, violations: list) -> int:
        """
        위험 점수 계산 (공식 가이드라인 기반)
        """
        if not violations:
            return 0
        
        # 기본 점수: 가장 높은 위반의 점수
        base_scores = [v["base_score"] for v in violations]
        max_score = max(base_scores) if base_scores else 0
        
        # 추가 위반에 대한 가산점 (각각 10점씩, 최대 30점)
        additional_score = min(len(violations) - 1, 3) * 10
        
        # 위반 조합 보너스
        combination_score = 0
        for (cat1, sub1), (cat2, sub2) in [(a, b) for i, a in enumerate(detected_subcategories) for b in detected_subcategories[i+1:]]:
            key1 = (sub1, sub2)
            key2 = (sub2, sub1)
            if key1 in self.combination_bonus:
                combination_score += self.combination_bonus[key1]
            elif key2 in self.combination_bonus:
                combination_score += self.combination_bonus[key2]
        
        total_score = max_score + additional_score + combination_score
        return min(total_score, 100)
    
    def _get_risk_level(self, score: int) -> str:
        """
        점수에 따른 위험 등급
        """
        if score >= 80:
            return "🔴 매우 높음 (삭제 가능성 높음)"
        elif score >= 60:
            return "🟠 높음 (경고/제한 가능성)"
        elif score >= 40:
            return "🟡 중간 (주의 필요)"
        elif score >= 20:
            return "🟢 낮음"
        else:
            return "✅ 안전"
    
    def _generate_recommendations(self, violations: list) -> list:
        """
        공식 가이드라인 기반 권고사항 생성
        """
        recommendations = []
        
        for v in violations:
            cat = v["category"]
            sub = v["subcategory"]
            
            if sub == "직업_사기":
                recommendations.append(
                    "⚠️ [직업 사기 오인 가능] '업종만 괜찮으면', '쉽게', '보장' 같은 표현 제거 → "
                    "'요건 충족 시 검토 가능', '케이스별 상이' 등으로 변경"
                )
            elif sub == "가짜_문서_사기":
                recommendations.append(
                    "⚠️ [가짜 문서 사기 오인 가능] '인증 가자', '대행' 표현 제거 → "
                    "'인증 요건 안내', '공식 절차 확인 필요' 등으로 변경"
                )
            elif sub == "반복_게시":
                recommendations.append(
                    "⚠️ [스팸 탐지] 동일/유사 문구 반복 게시 금지 → "
                    "같은 주제라도 문장 구조/표현을 다르게 작성"
                )
            elif sub == "참여_유도":
                recommendations.append(
                    "⚠️ [참여 유도 스팸] 'DM 주세요', '좋아요 누르면' 등 과도한 CTA 최소화"
                )
            elif sub == "기만적_오해_유발":
                recommendations.append(
                    "⚠️ [과장/기만 오인 가능] '100%', '무조건', '보장' 표현 제거 → "
                    "'가능성', '검토 필요', '케이스별 상이' 등으로 완화"
                )
            elif sub == "투자_금전_사기":
                recommendations.append(
                    "⚠️ [투자 사기 오인 가능] 수익 보장, 무위험 투자 표현 절대 금지"
                )
        
        return recommendations
    
    def analyze_all_posts(self, posts: list) -> list:
        """
        전체 게시물 분석 + 중복 검사
        """
        results = []
        
        for i, post in enumerate(posts):
            analysis = self.analyze_post(post)
            
            # 중복/반복 게시 검사
            duplicates = self._find_duplicates(post["text"], posts, i)
            
            if duplicates:
                # 중복 발견 시 스팸 > 반복_게시 위반 추가
                analysis["violations"].append({
                    "category": "스팸",
                    "subcategory": "반복_게시",
                    "matched_indicators": [f"{len(duplicates)}개의 유사 게시물 발견"],
                    "matched_keywords": [],
                    "base_score": 80
                })
                analysis["violation_details"].append(
                    f"[스팸/반복_게시] {len(duplicates)}개의 유사 게시물 발견 (유사도 80% 이상)"
                )
                analysis["official_policy_refs"].append(
                    "커뮤니티 규정 > 스팸 > '매우 빈번한 빈도로 콘텐츠를 게시' / '반복적인 콘텐츠 게시'"
                )
                analysis["recommendations"].append(
                    "⚠️ [스팸 탐지] 동일/유사 문구 반복 게시 금지 → 같은 주제라도 문장 구조/표현을 다르게 작성"
                )
                
                # 점수 재계산
                analysis["risk_score"] = min(analysis["risk_score"] + 30, 100)
                analysis["risk_level"] = self._get_risk_level(analysis["risk_score"])
            
            analysis["is_duplicate"] = len(duplicates) > 0
            analysis["duplicate_count"] = len(duplicates)
            
            results.append(analysis)
        
        return results
    
    def _find_duplicates(self, text: str, all_posts: list, current_index: int, threshold: float = 0.8) -> list:
        """
        유사한 게시물 찾기
        """
        duplicates = []
        for i, post in enumerate(all_posts):
            if i != current_index:
                similarity = SequenceMatcher(None, text, post["text"]).ratio()
                if similarity >= threshold:
                    duplicates.append({
                        "index": i,
                        "similarity": round(similarity * 100, 1)
                    })
        return duplicates


def generate_summary(results: list) -> dict:
    """
    전체 분석 요약 생성
    """
    total = len(results)
    if total == 0:
        return {
            "total_posts": 0,
            "critical_count": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
            "safe_count": 0,
            "duplicate_count": 0,
            "average_risk_score": 0,
            "top_violations": []
        }
    
    # 등급별 카운트
    critical = sum(1 for r in results if "매우 높음" in r["risk_level"])
    high = sum(1 for r in results if "높음" in r["risk_level"] and "매우" not in r["risk_level"])
    medium = sum(1 for r in results if "중간" in r["risk_level"])
    low = sum(1 for r in results if "낮음" in r["risk_level"])
    safe = sum(1 for r in results if "안전" in r["risk_level"])
    duplicates = sum(1 for r in results if r.get("is_duplicate", False))
    
    # 가장 빈번한 위반 유형
    all_violations = []
    for r in results:
        for v in r.get("violations", []):
            all_violations.append(f"{v['category']}/{v['subcategory']}")
    
    from collections import Counter
    violation_counts = Counter(all_violations)
    top_violations = violation_counts.most_common(5)
    
    return {
        "total_posts": total,
        "critical_count": critical,
        "high_risk_count": high,
        "medium_risk_count": medium,
        "low_risk_count": low,
        "safe_count": safe,
        "duplicate_count": duplicates,
        "average_risk_score": round(sum(r["risk_score"] for r in results) / total, 1),
        "top_violations": top_violations
    }
