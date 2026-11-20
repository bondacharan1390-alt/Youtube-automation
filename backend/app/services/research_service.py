from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.llm.manager import LLMManager
from app.schemas.research import TopicAnalysisResponse, VideoIdeasResponse, VideoIdeaItem

class ResearchService:
    @staticmethod
    def analyze_topic(topic: str, language: str = "en", db: Session = None) -> TopicAnalysisResponse:
        system_prompt = (
            "You are an elite YouTube Strategist and Audience Algorithm Specialist. "
            "Analyze the given video topic and return a strictly structured JSON analysis."
        )

        lang_instruction = (
            "The content must be tailored for a Telugu YouTube audience with Telugu keywords and hook angles."
            if language == "te"
            else "The content must be tailored for an English-speaking international YouTube audience."
        )

        user_prompt = f"""
        Analyze this YouTube video topic: "{topic}".
        {lang_instruction}

        Return a JSON object matching this exact schema:
        {{
            "topic": "{topic}",
            "virality_score": 85,
            "audience_persona": "Description of the target viewer persona and demographics",
            "search_intent": "Why viewers search for this and what retention triggers matter",
            "hook_angles": ["Hook idea 1", "Hook idea 2", "Hook idea 3"],
            "primary_keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4"],
            "long_tail_keywords": ["long tail query 1", "long tail query 2", "long tail query 3"],
            "recommended_video_length": "8 to 12 minutes (Long) or 50 seconds (Short)"
        }}
        """

        data = LLMManager.generate_json_safe(user_prompt, system_prompt=system_prompt, db=db)
        
        return TopicAnalysisResponse(
            topic=topic,
            language=language,
            virality_score=int(data.get("virality_score", 85)),
            audience_persona=data.get("audience_persona", "General YouTube Viewers"),
            search_intent=data.get("search_intent", "Informational search"),
            hook_angles=data.get("hook_angles", ["The truth you didn't know."]),
            primary_keywords=data.get("primary_keywords", [topic]),
            long_tail_keywords=data.get("long_tail_keywords", [f"how to learn {topic}"]),
            recommended_video_length=data.get("recommended_video_length", "8 to 10 minutes"),
        )

    @staticmethod
    def generate_ideas(seed_keyword: str, language: str = "en", db: Session = None) -> VideoIdeasResponse:
        system_prompt = (
            "You are a Viral YouTube Title and Concept Ideator. "
            "Generate 5 distinct, high-CTR YouTube video concepts for the given keyword."
        )

        lang_instruction = (
            "All video titles, angles, and hooks MUST be in Telugu (తెలుగు)."
            if language == "te"
            else "All video titles, angles, and hooks MUST be in English."
        )

        user_prompt = f"""
        Generate 5 high-converting YouTube video concepts for seed keyword: "{seed_keyword}".
        {lang_instruction}

        Return a JSON object with this exact structure:
        {{
            "ideas": [
                {{
                    "title": "Compelling Title",
                    "angle": "Documentary / Mythbusting / Deep Dive / Tutorial / Shorts Hook",
                    "hook": "First 3-second spoken sentence",
                    "estimated_ctr": "14.2%",
                    "format": "16:9 or 9:16"
                }}
            ]
        }}
        """

        data = LLMManager.generate_json_safe(user_prompt, system_prompt=system_prompt, db=db)
        raw_ideas = data.get("ideas", [])
        
        ideas = [
            VideoIdeaItem(
                title=item.get("title", f"The Future of {seed_keyword}"),
                angle=item.get("angle", "Explainer"),
                hook=item.get("hook", "Did you know this shocking truth?"),
                estimated_ctr=item.get("estimated_ctr", "12.5%"),
                format=item.get("format", "16:9"),
            )
            for item in raw_ideas
        ]

        return VideoIdeasResponse(
            seed_keyword=seed_keyword,
            language=language,
            ideas=ideas,
        )
