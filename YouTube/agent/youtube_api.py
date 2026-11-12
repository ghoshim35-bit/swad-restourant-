"""YouTube Data API v3 helpers: login, upload, list, update, delete, stats, comments."""

from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

HERE = Path(__file__).resolve().parent
CLIENT_SECRET = Path(os.environ.get("YT_CLIENT_SECRET", HERE / "client_secret.json"))
TOKEN_FILE = Path(os.environ.get("YT_TOKEN_FILE", HERE / "token.json"))

# force-ssl covers read/update/delete/comments; upload is its own scope.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.upload",
]

# Google lets users untick individual permissions; don't crash, check below instead.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def get_service():
    """Log in with OAuth (browser opens the first time) and return a YouTube client."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                raise FileNotFoundError(
                    f"{CLIENT_SECRET} nahi mila. README.md ke 'Setup' steps follow karke "
                    "Google Cloud se client_secret.json download kijiye."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
            granted = set(getattr(creds, "granted_scopes", None) or creds.scopes or SCOPES)
            missing = [s for s in SCOPES if s not in granted]
            if missing:
                raise PermissionError(
                    "Google login mein saari permissions nahi mili. Allow page par "
                    "'Manage your YouTube account' aur 'Manage your YouTube videos' - dono "
                    "checkbox (ya 'Select all') tick karke Continue dabaiye. Phir se chalaiye."
                )
        TOKEN_FILE.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def get_my_channel(yt) -> dict:
    """Return the channel this login is connected to (to confirm the right account)."""
    res = yt.channels().list(part="snippet,statistics", mine=True).execute()
    if not res.get("items"):
        return {"error": "Is Google account par koi YouTube channel nahi mila."}
    ch = res["items"][0]
    return {
        "channel_id": ch["id"],
        "title": ch["snippet"]["title"],
        "handle": ch["snippet"].get("customUrl", ""),
        "subscribers": int(ch["statistics"].get("subscriberCount", 0)),
        "videos": int(ch["statistics"].get("videoCount", 0)),
    }


def get_trending(yt, region_code: str = "IN", category_id: str = "", max_results: int = 15) -> list[dict]:
    """Most popular videos right now in a country - for topic and title ideas."""
    params = dict(part="snippet,statistics", chart="mostPopular",
                  regionCode=region_code, maxResults=min(max_results, 50))
    if category_id:
        params["videoCategoryId"] = category_id
    res = yt.videos().list(**params).execute()
    return [{
        "title": v["snippet"]["title"],
        "channel": v["snippet"]["channelTitle"],
        "views": int(v["statistics"].get("viewCount", 0)),
        "tags": v["snippet"].get("tags", [])[:10],
        "url": f"https://youtu.be/{v['id']}",
    } for v in res.get("items", [])]


def list_local_videos(folder: str) -> list[dict]:
    path = Path(folder).expanduser()
    if not path.is_dir():
        raise FileNotFoundError(f"Folder nahi mila: {path}")
    return [
        {"path": str(p), "size_mb": round(p.stat().st_size / 1_048_576, 1)}
        for p in sorted(path.iterdir())
        if p.suffix.lower() in VIDEO_EXTENSIONS
    ]


def upload_video(
    yt,
    file_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str = "private",
    category_id: str = "22",
    publish_at: str | None = None,
    made_for_kids: bool = False,
) -> dict:
    path = Path(file_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Video file nahi mili: {path}")
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": made_for_kids}
    if publish_at:
        # Scheduled publishing requires the video to be private until then.
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": category_id,
        },
        "status": status,
    }
    media = MediaFileUpload(str(path), chunksize=8 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        progress, response = request.next_chunk()
        if progress:
            print(f"  ...upload {int(progress.progress() * 100)}%")
    return {"video_id": response["id"], "url": f"https://youtu.be/{response['id']}"}


def set_thumbnail(yt, video_id: str, image_path: str) -> dict:
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Thumbnail file nahi mili: {path}")
    yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(path))).execute()
    return {"ok": True, "video_id": video_id}


def list_my_videos(yt, max_results: int = 10) -> list[dict]:
    channel = yt.channels().list(part="contentDetails", mine=True).execute()
    if not channel.get("items"):
        return []
    uploads = channel["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt.playlistItems().list(
        part="contentDetails", playlistId=uploads, maxResults=min(max_results, 50)
    ).execute()["items"]
    ids = [i["contentDetails"]["videoId"] for i in items]
    return get_video_details(yt, ids) if ids else []


def get_video_details(yt, video_ids: list[str]) -> list[dict]:
    res = yt.videos().list(part="snippet,status,statistics", id=",".join(video_ids)).execute()
    out = []
    for v in res.get("items", []):
        s = v.get("statistics", {})
        out.append({
            "video_id": v["id"],
            "title": v["snippet"]["title"],
            "published_at": v["snippet"].get("publishedAt"),
            "privacy": v["status"]["privacyStatus"],
            "views": int(s.get("viewCount", 0)),
            "likes": int(s.get("likeCount", 0)),
            "comments": int(s.get("commentCount", 0)),
            "tags": v["snippet"].get("tags", []),
            "description": v["snippet"].get("description", "")[:500],
        })
    return out


def update_video(
    yt,
    video_id: str,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    privacy: str | None = None,
) -> dict:
    current = yt.videos().list(part="snippet,status", id=video_id).execute()["items"]
    if not current:
        raise ValueError(f"Video nahi mila: {video_id}")
    video = current[0]
    snippet, status = video["snippet"], video["status"]
    if title is not None:
        snippet["title"] = title[:100]
    if description is not None:
        snippet["description"] = description[:5000]
    if tags is not None:
        snippet["tags"] = tags
    if privacy is not None:
        status["privacyStatus"] = privacy
    yt.videos().update(
        part="snippet,status",
        body={"id": video_id, "snippet": snippet, "status": status},
    ).execute()
    return {"ok": True, "video_id": video_id}


def delete_video(yt, video_id: str) -> dict:
    yt.videos().delete(id=video_id).execute()
    return {"ok": True, "deleted": video_id}


def list_comments(yt, video_id: str, max_results: int = 20) -> list[dict]:
    res = yt.commentThreads().list(
        part="snippet", videoId=video_id, maxResults=min(max_results, 100), order="time"
    ).execute()
    out = []
    for t in res.get("items", []):
        c = t["snippet"]["topLevelComment"]
        out.append({
            "comment_id": c["id"],
            "author": c["snippet"]["authorDisplayName"],
            "text": c["snippet"]["textOriginal"],
            "likes": c["snippet"].get("likeCount", 0),
            "replies": t["snippet"].get("totalReplyCount", 0),
        })
    return out


def reply_to_comment(yt, comment_id: str, text: str) -> dict:
    res = yt.comments().insert(
        part="snippet", body={"snippet": {"parentId": comment_id, "textOriginal": text}}
    ).execute()
    return {"ok": True, "reply_id": res["id"]}
