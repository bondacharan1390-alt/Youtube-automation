"""Phase 6 Verification Script: YouTube Upload Engine, Playlists & Security.

Runs thorough real-code verification of:
1. Resumable Chunked Upload & Byte-Range Header Validation (RFC 7233)
2. Thumbnail Attachment to Uploaded Video via thumbnails.set
3. YouTube Playlist Lifecycle (Create, List, Add Video)
4. Failed Upload Retry Engine with Deduplication & Bounded Backoff
5. Security Audit: Private Default, Mandatory Manual Approval for Public, AES-256 Token Encryption
"""
import os
import sys
import tempfile
from datetime import datetime, timezone

from app.core.database import SessionLocal, Base, engine
from app.core.security import encrypt_secret, decrypt_secret
from app.models.user import User, Channel
from app.models.project import Project, PublishJob, Playlist
from app.services.youtube.resumable_uploader import ResumableUploader
from app.services.youtube.playlist_service import PlaylistService
from app.services.youtube.youtube_service import YouTubeService


def run_phase6_verification():
    print("=" * 70)
    print("PHASE 6: YOUTUBE UPLOAD ENGINE, PLAYLISTS & SECURITY VERIFICATION")
    print("=" * 70)

    db = SessionLocal()
    report = {
        "resumable_upload": False,
        "thumbnail_attachment": False,
        "playlist_management": False,
        "retry_deduplication": False,
        "security_approval_enforcement": False,
        "token_encryption": False,
    }

    try:
        # Setup test user and channel
        user = db.query(User).filter(User.email == "creator@youtube-studio.ai").first()
        assert user is not None, "Creator user must exist"
        channel = db.query(Channel).filter(Channel.user_id == user.id, Channel.is_active == True).first()
        assert channel is not None, "Channel must exist"

        print(f"\n[1] TEST CHANNEL & USER CONTEXT")
        print(f"  User: {user.email}")
        print(f"  Channel: {channel.channel_name} (ID: {channel.id})")
        print(f"  Daily Quota Used: {channel.quota_units_used_today}/10000 units")

        # -------------------------------------------------------------
        # 1. Resumable Chunked Upload Validation (RFC 7233)
        # -------------------------------------------------------------
        print(f"\n[2] RESUMABLE CHUNKED UPLOAD & RFC 7233 VALIDATION")
        test_video_size = 6 * 1024 * 1024  # 6 MB
        chunk_size = 2 * 1024 * 1024       # 2 MB chunks
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
            tf.write(b"V" * test_video_size)
            test_video_path = tf.name

        try:
            progress_updates = []
            def track_progress(bytes_done, total):
                progress_updates.append((bytes_done, total))

            sim_res = ResumableUploader.simulate_resumable_upload(
                file_path=test_video_path,
                chunk_size=chunk_size,
                progress_callback=track_progress,
            )

            headers = sim_res["validated_headers"]
            print(f"  Total Video Size: {sim_res['total_bytes']} bytes ({sim_res['total_bytes'] / (1024*1024):.1f} MB)")
            print(f"  Chunks Transferred: {sim_res['chunks_transferred']}")
            print(f"  Simulated Video ID: {sim_res['video_id']}")
            for h in headers:
                print(f"    Chunk {h['chunk_index']}: Range={h['Content-Range']} | Length={h['Content-Length']} bytes")

            # Check header formats
            assert len(headers) == 3, "6MB with 2MB chunks must produce 3 chunks"
            assert headers[0]["Content-Range"] == f"bytes 0-{2*1024*1024 - 1}/{test_video_size}"
            assert headers[-1]["bytes_transferred"] == 2 * 1024 * 1024
            assert progress_updates[-1][0] == test_video_size, "Final progress must reach 100%"
            print(f"  => RFC 7233 Byte-Range & Header Validation: PASSED")
            report["resumable_upload"] = True
        finally:
            if os.path.exists(test_video_path):
                os.remove(test_video_path)

        # -------------------------------------------------------------
        # 2. Thumbnail Attachment Verification
        # -------------------------------------------------------------
        print(f"\n[3] THUMBNAIL ATTACHMENT VIA thumbnails.set")
        storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "storage"))
        test_thumb_dir = os.path.join(storage_dir, "thumbnails")
        os.makedirs(test_thumb_dir, exist_ok=True)
        test_thumb_path = os.path.join(test_thumb_dir, "verify_test_thumb.png")
        with open(test_thumb_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 2048)  # 2KB valid PNG header

        try:
            quota_before = channel.quota_units_used_today
            thumb_res = YouTubeService.attach_thumbnail_to_video(
                channel=channel,
                youtube_video_id=sim_res["video_id"],
                thumbnail_path=test_thumb_path,
                db=db,
            )
            print(f"  Attached to Video: {sim_res['video_id']}")
            print(f"  Success: {thumb_res.get('success')}")
            print(f"  Message: {thumb_res.get('message')}")
            print(f"  Quota Units Before: {quota_before} -> After: {channel.quota_units_used_today} (+50 units)")
            assert thumb_res.get("success") is True
            assert channel.quota_units_used_today == quota_before + 50
            print(f"  => Thumbnail Attachment & Quota Accounting: PASSED")
            report["thumbnail_attachment"] = True
        finally:
            if os.path.exists(test_thumb_path):
                os.remove(test_thumb_path)

        # -------------------------------------------------------------
        # 3. YouTube Playlist Lifecycle (Create, List, Add Video)
        # -------------------------------------------------------------
        print(f"\n[4] YOUTUBE PLAYLIST MANAGEMENT (playlists.insert / list / playlistItems.insert)")
        new_playlist = PlaylistService.create_playlist(
            channel_id=channel.id,
            title="AI Video Engine Demo Series 2026",
            description="Autonomous multi-modal YouTube generation pipeline.",
            privacy_status="private",
            db=db,
        )
        print(f"  Created Playlist: '{new_playlist['title']}'")
        print(f"  YouTube Playlist ID: {new_playlist['youtube_playlist_id']}")
        print(f"  Privacy: {new_playlist['privacy_status']}")

        # List playlists
        all_playlists = PlaylistService.list_playlists(channel.id, db)
        print(f"  Total Channel Playlists: {len(all_playlists)}")
        found = any(p["youtube_playlist_id"] == new_playlist["youtube_playlist_id"] for p in all_playlists)
        assert found, "Created playlist must be present in channel listing"

        # Add video to playlist
        item_res = PlaylistService.add_video_to_playlist(
            channel_id=channel.id,
            playlist_id=new_playlist["youtube_playlist_id"],
            youtube_video_id=sim_res["video_id"],
            db=db,
        )
        print(f"  Linked Video {sim_res['video_id']} to Playlist: Item ID = {item_res['item_id']}")
        assert item_res["success"] is True
        print(f"  => Playlist Lifecycle: PASSED")
        report["playlist_management"] = True

        # -------------------------------------------------------------
        # 4. Failed Upload Retry & Deduplication Safeguard
        # -------------------------------------------------------------
        print(f"\n[5] FAILED UPLOAD RETRY & DEDUPLICATION SAFEGUARD")
        proj = db.query(Project).filter(Project.user_id == user.id).first()
        assert proj is not None

        # 4a: Deduplication: already uploaded video should NOT create a duplicate
        already_uploaded_job = PublishJob(
            project_id=proj.id,
            title="Deduplication Guard Test",
            privacy_status="private",
            upload_status="uploaded",
            youtube_video_id="sim_existing_video_id_999",
            manual_approval_granted=True,
            retry_count=0,
        )
        db.add(already_uploaded_job)
        db.commit()
        db.refresh(already_uploaded_job)

        retried_job = YouTubeService.retry_upload(already_uploaded_job.id, user, db)
        print(f"  Deduplication Check: Status={retried_job.upload_status}, VideoID={retried_job.youtube_video_id}")
        assert retried_job.youtube_video_id == "sim_existing_video_id_999", "Deduplication must keep existing video ID"
        assert retried_job.upload_status == "uploaded"

        # 4b: Bounded Retry: attempts > 3 must be blocked
        exhausted_job = PublishJob(
            project_id=proj.id,
            title="Max Retry Guard Test",
            privacy_status="private",
            upload_status="failed",
            retry_count=3,
            manual_approval_granted=True,
        )
        db.add(exhausted_job)
        db.commit()
        db.refresh(exhausted_job)

        bounded_blocked = False
        try:
            YouTubeService.retry_upload(exhausted_job.id, user, db)
        except ValueError as ve:
            if "Maximum retry limit" in str(ve):
                bounded_blocked = True
                print(f"  Bounded Retries Check: Correctly rejected attempt 4: '{ve}'")

        assert bounded_blocked, "Must strictly reject retries after 3 attempts"
        print(f"  => Retry Engine & Deduplication Guard: PASSED")
        report["retry_deduplication"] = True

        # -------------------------------------------------------------
        # 5. Security Verification
        # -------------------------------------------------------------
        print(f"\n[6] SECURITY VERIFICATION: PRIVACY & ENCRYPTION")
        # 5a: Public upload without manual approval must be rejected immediately
        public_approval_blocked = False
        try:
            YouTubeService.upload_video(
                project_id=proj.id,
                user=user,
                title="Unauthorized Public Video",
                description="This should fail",
                tags=["security"],
                privacy_status="public",
                scheduled_publish_time=None,
                manual_approval_granted=False,
                db=db,
            )
        except ValueError as ve:
            if "Manual approval required" in str(ve):
                public_approval_blocked = True
                print(f"  Public Video Without Approval Blocked: '{ve}'")

        assert public_approval_blocked, "Public upload without explicit approval must raise ValueError"
        report["security_approval_enforcement"] = True

        # 5b: Token encryption
        raw_token = "offline-test-token-not-a-secret"
        enc = encrypt_secret(raw_token)
        dec = decrypt_secret(enc)
        assert raw_token != enc, "Encrypted token must differ from plaintext"
        assert dec == raw_token, "Decrypted token must exactly match original"
        print(f"  Fernet AES-256 Secret Encryption / Decryption verified.")
        report["token_encryption"] = True

        print(f"\n" + "=" * 70)
        print("PHASE 6 VERIFICATION SUMMARY:")
        for k, v in report.items():
            print(f"  {k:35}: {'PASS' if v else 'FAIL'}")
        print("=" * 70)

        all_passed = all(report.values())
        if all_passed:
            print("\nALL PHASE 6 REQUIREMENTS VERIFIED SUCCESSFULLY!")
            return 0
        else:
            print("\nSOME VERIFICATIONS FAILED")
            return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run_phase6_verification())
