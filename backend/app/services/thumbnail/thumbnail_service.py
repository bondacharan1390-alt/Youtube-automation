"""YouTube high-CTR thumbnail composer for 1280x720 (16:9) and 720x1280 (9:16)."""
import os
import logging
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from sqlalchemy.orm import Session
from app.models.project import Project, Asset

logger = logging.getLogger(__name__)

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
THUMBNAIL_DIR = os.path.join(STORAGE_DIR, "thumbnails")


def _get_font(size: int, is_telugu: bool = False) -> ImageFont.FreeTypeFont:
    """Load appropriate system font with fallback."""
    font_candidates = []
    if is_telugu:
        font_candidates = [
            "C:/Windows/Fonts/Nirmala.ttc",
            "C:/Windows/Fonts/gautami.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    else:
        font_candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/Nirmala.ttc",
        ]

    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    return ImageFont.load_default()


class ThumbnailService:
    THEMES = {
        "viral_punch": {
            "bg_color": (15, 12, 35),
            "accent_color": (255, 215, 0),    # Golden Yellow
            "badge_bg": (220, 38, 38),         # Crimson Red
            "text_color": (255, 255, 255),
            "stroke_color": (0, 0, 0),
        },
        "cinematic_dark": {
            "bg_color": (10, 15, 25),
            "accent_color": (0, 229, 255),     # Electric Cyan
            "badge_bg": (124, 58, 237),        # Purple
            "text_color": (240, 248, 255),
            "stroke_color": (5, 5, 15),
        },
        "tech_minimal": {
            "bg_color": (20, 20, 25),
            "accent_color": (16, 185, 129),    # Emerald
            "badge_bg": (37, 99, 235),         # Blue
            "text_color": (255, 255, 255),
            "stroke_color": (10, 10, 15),
        },
        "breaking_news": {
            "bg_color": (30, 10, 10),
            "accent_color": (255, 235, 59),    # Bright Yellow
            "badge_bg": (239, 68, 68),         # Danger Red
            "text_color": (255, 255, 255),
            "stroke_color": (0, 0, 0),
        },
    }

    @classmethod
    def generate_thumbnail(
        cls,
        project_id: str,
        headline: str,
        subtitle: Optional[str] = None,
        badge_text: Optional[str] = "NEW",
        theme_name: str = "viral_punch",
        aspect_ratio: str = "16:9",
        bg_image_path: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
        width, height = (1280, 720) if aspect_ratio == "16:9" else (720, 1280)

        theme = cls.THEMES.get(theme_name, cls.THEMES["viral_punch"])

        # 1. Base Image
        base_img = None
        if bg_image_path and os.path.exists(bg_image_path):
            try:
                loaded = Image.open(bg_image_path).convert("RGB")
                base_img = loaded.resize((width, height), Image.Resampling.LANCZOS)
            except Exception as e:
                logger.warning(f"Failed to load background image: {e}")

        if not base_img:
            # Gradient Canvas
            base_img = Image.new("RGB", (width, height), theme["bg_color"])
            draw = ImageDraw.Draw(base_img)
            r0, g0, b0 = theme["bg_color"]
            r1, g1, b1 = (r0 + 35, g0 + 20, b0 + 60)
            for y in range(height):
                ratio = y / height
                r = int(r0 * (1 - ratio) + r1 * ratio)
                g = int(g0 * (1 - ratio) + g1 * ratio)
                b = int(b0 * (1 - ratio) + b1 * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

        # 2. Dramatic Vignette / Dark Overlay for 100% text readability
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        # Gradient shadow from bottom-left to top-right
        for y in range(int(height * 0.3), height):
            alpha = int(180 * ((y - height * 0.3) / (height * 0.7)))
            overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, min(alpha, 220)))

        base_img.paste(Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(base_img)

        # Detect Telugu characters in text
        is_telugu = any('\u0c00' <= char <= '\u0c7f' for char in (headline + (subtitle or "") + (badge_text or "")))

        # 3. Badge Pill
        badge_y = 60 if aspect_ratio == "16:9" else 120
        badge_x = 70 if aspect_ratio == "16:9" else 50
        if badge_text:
            badge_font = _get_font(28 if aspect_ratio == "16:9" else 36, is_telugu=is_telugu)
            badge_text_upper = badge_text.upper() if not is_telugu else badge_text
            bbox = badge_font.getbbox(badge_text_upper)
            bw = (bbox[2] - bbox[0]) + 36
            bh = (bbox[3] - bbox[1]) + 20
            # Draw rounded pill
            draw.rounded_rectangle(
                [(badge_x, badge_y), (badge_x + bw, badge_y + bh)],
                radius=10,
                fill=theme["badge_bg"],
            )
            draw.text(
                (badge_x + 18, badge_y + 10),
                badge_text_upper,
                font=badge_font,
                fill=(255, 255, 255),
            )
            badge_y += bh + 30

        # 4. Multi-line Headline Text with Heavy Drop Shadow & Dark Stroke
        title_font_size = 72 if aspect_ratio == "16:9" else 64
        title_font = _get_font(title_font_size, is_telugu=is_telugu)

        # Word wrap headline
        words = headline.split()
        lines: List[str] = []
        cur_line = []
        max_chars = 24 if aspect_ratio == "16:9" else 14
        for w in words:
            if len(" ".join(cur_line + [w])) <= max_chars:
                cur_line.append(w)
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        # Draw lines
        text_y = badge_y
        for idx, line_text in enumerate(lines[:3]):
            # Shadow
            draw.text(
                (badge_x + 6, text_y + 6),
                line_text,
                font=title_font,
                fill=(0, 0, 0),
                stroke_width=6,
                stroke_fill=(0, 0, 0),
            )
            # Main headline text
            line_color = theme["accent_color"] if idx == 0 else theme["text_color"]
            draw.text(
                (badge_x, text_y),
                line_text,
                font=title_font,
                fill=line_color,
                stroke_width=4,
                stroke_fill=theme["stroke_color"],
            )
            bbox = title_font.getbbox(line_text)
            lh = (bbox[3] - bbox[1]) + 22
            text_y += lh

        # 5. Subtitle Banner (if provided)
        if subtitle:
            sub_font = _get_font(34 if aspect_ratio == "16:9" else 38, is_telugu=is_telugu)
            draw.text(
                (badge_x + 3, text_y + 25),
                subtitle[:60],
                font=sub_font,
                fill=(220, 225, 240),
                stroke_width=3,
                stroke_fill=(0, 0, 0),
            )

        # Save to storage/thumbnails/
        output_filename = f"{project_id}.png"
        output_path = os.path.join(THUMBNAIL_DIR, output_filename)
        base_img.save(output_path, "PNG", quality=95)
        file_size = os.path.getsize(output_path)

        # Register Asset in DB if session provided
        asset_id = None
        if db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                asset = Asset(
                    project_id=project_id,
                    asset_type="thumbnail",
                    storage_provider="local",
                    file_path=output_path,
                    file_name=output_filename,
                    mime_type="image/png",
                    file_size_bytes=file_size,
                )
                db.add(asset)
                db.commit()
                db.refresh(asset)
                asset_id = asset.id

        return {
            "project_id": project_id,
            "asset_id": asset_id,
            "file_path": output_path,
            "thumbnail_url": f"/storage/thumbnails/{output_filename}",
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "theme": theme_name,
            "file_size_bytes": file_size,
        }
