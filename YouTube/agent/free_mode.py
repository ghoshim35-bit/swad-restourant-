"""Free mode - bina Claude API key ke YouTube ka kaam (menu se).

YouTube Data API free hai (roz ka quota), isliye yeh mode bilkul free chalta hai.
Title / description / tags aap khud likhenge. AI wala mode: python youtube_agent.py

Run:  python free_mode.py
"""

from __future__ import annotations

import youtube_api as ytapi

MENU = """
========== YouTube Free Mode ==========
 1. Kaunsa channel connected hai
 2. India mein kya trend kar raha hai (ideas ke liye)
 3. Meri videos aur views
 4. Video upload karo
 5. Video ka title / description badlo
 6. Video ke comments dekho
 0. Band karo
======================================="""


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    value = input(f"{prompt}{hint}: ").strip()
    return value or default


def show_channel(yt) -> None:
    ch = ytapi.get_my_channel(yt)
    if "error" in ch:
        print("❌", ch["error"])
        return
    print(f"\n✅ {ch['title']} {ch['handle']}")
    print(f"   Subscribers: {ch['subscribers']}  |  Videos: {ch['videos']}")


def show_trending(yt) -> None:
    print("\nCategory: khaali = sab, 10 = Music, 20 = Gaming, 24 = Entertainment, 26 = Howto & Style")
    category = ask("Category number")
    for i, v in enumerate(ytapi.get_trending(yt, "IN", category, 15), 1):
        print(f"\n{i}. {v['title']}")
        print(f"   {v['channel']}  |  {v['views']:,} views")
        if v["tags"]:
            print(f"   Tags: {', '.join(v['tags'][:6])}")
    print("\n💡 Inse idea lekar APNI video banaiye. Doosron ki video upload karne se copyright strike aati hai.")


def show_my_videos(yt) -> None:
    videos = ytapi.list_my_videos(yt, 10)
    if not videos:
        print("\nAbhi koi video nahi hai.")
    for v in videos:
        print(f"\n• {v['title']}  ({v['privacy']})")
        print(f"  ID: {v['video_id']}  |  {v['views']} views, {v['likes']} likes, {v['comments']} comments")


def upload(yt) -> None:
    folder = ask("Video kis folder mein hai", "videos")
    try:
        files = ytapi.list_local_videos(folder)
    except FileNotFoundError as e:
        print("❌", e)
        return
    if not files:
        print(f"❌ '{folder}' mein koi video file (.mp4, .mov ...) nahi mili.")
        return
    for i, f in enumerate(files, 1):
        print(f" {i}. {f['path']}  ({f['size_mb']} MB)")
    choice = ask("Kaunsi video (number)", "1")
    if not choice.isdigit() or not 1 <= int(choice) <= len(files):
        print("❌ Galat number.")
        return
    path = files[int(choice) - 1]["path"]
    title = ask("Title")
    if not title:
        print("❌ Title zaroori hai.")
        return
    description = ask("Description")
    tags = [t.strip() for t in ask("Tags (comma se alag)").split(",") if t.strip()]
    privacy = ask("Privacy: private / unlisted / public", "private")
    if privacy not in {"private", "unlisted", "public"}:
        print("❌ private, unlisted ya public likhiye.")
        return
    if ask(f'\n"{title}" ko {privacy} upload karein? (y/n)', "n").lower() not in {"y", "yes", "haan", "ha"}:
        print("Upload cancel.")
        return
    result = ytapi.upload_video(yt, path, title, description, tags, privacy)
    print(f"\n✅ Upload ho gaya! {result['url']}")


def edit(yt) -> None:
    video_id = ask("Video ID (option 3 se milega)")
    if not video_id:
        return
    title = ask("Naya title (khaali = mat badlo)")
    description = ask("Nayi description (khaali = mat badlo)")
    if not title and not description:
        print("Kuch nahi badla.")
        return
    ytapi.update_video(yt, video_id, title=title or None, description=description or None)
    print("✅ Update ho gaya.")


def comments(yt) -> None:
    video_id = ask("Video ID (option 3 se milega)")
    if not video_id:
        return
    items = ytapi.list_comments(yt, video_id, 20)
    if not items:
        print("Koi comment nahi.")
    for c in items:
        print(f"\n• {c['author']}: {c['text']}")


ACTIONS = {"1": show_channel, "2": show_trending, "3": show_my_videos,
           "4": upload, "5": edit, "6": comments}


def main() -> None:
    print("YouTube se login ho raha hai (pehli baar browser khulega)...")
    yt = ytapi.get_service()
    show_channel(yt)
    while True:
        print(MENU)
        try:
            choice = input("Number chuniye: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if choice == "0":
            break
        action = ACTIONS.get(choice)
        if not action:
            print("❌ 0 se 6 tak ka number likhiye.")
            continue
        try:
            action(yt)
        except Exception as e:
            print(f"❌ Error: {e}")
    print("👋 Bye!")


if __name__ == "__main__":
    main()
