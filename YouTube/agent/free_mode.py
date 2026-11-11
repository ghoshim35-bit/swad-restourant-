"""YouTube Free Mode - bina Claude API key ke (koi AI kharcha nahi), simple menu se channel chalaiye.

Run:  python free_mode.py
Sirf YouTube Data API ka free quota use hota hai. Title/description aap khud likhte hain.
"""

from __future__ import annotations

import json

import youtube_api as ytapi

MENU = """
──────── 🆓 YouTube Free Mode ────────
 1. Connected channel dekho
 2. Trending videos (ideas ke liye)
 3. Meri videos + views
 4. Local folder ki videos dekho
 5. Video upload karo
 6. Video ka title/description/tags/privacy badlo
 7. Thumbnail lagao
 8. Comments dekho
 9. Comment ka reply karo
10. Video delete karo
 0. Exit
"""


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    return input(f"   {prompt}{hint}: ").strip() or default


def ask_int(prompt: str, default: int) -> int:
    value = ask(prompt, str(default))
    return int(value) if value.isdigit() else default


def confirm(action: str) -> bool:
    answer = input(f"\n⚠️  Confirm: {action}\n   Karna hai? (y/n): ").strip().lower()
    return answer in {"y", "yes", "haan", "ha", "han"}


def show(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=1))


def ask_privacy(default: str) -> str:
    privacy = ask("Privacy (private/unlisted/public)", default).lower()
    if privacy not in {"private", "unlisted", "public", ""}:
        raise ValueError("privacy sirf private, unlisted ya public ho sakti hai")
    return privacy


def upload(yt) -> None:
    path = ask("Video file ka path (jaise videos/my.mp4)")
    title = ask("Title (max 100 characters)")
    description = ask("Description")
    tags = [t.strip() for t in ask("Tags (comma se alag)").split(",") if t.strip()]
    privacy = ask_privacy("private")
    publish_at = ask("Schedule time UTC (jaise 2026-12-01T12:30:00Z), khaali = abhi nahi")
    when = f", scheduled {publish_at}" if publish_at else ""
    if confirm(f'Upload "{path}" as {privacy}{when} with title "{title}"'):
        show(ytapi.upload_video(yt, path, title, description, tags, privacy, publish_at=publish_at or None))


def update(yt) -> None:
    video_id = ask("Video ID")
    title = ask("Naya title (khaali = same)")
    description = ask("Nayi description (khaali = same)")
    tags_raw = ask("Naye tags comma se (khaali = same)")
    privacy = ask_privacy("")
    if privacy == "public" and not confirm(f"Make video {video_id} PUBLIC"):
        return
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else None
    show(ytapi.update_video(yt, video_id, title=title or None, description=description or None,
                            tags=tags, privacy=privacy or None))


def reply(yt) -> None:
    comment_id = ask("Comment ID")
    text = ask("Reply text")
    if text and confirm(f'Reply to comment {comment_id}: "{text}"'):
        show(ytapi.reply_to_comment(yt, comment_id, text))


def delete(yt) -> None:
    video_id = ask("Video ID")
    if confirm(f"PERMANENTLY DELETE video {video_id} (wapas nahi aayega)"):
        show(ytapi.delete_video(yt, video_id))


ACTIONS = {
    "1": lambda yt: show(ytapi.get_my_channel(yt)),
    "2": lambda yt: show(ytapi.get_trending(yt, ask("Country code", "IN").upper(),
                                            ask("Category ID (10 Music, 20 Gaming, 24 Entertainment; khaali = sab)"),
                                            ask_int("Kitni videos", 15))),
    "3": lambda yt: show(ytapi.list_my_videos(yt, ask_int("Kitni videos", 10))),
    "4": lambda yt: show(ytapi.list_local_videos(ask("Folder", "videos"))),
    "5": upload,
    "6": update,
    "7": lambda yt: show(ytapi.set_thumbnail(yt, ask("Video ID"), ask("Image path (JPG/PNG, max 2MB)"))),
    "8": lambda yt: show(ytapi.list_comments(yt, ask("Video ID"), ask_int("Kitne comments", 20))),
    "9": reply,
    "10": delete,
}


def main() -> None:
    print("🆓 Free Mode - koi AI / Claude API key nahi chahiye. YouTube login ho raha hai...")
    try:
        yt = ytapi.get_service()
        ch = ytapi.get_my_channel(yt)
    except Exception as e:
        print(f"❌ YouTube login nahi hua: {e}")
        return
    print(f"   ✅ Connected channel: {ch.get('title')} {ch.get('handle', '')}")
    while True:
        print(MENU)
        try:
            choice = input("👤 Number chuniye: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if choice in {"0", "exit", "quit", "band"}:
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("   ❓ Galat number, dobara try kijiye.")
            continue
        try:
            action(yt)
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            print(f"   ❌ {type(e).__name__}: {e}")
    print("👋 Bye!")


if __name__ == "__main__":
    main()
