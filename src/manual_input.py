# src/manual_input.py
import json
from datetime import datetime
from typing import List, Dict

class ManualInputHandler:
    """
    크롤링이 막힐 경우 수동 입력 지원
    """
    
    def __init__(self):
        self.posts = []
    
    def add_post(self, text: str, date: str, time: str = "00:00:00") -> None:
        """
        수동으로 게시물 추가
        """
        datetime_str = f"{date}T{time}.000Z"
        self.posts.append({
            "username": "",
            "text": text.strip(),
            "datetime": datetime_str,
            "link": "",
            "likes": 0,
            "replies": 0,
            "reposts": 0,
            "scraped_at": datetime.now().isoformat()
        })
    
    def load_from_json(self, filepath: str) -> List[Dict]:
        """
        JSON 파일에서 게시물 로드
        
        예시 JSON 형식:
        [
            {
                "text": "게시물 내용",
                "date": "2024-11-15",
                "time": "14:30:00"
            }
        ]
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            self.add_post(
                text=item.get("text", ""),
                date=item.get("date", ""),
                time=item.get("time", "00:00:00")
            )
        
        return self.posts
    
    def load_from_txt(self, filepath: str) -> List[Dict]:
        """
        텍스트 파일에서 게시물 로드
        
        형식 (각 게시물은 빈 줄로 구분):
        ---
        DATE: 2024-11-15
        TIME: 14:30:00
        TEXT:
        게시물 내용
        여러 줄 가능
        ---
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 구분자로 분리
        blocks = content.split('---')
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            lines = block.split('\n')
            date = ""
            time = "00:00:00"
            text_lines = []
            in_text = False
            
            for line in lines:
                if line.startswith('DATE:'):
                    date = line.replace('DATE:', '').strip()
                elif line.startswith('TIME:'):
                    time = line.replace('TIME:', '').strip()
                elif line.startswith('TEXT:'):
                    in_text = True
                elif in_text:
                    text_lines.append(line)
            
            if date and text_lines:
                self.add_post(
                    text='\n'.join(text_lines),
                    date=date,
                    time=time
                )
        
        return self.posts
    
    def get_posts(self) -> List[Dict]:
        return self.posts
    
    def clear(self) -> None:
        self.posts = []


def create_sample_json(output_path: str) -> None:
    """
    샘플 JSON 파일 생성
    """
    sample = [
        {
            "text": "기업 설립한지 얼마 안되고\n업종만 괜찮으면\n법인 스팩업 기억해\n\n- 여성기업인증과 소부장인증 가자 -",
            "date": "2024-11-15",
            "time": "10:30:00"
        },
        {
            "text": "기업 설립한지 얼마 안되고\n업종만 괜찮으면\n법인 스팩업 기억해\n\n- 여성기업인증과 소부장인증 가자 -",
            "date": "2024-12-30",
            "time": "14:20:00"
        },
        {
            "text": "세금이던 직원에게 줘야할 돈이던 빨리 줘야하는이유?\n세금 이자 대략 8퍼\n직원에게 대략 20퍼.\n심지어 비용처리도안됨",
            "date": "2025-01-01",
            "time": "21:01:00"
        },
        {
            "text": "재밌는게 뭔지알아?\n마케팅을 잘하시는 분들 젊은분들일수록 강의 많이들어.\n반면\n아닌 사람들일수록 강의팔이라 욕한다.\n그러나 재밌는건 그 중에 노하우들 흡수가 진짜여.\n돈 낭비 아니다.",
            "date": "2025-01-01",
            "time": "14:53:00"
        }
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    
    print(f"샘플 JSON 생성됨: {output_path}")


def create_sample_txt(output_path: str) -> None:
    """
    샘플 TXT 파일 생성
    """
    sample = """---
DATE: 2024-11-15
TIME: 10:30:00
TEXT:
기업 설립한지 얼마 안되고
업종만 괜찮으면
법인 스팩업 기억해

- 여성기업인증과 소부장인증 가자 -
---
DATE: 2024-12-30
TIME: 14:20:00
TEXT:
기업 설립한지 얼마 안되고
업종만 괜찮으면
법인 스팩업 기억해

- 여성기업인증과 소부장인증 가자 -
---
DATE: 2025-01-01
TIME: 21:01:00
TEXT:
세금이던 직원에게 줘야할 돈이던 빨리 줘야하는이유?
세금 이자 대략 8퍼
직원에게 대략 20퍼.
심지어 비용처리도안됨
---
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sample)
    
    print(f"샘플 TXT 생성됨: {output_path}")
