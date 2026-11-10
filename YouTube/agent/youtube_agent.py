"""YouTube AI Agent - Claude se baat karke videos upload aur manage kijiye.

Run:  python youtube_agent.py
Examples (Hindi/Hinglish/English sab chalega):
  - "videos/ folder me jo video hai use upload karo, title aur description khud likho"
  - "meri last 5 videos ke views dikhao"
  - "video abc123 ka title better banao"
  - "latest video ke comments ka reply karo"
"""

from __future__ import annotations

import json
from datetime import date

import anthropic
from anthropic import beta_tool

import youtube_api as ytapi

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = f"""You are a YouTube channel manager agent for the user. Today is {date.today().isoformat()}.
You can upload videos, set thumbnails, list videos with stats, update titles/descriptions/tags/privacy,
read and reply to comments, and delete videos, using the tools provided.

Reply in the same language the user writes in (often Hinglish).

When uploading, write a catchy title (under 70 characters), an SEO-friendly description with a short
hook in the first two lines plus relevant hashtags, and 10-15 tags, unless the user gave their own.
Upload as "private" unless the user clearly asks for public or unlisted.

Before deleting a video, changing privacy to public, or replying to comments, tell the user what you are
about to do; the tool will also ask the user to confirm. If the user declines, do not retry - ask what
they want instead. If a tool returns an error, explain it simply and suggest the fix."""

_yt = None


def yt():
    """Lazily log in to YouTube the first time a tool needs it."""
    global _yt
    if _yt is None:
        _yt = ytapi.get_service()
        ch = ytapi.get_my_channel(_yt)
        print(f"   ✅ Connected channel: {ch.get('title')} {ch.get('handle', '')}")
    return _yt


def confirm(action: str) -> bool:
    answer = input(f"\n⚠️  Confirm: {action}\n   Karna hai? (y/n): ").strip().lower()
    return answer in {"y", "yes", "haan", "ha", "han"}


def _ok(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=1)


def _err(e: Exception) -> str:
    return _ok({"error": f"{type(e).__name__}: {e}"})


DECLINED = _ok({"declined": True, "message": "User ne mana kar diya / user declined."})


@beta_tool
def get_my_channel() -> str:
    """Show which YouTube channel is connected (name, handle, subscribers, video count)."""
    try:
        return _ok(ytapi.get_my_channel(yt()))
    except Exception as e:
        return _err(e)


@beta_tool
def list_local_videos(folder: str) -> str:
    """List video files in a folder on this computer, so you can pick one to upload.

    Args:
        folder: Folder path, e.g. "videos" or "C:/Users/me/Videos".
    """
    try:
        return _ok(ytapi.list_local_videos(folder))
    except Exception as e:
        return _err(e)


@beta_tool
def upload_video(
    file_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str = "private",
    publish_at: str = "",
    made_for_kids: bool = False,
) -> str:
    """Upload a video file to the user's YouTube channel.

    Args:
        file_path: Path to the video file.
        title: Video title (max 100 characters).
        description: Video description (max 5000 characters).
        tags: List of tags.
        privacy: One of "private", "unlisted", "public".
        publish_at: Optional ISO 8601 UTC time to schedule publishing, e.g. "2026-12-01T12:30:00Z". Empty for none.
        made_for_kids: Whether the video is made for kids.
    """
    if privacy not in {"private", "unlisted", "public"}:
        return _err(ValueError("privacy must be private, unlisted or public"))
    when = f", scheduled {publish_at}" if publish_at else ""
    if not confirm(f'Upload "{file_path}" as {privacy}{when} with title "{title}"'):
        return DECLINED
    try:
        return _ok(ytapi.upload_video(
            yt(), file_path, title, description, tags, privacy,
            publish_at=publish_at or None, made_for_kids=made_for_kids,
        ))
    except Exception as e:
        return _err(e)


@beta_tool
def set_thumbnail(video_id: str, image_path: str) -> str:
    """Set a custom thumbnail image (JPG/PNG, max 2MB) for a video.

    Args:
        video_id: The YouTube video ID.
        image_path: Path to the image file.
    """
    try:
        return _ok(ytapi.set_thumbnail(yt(), video_id, image_path))
    except Exception as e:
        return _err(e)


@beta_tool
def list_my_videos(max_results: int = 10) -> str:
    """List the channel's most recent uploads with views, likes, comments and privacy.

    Args:
        max_results: How many videos to list (1-50).
    """
    try:
        return _ok(ytapi.list_my_videos(yt(), max_results))
    except Exception as e:
        return _err(e)


@beta_tool
def get_video_details(video_ids: list[str]) -> str:
    """Get title, description, tags, privacy and stats for specific videos.

    Args:
        video_ids: List of YouTube video IDs.
    """
    try:
        return _ok(ytapi.get_video_details(yt(), video_ids))
    except Exception as e:
        return _err(e)


@beta_tool
def update_video(
    video_id: str,
    title: str = "",
    description: str = "",
    tags: list[str] | None = None,
    privacy: str = "",
) -> str:
    """Update a video's title, description, tags and/or privacy. Empty fields are left unchanged.

    Args:
        video_id: The YouTube video ID.
        title: New title, or empty to keep.
        description: New description, or empty to keep.
        tags: New list of tags, or null to keep.
        privacy: "private", "unlisted", "public", or empty to keep.
    """
    if privacy and privacy not in {"private", "unlisted", "public"}:
        return _err(ValueError("privacy must be private, unlisted or public"))
    if privacy == "public" and not confirm(f"Make video {video_id} PUBLIC"):
        return DECLINED
    try:
        return _ok(ytapi.update_video(
            yt(), video_id,
            title=title or None, description=description or None,
            tags=tags, privacy=privacy or None,
        ))
    except Exception as e:
        return _err(e)


@beta_tool
def delete_video(video_id: str) -> str:
    """Permanently delete a video from the channel. This cannot be undone.

    Args:
        video_id: The YouTube video ID.
    """
    if not confirm(f"PERMANENTLY DELETE video {video_id} (wapas nahi aayega)"):
        return DECLINED
    try:
        return _ok(ytapi.delete_video(yt(), video_id))
    except Exception as e:
        return _err(e)


@beta_tool
def list_comments(video_id: str, max_results: int = 20) -> str:
    """List the latest top-level comments on a video.

    Args:
        video_id: The YouTube video ID.
        max_results: How many comments (1-100).
    """
    try:
        return _ok(ytapi.list_comments(yt(), video_id, max_results))
    except Exception as e:
        return _err(e)


@beta_tool
def reply_to_comment(comment_id: str, text: str) -> str:
    """Post a public reply to a comment as the channel.

    Args:
        comment_id: The comment ID to reply to.
        text: Reply text.
    """
    if not confirm(f'Reply to comment {comment_id}: "{text}"'):
        return DECLINED
    try:
        return _ok(ytapi.reply_to_comment(yt(), comment_id, text))
    except Exception as e:
        return _err(e)


TOOLS = [
    get_my_channel, list_local_videos, upload_video, set_thumbnail, list_my_videos, get_video_details,
    update_video, delete_video, list_comments, reply_to_comment,
]


def run_turn(client: anthropic.Anthropic, history: list) -> None:
    """Let Claude work (calling tools as needed) until it answers; extend history in place."""
    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        # If the main model declines a request, the API retries it on a fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        tools=TOOLS,
        messages=list(history),
        max_iterations=30,
    )
    for message in runner:
        history.append({"role": "assistant", "content": message.content})
        for block in message.content:
            if block.type == "text" and block.text.strip():
                print(f"\n🤖 {block.text}")
            elif block.type == "tool_use":
                print(f"   🔧 {block.name}(...)")
        if message.stop_reason == "refusal":
            print("\n🤖 Yeh request handle nahi ho sakti. Kuch aur try kijiye.")
            return
        if message.stop_reason == "max_tokens":
            print("\n🤖 Jawab bahut lamba ho gaya - thoda chhota sawal poochiye.")
            return
        tool_results = runner.generate_tool_call_response()  # cached: tools run once
        if tool_results is not None:
            history.append(tool_results)


def main() -> None:
    client = anthropic.Anthropic()
    history: list = []
    print("🎬 YouTube AI Agent ready! Kya karna hai? (exit likhkar band karein)\n")
    while True:
        try:
            user = input("\n👤 Aap: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue
        if user.lower() in {"exit", "quit", "bye", "band"}:
            break
        start = len(history)
        history.append({"role": "user", "content": user})
        try:
            run_turn(client, history)
        except anthropic.AuthenticationError:
            print("❌ ANTHROPIC_API_KEY galat hai ya set nahi hai. README dekhiye.")
            del history[start:]
        except anthropic.RateLimitError:
            print("⏳ Rate limit lag gaya - thodi der baad try kijiye.")
            del history[start:]
        except anthropic.APIStatusError as e:
            print(f"❌ API error ({e.status_code}): {e.message}")
            del history[start:]
        except anthropic.APIConnectionError:
            print("🌐 Internet connection check kijiye.")
            del history[start:]
    print("👋 Bye!")


if __name__ == "__main__":
    main()
