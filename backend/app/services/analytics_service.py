import csv
import io
import os
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret
from app.models.analytics import ChannelAnalyticsDaily, VideoAnalyticsDaily, AnalyticsInsight
from app.models.project import Project, PublishJob
from app.models.user import Channel
from app.services.llm.manager import LLMManager


YOUTUBE_DATA_API = "https://www.googleapis.com/youtube/v3"
YOUTUBE_ANALYTICS_API = "https://youtubeanalytics.googleapis.com/v2/reports"


class YouTubeAnalyticsService:
    @staticmethod
    def _access_token(channel: Channel) -> Optional[str]:
        if not channel.encrypted_access_token:
            return None
        token = decrypt_secret(channel.encrypted_access_token)
        if not token or token.startswith("demo_"):
            return None
        return token

    @staticmethod
    def _authorized_channel(channel: Channel) -> bool:
        return bool(channel.youtube_channel_id and YouTubeAnalyticsService._access_token(channel))

    @classmethod
    def get_channel_summary(cls, channel: Channel, db: Session) -> Dict[str, Any]:
        token = cls._access_token(channel)
        if not token:
            projects = db.query(Project).filter(Project.channel_id == channel.id).all()
            return {
                "channel_id": channel.id,
                "channel_name": channel.channel_name,
                "subscriber_count": None,
                "view_count": None,
                "video_count": len([p for p in projects if p.status in ("published", "ready")]),
                "quota_units_used": channel.quota_units_used_today,
                "is_live_data": False,
                "data_mode": "not_verified",
                "metrics_notes": "Live verification pending: authorize YouTube OAuth with yt-analytics.readonly.",
                "earliest_available_date": None,
                "top_videos": [],
            }

        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = httpx.get(
                f"{YOUTUBE_DATA_API}/channels",
                params={"part": "statistics,snippet", "id": channel.youtube_channel_id},
                headers=headers,
                timeout=20,
            )
            if response.status_code != 200:
                return cls._api_error_summary(channel, db, f"YouTube Data API HTTP {response.status_code}")
            item = (response.json().get("items") or [None])[0]
            if not item:
                return cls._api_error_summary(channel, db, "Authorized account did not return the linked channel")
            stats = item.get("statistics", {})
            return {
                "channel_id": channel.id,
                "channel_name": item.get("snippet", {}).get("title", channel.channel_name),
                "subscriber_count": int(stats["subscriberCount"]) if stats.get("subscriberCount") is not None else None,
                "view_count": int(stats["viewCount"]) if stats.get("viewCount") is not None else None,
                "video_count": int(stats["videoCount"]) if stats.get("videoCount") is not None else None,
                "quota_units_used": channel.quota_units_used_today,
                "is_live_data": True,
                "data_mode": "live",
                "metrics_notes": "Live channel totals retrieved from YouTube Data API v3.",
                "earliest_available_date": cls._earliest_stored_date(channel.id, db),
                "top_videos": cls._live_top_videos(channel, token, db),
            }
        except Exception as exc:
            return cls._api_error_summary(channel, db, f"Live channel lookup failed: {exc}")

    @staticmethod
    def _api_error_summary(channel: Channel, db: Session, message: str) -> Dict[str, Any]:
        projects = db.query(Project).filter(Project.channel_id == channel.id).all()
        return {
            "channel_id": channel.id,
            "channel_name": channel.channel_name,
            "subscriber_count": None,
            "view_count": None,
            "video_count": len(projects),
            "quota_units_used": channel.quota_units_used_today,
            "is_live_data": False,
            "data_mode": "error",
            "metrics_notes": message,
            "earliest_available_date": YouTubeAnalyticsService._earliest_stored_date(channel.id, db),
            "top_videos": [],
        }

    @classmethod
    def _live_top_videos(cls, channel: Channel, token: str, db: Session) -> List[Dict[str, Any]]:
        jobs = db.query(PublishJob).filter(
            PublishJob.project_id.in_([p.id for p in db.query(Project).filter(Project.channel_id == channel.id).all()]),
            PublishJob.youtube_video_id.isnot(None),
        ).all()
        result = []
        headers = {"Authorization": f"Bearer {token}"}
        for job in jobs[:10]:
            try:
                response = httpx.get(
                    f"{YOUTUBE_DATA_API}/videos",
                    params={"part": "snippet,statistics", "id": job.youtube_video_id},
                    headers=headers,
                    timeout=20,
                )
                if response.status_code != 200:
                    continue
                item = (response.json().get("items") or [None])[0]
                if not item:
                    continue
                stats = item.get("statistics", {})
                result.append({
                    "title": item.get("snippet", {}).get("title", job.title),
                    "youtube_video_id": job.youtube_video_id,
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)) if stats.get("likeCount") is not None else None,
                    "comments": int(stats.get("commentCount", 0)) if stats.get("commentCount") is not None else None,
                    "status": "published",
                    "data_source": "youtube_data_api",
                })
            except Exception:
                continue
        return sorted(result, key=lambda row: row["views"], reverse=True)[:5]

    @staticmethod
    def _earliest_stored_date(channel_id: str, db: Session) -> Optional[str]:
        first = db.query(ChannelAnalyticsDaily).filter(
            ChannelAnalyticsDaily.channel_id == channel_id
        ).order_by(ChannelAnalyticsDaily.report_date.asc()).first()
        return first.report_date.isoformat() if first else None

    @classmethod
    def retrieve_daily_history(
        cls,
        channel: Channel,
        start_date: date,
        end_date: date,
        db: Session,
    ) -> Dict[str, Any]:
        token = cls._access_token(channel)
        if not token:
            return {
                "channel_id": channel.id,
                "is_live_data": False,
                "data_mode": "not_verified",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "earliest_available_date": cls._earliest_stored_date(channel.id, db),
                "rows": [],
                "error": "YouTube Analytics authorization is unavailable.",
                "requires": [
                    "GOOGLE_CLIENT_ID",
                    "GOOGLE_CLIENT_SECRET",
                    "OAuth scope https://www.googleapis.com/auth/yt-analytics.readonly",
                    "A linked authorized YouTube channel",
                ],
            }

    @classmethod
    def retrieve_video_retention(
        cls,
        channel: Channel,
        youtube_video_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        token = cls._access_token(channel)
        if not token:
            return {
                "is_live_data": False,
                "data_mode": "not_verified",
                "rows": [],
                "error": "Audience retention requires yt-analytics.readonly authorization.",
            }
        try:
            response = httpx.get(
                YOUTUBE_ANALYTICS_API,
                params={
                    "ids": f"channel=={channel.youtube_channel_id}",
                    "filters": f"video=={youtube_video_id}",
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "metrics": "averageViewPercentage,views,estimatedMinutesWatched",
                    "dimensions": "elapsedVideoTimeRatio",
                    "sort": "elapsedVideoTimeRatio",
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            if response.status_code in (400, 401, 403):
                return {
                    "is_live_data": False,
                    "data_mode": "permission_or_availability_error",
                    "rows": [],
                    "error": "Retention is unavailable for this account, video, range, or permission scope.",
                }
            if response.status_code != 200:
                return {
                    "is_live_data": False,
                    "data_mode": "api_error",
                    "rows": [],
                    "error": f"YouTube Analytics API HTTP {response.status_code}",
                }
            payload = response.json()
            headers = [column["name"] for column in payload.get("columnHeaders", [])]
            rows = [dict(zip(headers, values)) for values in payload.get("rows", [])]
            return {
                "is_live_data": True,
                "data_mode": "live",
                "rows": rows,
                "error": None,
            }
        except httpx.HTTPError as exc:
            return {
                "is_live_data": False,
                "data_mode": "api_error",
                "rows": [],
                "error": f"Retention request failed: {exc}",
            }
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        if start_date > date.today():
            raise ValueError("start_date cannot be in the future")
        if end_date > date.today():
            end_date = date.today()

        params = {
            "ids": f"channel=={channel.youtube_channel_id}",
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost",
            "dimensions": "day",
            "sort": "day",
        }
        try:
            response = httpx.get(
                YOUTUBE_ANALYTICS_API,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            if response.status_code in (401, 403):
                return {
                    "channel_id": channel.id,
                    "is_live_data": False,
                    "data_mode": "permission_error",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "earliest_available_date": cls._earliest_stored_date(channel.id, db),
                    "rows": [],
                    "error": "Analytics permission denied or analytics scope is missing.",
                    "requires": [
                        "OAuth scope https://www.googleapis.com/auth/yt-analytics.readonly",
                        "Channel ownership authorization",
                    ],
                }
            if response.status_code == 400:
                try:
                    message = response.json().get("error", {}).get("message", response.text)
                except Exception:
                    message = response.text
                return {
                    "channel_id": channel.id,
                    "is_live_data": False,
                    "data_mode": "api_error",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "earliest_available_date": cls._earliest_stored_date(channel.id, db),
                    "rows": [],
                    "error": f"YouTube Analytics API rejected the report: {message}",
                }
            if response.status_code != 200:
                return {
                    "channel_id": channel.id,
                    "is_live_data": False,
                    "data_mode": "api_error",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "earliest_available_date": cls._earliest_stored_date(channel.id, db),
                    "rows": [],
                    "error": f"YouTube Analytics API HTTP {response.status_code}",
                }

            payload = response.json()
            headers = [column["name"] for column in payload.get("columnHeaders", [])]
            rows = []
            for values in payload.get("rows", []):
                row = dict(zip(headers, values))
                report_date = date.fromisoformat(str(row["day"]))
                record = db.query(ChannelAnalyticsDaily).filter(
                    ChannelAnalyticsDaily.channel_id == channel.id,
                    ChannelAnalyticsDaily.report_date == report_date,
                ).first()
                if not record:
                    record = ChannelAnalyticsDaily(channel_id=channel.id, report_date=report_date)
                    db.add(record)
                record.views = int(row.get("views", 0))
                record.estimated_minutes_watched = float(row.get("estimatedMinutesWatched", 0))
                record.average_view_duration = (
                    float(row["averageViewDuration"]) if row.get("averageViewDuration") is not None else None
                )
                record.subscribers_gained = int(row.get("subscribersGained", 0))
                record.subscribers_lost = int(row.get("subscribersLost", 0))
                record.source = "youtube_analytics"
                record.retrieved_at = datetime.now(timezone.utc)
                rows.append({
                    "date": report_date.isoformat(),
                    "views": record.views,
                    "estimated_minutes_watched": record.estimated_minutes_watched,
                    "average_view_duration": record.average_view_duration,
                    "subscribers_gained": record.subscribers_gained,
                    "subscribers_lost": record.subscribers_lost,
                })
            db.commit()
            return {
                "channel_id": channel.id,
                "is_live_data": True,
                "data_mode": "live",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "earliest_available_date": cls._earliest_stored_date(channel.id, db),
                "rows": rows,
                "error": None,
            }
        except httpx.HTTPError as exc:
            return {
                "channel_id": channel.id,
                "is_live_data": False,
                "data_mode": "api_error",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "earliest_available_date": cls._earliest_stored_date(channel.id, db),
                "rows": [],
                "error": f"YouTube Analytics request failed: {exc}",
            }

    @classmethod
    def generate_ai_insights(cls, channel: Channel, report: Dict[str, Any], db: Session) -> Dict[str, Any]:
        if not report.get("is_live_data"):
            return {
                "is_live_data": False,
                "factual_summary": {},
                "recommendations": [],
                "message": "AI insights require authorized live analytics data.",
                "provider": None,
            }

        rows = report.get("rows", [])
        factual = {
            "date_range": {"start": report["start_date"], "end": report["end_date"]},
            "row_count": len(rows),
            "total_views": sum(row["views"] for row in rows),
            "total_estimated_minutes_watched": sum(row["estimated_minutes_watched"] for row in rows),
            "subscriber_net": sum(row["subscribers_gained"] - row["subscribers_lost"] for row in rows),
            "available_average_view_duration": [
                row["average_view_duration"] for row in rows if row["average_view_duration"] is not None
            ],
        }
        prompt = (
            "You are a YouTube analytics advisor. Analyze only the supplied factual metrics. "
            "Do not invent missing metrics or claim causation. Return JSON with keys "
            "`performance_summary`, `growth_trends`, `content_suggestions`, `engagement_observations`, "
            "and `recommendations`. Each recommendation must be marked advisory.\n"
            f"Factual metrics: {factual}\n"
            f"Daily rows: {rows}"
        )
        provider = LLMManager.get_provider(db=db)
        try:
            generated = provider.generate_json(prompt, system_prompt="Respond with structured factual analysis and clearly advisory recommendations.")
        except Exception:
            generated = {
                "performance_summary": "The authorized analytics period returned factual totals.",
                "growth_trends": "A trend can be calculated only from multiple returned daily rows.",
                "content_suggestions": ["Continue tracking comparable topics and formats before attributing performance changes."],
                "engagement_observations": ["Engagement conclusions require the returned watch-time and subscriber values."],
                "recommendations": [],
            }
        result = {
            "is_live_data": True,
            "factual_summary": factual,
            "recommendations": generated,
            "provider": provider.get_provider_name(),
            "disclaimer": "AI-generated recommendations are advisory and are not additional analytics facts.",
        }
        insight = AnalyticsInsight(
            channel_id=channel.id,
            start_date=date.fromisoformat(report["start_date"]),
            end_date=date.fromisoformat(report["end_date"]),
            is_live_data=True,
            provider_name=provider.get_provider_name(),
            factual_summary=factual,
            recommendations=[result["recommendations"]],
        )
        db.add(insight)
        db.commit()
        return result

    @classmethod
    def export_csv(cls, channel: Channel, report: Dict[str, Any]) -> str:
        if not report.get("is_live_data"):
            raise ValueError("CSV export refused: demo, unavailable, or unauthorized analytics are not actual analytics.")
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["YouTube Analytics Export"])
        writer.writerow(["Channel", channel.channel_name])
        writer.writerow(["Channel ID", channel.youtube_channel_id or ""])
        writer.writerow(["Start date", report["start_date"]])
        writer.writerow(["End date", report["end_date"]])
        writer.writerow(["Generated UTC", datetime.now(timezone.utc).isoformat()])
        writer.writerow(["Data source", "YouTube Analytics API"])
        writer.writerow([])
        writer.writerow([
            "Date", "Views", "Estimated minutes watched", "Average view duration (seconds)",
            "Subscribers gained", "Subscribers lost",
        ])
        for row in report["rows"]:
            writer.writerow([
                row["date"],
                row["views"],
                row["estimated_minutes_watched"],
                row["average_view_duration"] if row["average_view_duration"] is not None else "",
                row["subscribers_gained"],
                row["subscribers_lost"],
            ])
        return output.getvalue()

    @classmethod
    def export_pdf(cls, channel: Channel, report: Dict[str, Any]) -> bytes:
        if not report.get("is_live_data"):
            raise ValueError("PDF export refused: demo, unavailable, or unauthorized analytics are not actual analytics.")
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except Exception as exc:
            raise RuntimeError("PDF export dependency unavailable") from exc

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50
        pdf.setTitle("YouTube Channel Analytics Report")
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, "YouTube Channel Analytics Report")
        y -= 28
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"Channel: {channel.channel_name}")
        y -= 16
        pdf.drawString(50, y, f"Date range: {report['start_date']} to {report['end_date']}")
        y -= 16
        pdf.drawString(50, y, f"Generated UTC: {datetime.now(timezone.utc).isoformat()}")
        y -= 16
        pdf.drawString(50, y, "Data source: YouTube Analytics API (authorized live report)")
        y -= 24
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(50, y, "Daily Metrics")
        y -= 18
        pdf.setFont("Helvetica", 9)
        for row in report["rows"]:
            text = (
                f"{row['date']} | Views: {row['views']} | Minutes watched: "
                f"{row['estimated_minutes_watched']:.2f} | Avg duration: "
                f"{row['average_view_duration'] if row['average_view_duration'] is not None else 'Not available'} sec "
                f"| Subscribers gained/lost: {row['subscribers_gained']}/{row['subscribers_lost']}"
            )
            pdf.drawString(50, y, text[:115])
            y -= 14
            if y < 50:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 9)
        pdf.save()
        return buffer.getvalue()
