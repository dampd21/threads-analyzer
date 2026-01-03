# src/analyzer.py
from difflib import SequenceMatcher
from config import RISK_PATTERNS, DUPLICATE_THRESHOLD

class GuidelineAnalyzer:
    def __init__(self):
        self.risk_patterns = RISK_PATTERNS
    
    def analyze_post(self, post: dict) -> dict:
        """
        단일 게시물 분석
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
            "spam_detected": [],
            "exaggeration_detected": [],
            "broker_detected": [],
            "cta_detected": [],
            
            # 종합 점수
            "risk_score": 0,
            "risk_level": "안전",
            "recommendations": []
        }
        
        # 각 카테고리별 키워드 검사
        analysis["spam_detected"] = self._find_keywords(text, self.risk_patterns["spam_keywords"])
        analysis["exaggeration_detected"] = self._find_keywords(text, self.risk_patterns["exaggeration_keywords"])
        analysis["broker_detected"] = self._find_keywords(text, self.risk_patterns["broker_keywords"])
        analysis["cta_detected"] = self._find_keywords(text, self.risk_patterns["cta_patterns"])
        
        # 위험 점수 계산
        analysis["risk_score"] = self._calculate_risk_score(analysis)
        analysis["risk_level"] = self._get_risk_level(analysis["risk_score"])
        
        # 권고사항 생성
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def analyze_all_posts(self, posts: list) -> list:
        """
        전체 게시물 분석 + 중복 검사
        """
        results = []
        
        for i, post in enumerate(posts):
            analysis = self.analyze_post(post)
            
            # 중복/반복 게시 검사
            duplicates = self._find_duplicates(post["text"], posts, i)
            analysis["duplicate_count"] = len(duplicates)
            analysis["is_duplicate"] = len(duplicates) > 0
            
            if analysis["is_duplicate"]:
                analysis["risk_score"] += 30
                analysis["risk_score"] = min(analysis["risk_score"], 100)
                analysis["risk_level"] = self._get_risk_level(analysis["risk_score"])
                analysis["recommendations"].append("⚠️ 유사한 게시물이 반복됨 - 스팸으로 오인될 가능성 높음")
            
            results.append(analysis)
        
        return results
    
    def _find_keywords(self, text: str, keywords: list) -> list:
        found = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        return found
    
    def _calculate_risk_score(self, analysis: dict) -> int:
        score = 0
        score += len(analysis["spam_detected"]) * 15
        score += len(analysis["exaggeration_detected"]) * 20
        score += len(analysis["broker_detected"]) * 25
        score += len(analysis["cta_detected"]) * 10
        return min(score, 100)
    
    def _get_risk_level(self, score: int) -> str:
        if score >= 70:
            return "🔴 높음"
        elif score >= 40:
            return "🟡 중간"
        elif score >= 20:
            return "🟢 낮음"
        else:
            return "✅ 안전"
    
    def _find_duplicates(self, text: str, all_posts: list, current_index: int) -> list:
        duplicates = []
        for i, post in enumerate(all_posts):
            if i != current_index:
                similarity = SequenceMatcher(None, text, post["text"]).ratio()
                if similarity >= DUPLICATE_THRESHOLD:
                    duplicates.append({
                        "index": i,
                        "similarity": round(similarity * 100, 1)
                    })
        return duplicates
    
    def _generate_recommendations(self, analysis: dict) -> list:
        recommendations = []
        
        if analysis["spam_detected"]:
            recommendations.append(f"스팸성 표현: {', '.join(analysis['spam_detected'])} → 정보형 문구로 변경")
        
        if analysis["exaggeration_detected"]:
            recommendations.append(f"과장 표현: {', '.join(analysis['exaggeration_detected'])} → 완화 표현 권장")
        
        if analysis["broker_detected"]:
            recommendations.append(f"대행/브로커 오인: {', '.join(analysis['broker_detected'])} → 정보 공유 톤으로 변경")
        
        if analysis["cta_detected"]:
            recommendations.append(f"과도한 유도: {', '.join(analysis['cta_detected'])} → 최소화 권장")
        
        return recommendations


def generate_summary(results: list) -> dict:
    """
    전체 분석 요약 생성
    """
    total = len(results)
    if total == 0:
        return {
            "total_posts": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
            "safe_count": 0,
            "duplicate_count": 0,
            "average_risk_score": 0
        }
    
    high_risk = sum(1 for r in results if "높음" in r["risk_level"])
    medium_risk = sum(1 for r in results if "중간" in r["risk_level"])
    low_risk = sum(1 for r in results if "낮음" in r["risk_level"])
    safe = sum(1 for r in results if "안전" in r["risk_level"])
    duplicates = sum(1 for r in results if r.get("is_duplicate", False))
    
    return {
        "total_posts": total,
        "high_risk_count": high_risk,
        "medium_risk_count": medium_risk,
        "low_risk_count": low_risk,
        "safe_count": safe,
        "duplicate_count": duplicates,
        "average_risk_score": round(sum(r["risk_score"] for r in results) / total, 1)
    }
