from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.project import Project, Scene
from app.services.llm.manager import LLMManager
from app.schemas.script import (
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptSceneItem,
    StoryGenerateRequest,
    StoryGenerateResponse,
    CharacterProfile,
    DialogueScene,
    StoryboardExportResponse,
)

class ScriptService:
    @staticmethod
    def generate_script(req: ScriptGenerateRequest, db: Session = None) -> ScriptGenerateResponse:
        is_shorts = req.aspect_ratio == "9:16"
        scene_count = req.target_scene_count
        
        system_prompt = (
            "You are a master YouTube scriptwriter, storyboard director, and visual prompt designer. "
            "Write a cinematic, high-retention video script structured into distinct scenes."
        )

        if req.language == "te":
            lang_instruction = (
                "CRITICAL BILINGUAL REQUIREMENT: "
                "1. `script_text` and `narration_text` MUST be in authentic, conversational Telugu (తెలుగు). "
                "2. `visual_prompt` MUST be in detailed English describing the exact cinematic frame for an image generator (e.g. 'Cinematic lighting, 8k, photorealistic')."
            )
        else:
            lang_instruction = (
                "All text (`script_text`, `narration_text`, `visual_prompt`) must be in engaging English."
            )

        format_instruction = (
            "This is a YouTube Short (9:16 vertical). Keep scenes punchy (3 to 6 seconds each). "
            "The visual prompts must explicitly specify vertical 9:16 composition and fast kinetic motion."
            if is_shorts
            else "This is a Long-form YouTube video (16:9 horizontal). Multi-act narrative progression with cinematic pacing."
        )

        user_prompt = f"""
        Title: "{req.title}"
        Topic: "{req.topic or req.title}"
        Aspect Ratio: "{req.aspect_ratio}"
        Target Scene Count: {scene_count}
        Tone: "{req.tone}"
        
        {lang_instruction}
        {format_instruction}

        Return a JSON object with this exact structure:
        {{
            "title": "{req.title}",
            "language": "{req.language}",
            "aspect_ratio": "{req.aspect_ratio}",
            "scenes": [
                {{
                    "scene_order": 1,
                    "script_text": "Brief scene concept",
                    "narration_text": "Exact voiceover lines to be spoken",
                    "visual_prompt": "Ultra-detailed visual prompt in English for image generator",
                    "duration_seconds": 6.0
                }}
            ]
        }}
        """

        data = LLMManager.generate_json_safe(user_prompt, system_prompt=system_prompt, db=db)
        raw_scenes = data.get("scenes", [])

        scenes: List[ScriptSceneItem] = []
        for idx, s in enumerate(raw_scenes, 1):
            dur = float(s.get("duration_seconds", 6.0))
            scenes.append(
                ScriptSceneItem(
                    scene_order=int(s.get("scene_order", idx)),
                    script_text=s.get("script_text", f"Scene {idx}"),
                    narration_text=s.get("narration_text", ""),
                    visual_prompt=s.get("visual_prompt", f"Cinematic shot {idx}"),
                    duration_seconds=dur if dur > 0 else 6.0,
                    character_name=s.get("character_name"),
                )
            )

        total_dur = sum(s.duration_seconds for s in scenes)

        # If project_id is provided, automatically update the database project scenes
        if req.project_id and db:
            ScriptService.save_scenes_to_project(req.project_id, scenes, db)

        return ScriptGenerateResponse(
            title=req.title,
            language=req.language,
            aspect_ratio=req.aspect_ratio,
            estimated_total_duration=round(total_dur, 2),
            scenes=scenes,
        )

    @staticmethod
    def generate_story(req: StoryGenerateRequest, db: Session = None) -> StoryGenerateResponse:
        system_prompt = (
            "You are a master narrative designer and dialogue writer for digital video creators. "
            "Create compelling characters and a high-tension dialogue script based on the premise."
        )

        lang_instruction = (
            "All dialogue lines MUST be in natural Telugu (తెలుగు). Character names and visual prompts in English."
            if req.language == "te"
            else "All dialogue lines and visual prompts in English."
        )

        user_prompt = f"""
        Premise: "{req.premise}"
        Character Count: {req.character_count}
        Tone: "{req.tone}"
        {lang_instruction}

        Return a JSON object with this exact structure:
        {{
            "story_title": "Title of Story",
            "characters": [
                {{
                    "name": "Character Name",
                    "role": "Role / Persona",
                    "voice_style": "Voice characteristics",
                    "visual_prompt": "Cinematic visual description in English for avatar generation"
                }}
            ],
            "dialogue_scenes": [
                {{
                    "speaker": "Character Name",
                    "line": "Spoken dialogue line",
                    "visual_prompt": "Visual prompt of character speaking",
                    "duration_seconds": 5.5
                }}
            ]
        }}
        """

        data = LLMManager.generate_json_safe(user_prompt, system_prompt=system_prompt, db=db)
        
        characters = [
            CharacterProfile(
                name=c.get("name", "Narrator"),
                role=c.get("role", "Protagonist"),
                voice_style=c.get("voice_style", "Clear and engaging"),
                visual_prompt=c.get("visual_prompt", "Cinematic portrait, 8k"),
            )
            for c in data.get("characters", [])
        ]

        dialogue_scenes = [
            DialogueScene(
                speaker=d.get("speaker", "Narrator"),
                line=d.get("line", ""),
                visual_prompt=d.get("visual_prompt", "Cinematic dialogue shot"),
                duration_seconds=float(d.get("duration_seconds", 5.5)),
            )
            for d in data.get("dialogue_scenes", [])
        ]

        return StoryGenerateResponse(
            story_title=data.get("story_title", req.premise[:60]),
            language=req.language,
            characters=characters,
            dialogue_scenes=dialogue_scenes,
        )

    @staticmethod
    def save_scenes_to_project(project_id: str, scenes: List[ScriptSceneItem], db: Session) -> Project:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Clear existing scenes
        db.query(Scene).filter(Scene.project_id == project_id).delete()
        
        total_duration = 0.0
        for s in scenes:
            db_scene = Scene(
                project_id=project.id,
                scene_order=s.scene_order,
                script_text=s.script_text,
                narration_text=s.narration_text,
                visual_prompt=s.visual_prompt,
                duration_seconds=s.duration_seconds,
            )
            db.add(db_scene)
            total_duration += s.duration_seconds

        project.status = "scripted"
        project.estimated_duration_seconds = round(total_duration, 2)
        project.target_scene_count = len(scenes)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def export_storyboard(project_id: str, db: Session) -> StoryboardExportResponse:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        scenes = [
            ScriptSceneItem(
                scene_order=s.scene_order,
                script_text=s.script_text or "",
                narration_text=s.narration_text or "",
                visual_prompt=s.visual_prompt or "",
                duration_seconds=s.duration_seconds or 6.0,
            )
            for s in project.scenes
        ]

        return StoryboardExportResponse(
            project_id=project.id,
            title=project.title,
            language=project.language,
            aspect_ratio=project.aspect_ratio,
            target_resolution=project.target_resolution,
            total_scenes=len(scenes),
            total_duration_seconds=project.estimated_duration_seconds,
            scenes=scenes,
            metadata=project.metadata_json or {},
        )
