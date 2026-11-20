import os
import random
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.project import Project, Scene, Asset
from app.services.hardware_queue import HardwareTaskQueue
from app.services.image.canvas_image_provider import CanvasImageProvider
from app.services.image.comfyui_provider import ComfyUIImageProvider

STORAGE_IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/images"))

class ImageService:
    @staticmethod
    def get_provider():
        comfy = ComfyUIImageProvider()
        if comfy.check_health()["is_healthy"]:
            return comfy
        return CanvasImageProvider()

    @staticmethod
    async def generate_scene_image(
        scene_id: str,
        prompt: str,
        aspect_ratio: str = "16:9",
        character_tokens: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        os.makedirs(STORAGE_IMAGES_DIR, exist_ok=True)
        file_name = f"scene_{scene_id}.png"
        output_path = os.path.join(STORAGE_IMAGES_DIR, file_name)

        # Inject character consistency tokens if present
        full_prompt = prompt
        if character_tokens:
            full_prompt = f"{character_tokens}, {prompt}"

        effective_seed = seed if seed is not None else random.randint(1000, 99999)
        provider = ImageService.get_provider()

        # Enforce sequential lock to protect 8 GB RAM / VRAM
        actual_path = await HardwareTaskQueue.run_sequential(
            f"Image Generation for Scene {scene_id}",
            provider.generate_image(
                prompt=full_prompt,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt or "blurry, low quality, distorted",
                seed=effective_seed,
            ),
        )

        file_size = os.path.getsize(actual_path) if os.path.exists(actual_path) else 0
        relative_url = f"/storage/images/{os.path.basename(actual_path)}"

        # Link to DB scene and create asset if db is provided
        asset_id = None
        if db:
            scene = db.query(Scene).filter(Scene.id == scene_id).first()
            if scene:
                asset = Asset(
                    project_id=scene.project_id,
                    asset_type="image",
                    storage_provider="local",
                    file_path=actual_path,
                    file_name=os.path.basename(actual_path),
                    mime_type="image/png",
                    file_size_bytes=file_size,
                )
                db.add(asset)
                db.commit()
                db.refresh(asset)

                scene.visual_asset_id = asset.id
                db.commit()
                asset_id = asset.id

        return {
            "scene_id": scene_id,
            "asset_id": asset_id,
            "file_path": actual_path,
            "image_url": relative_url,
            "file_size_bytes": file_size,
            "aspect_ratio": aspect_ratio,
            "seed": effective_seed,
            "prompt": full_prompt,
        }

    @staticmethod
    async def generate_project_images(
        project_id: str,
        character_tokens: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        db: Session = None,
    ) -> List[Dict[str, Any]]:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        results = []
        # Generate each scene sequentially
        for scene in project.scenes:
            prompt = scene.visual_prompt or f"Cinematic shot for {project.title}, scene {scene.scene_order}"
            res = await ImageService.generate_scene_image(
                scene_id=scene.id,
                prompt=prompt,
                aspect_ratio=project.aspect_ratio or "16:9",
                character_tokens=character_tokens,
                negative_prompt=negative_prompt,
                db=db,
            )
            results.append(res)

        return results

    @staticmethod
    async def regenerate_scene_image(
        scene_id: str,
        custom_prompt: Optional[str] = None,
        db: Session = None,
    ) -> Dict[str, Any]:
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")

        prompt = custom_prompt or scene.visual_prompt or f"Scene {scene.scene_order}"
        new_seed = random.randint(1000, 99999)

        res = await ImageService.generate_scene_image(
            scene_id=scene.id,
            prompt=prompt,
            aspect_ratio=scene.project.aspect_ratio if scene.project else "16:9",
            seed=new_seed,
            db=db,
        )
        return res
