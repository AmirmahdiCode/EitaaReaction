# -*- coding: utf-8 -*-

import os
import json
import time
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PHONE_NUMBER = os.getenv("EITAA_PHONE", "09204209320")
SHEETS_API = "https://script.google.com/macros/s/AKfycbwh0JqZAQaKI0UjbAY08US5Ah79FXH0ThVeoIbdSl_jx7Xk3wAbgxLQV2N1xzCFi8XG/exec"
BASE_URL = "https://amirmahdicode.github.io/EitaaReaction/save.html"
CHECK_INTERVAL = 1800
POSTS_FILE = "registered_posts.json"

EMOJIS = [
    "rofl", "heart_eyes", "neutral", "cursing", "mind_blown",
    "poop", "heart", "broken_heart", "kiss", "clap",
    "thumbs_up", "thumbs_down", "moon", "otter", "cherry",
    "peach", "banana", "party", "cool", "iran", "fire"
]

EMOJI_CHARS = {
    "rofl": "🤣",
    "heart_eyes": "😍",
    "neutral": "😐",
    "cursing": "🤬",
    "mind_blown": "🤯",
    "poop": "💩",
    "heart": "❤️",
    "broken_heart": "💔",
    "kiss": "😘",
    "clap": "👏",
    "thumbs_up": "👍",
    "thumbs_down": "👎",
    "moon": "🌙",
    "otter": "🦦",
    "cherry": "🍒",
    "peach": "🍑",
    "banana": "🍌",
    "party": "🎉",
    "cool": "😎",
    "iran": "🇮🇷",
    "fire": "🔥"
}

try:
    from AutoEitaa import AutoEitaa
    print("✅ ماژول AutoEitaa پیدا شد!")
except ImportError:
    try:
        from auto_eitaa import AutoEitaa
        print("✅ ماژول auto_eitaa پیدا شد!")
    except ImportError:
        print("❌ خطا: کتابخانه AutoEitaa نصب نیست!")
        print("لطفاً ابتدا دستور زیر را اجرا کنید:")
        print("pip install -e .")
        exit(1)

def load_posts():
    if os.path.exists(POSTS_FILE):
        try:
            with open(POSTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_posts(posts):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4, ensure_ascii=False)

def get_reactions_for_post(post_id):
    try:
        url = f"{SHEETS_API}?action=get&post={post_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "reactions" in data:
                return data["reactions"]
            else:
                return {emoji: 0 for emoji in EMOJIS}
    except Exception as e:
        print(f"❌ خطا در دریافت ریکشن‌های پست {post_id}: {e}")
    return None

class ReactionBot:
    def __init__(self):
        self.bot = AutoEitaa()
        self.registered_posts = load_posts()
        self.running = True
        print("🚀 ربات ریکشن آماده راه‌اندازی است...")

    def on_ready(self):
        print(f"✅ ربات با شماره {PHONE_NUMBER} وارد شد!")
        print(f"📁 {len(self.registered_posts)} پیام از فایل محلی بارگذاری شد")
        self.start_update_timer()

    def start_update_timer(self):
        def update_loop():
            while self.running:
                time.sleep(CHECK_INTERVAL)
                print(f"⏰ به‌روزرسانی دوره‌ای در {datetime.now()}")
                self.update_all_posts()
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        print(f"⏱️ تایمر به‌روزرسانی هر {CHECK_INTERVAL//60} دقیقه تنظیم شد")

    def update_all_posts(self):
        for post_id, post_data in self.registered_posts.items():
            self.update_single_post(post_id, post_data)

    def extract_chat_id_from_link(self, eitaa_link):
        if not eitaa_link:
            return None
        try:
            if "/joinchat/" in eitaa_link:
                parts = eitaa_link.split("/joinchat/")
                if len(parts) > 1:
                    return parts[1].strip()
            elif "eitaa.com/" in eitaa_link:
                parts = eitaa_link.split("eitaa.com/")
                if len(parts) > 1:
                    username = parts[1].strip()
                    if username and not username.startswith("joinchat"):
                        return username
            return eitaa_link
        except:
            return eitaa_link

    def update_single_post(self, post_id, post_data):
        try:
            reactions = get_reactions_for_post(post_id)
            if reactions is None:
                return
            
            chat_id = self.extract_chat_id_from_link(post_data.get("eitaa_link", ""))
            if not chat_id:
                print(f"❌ chat_id برای پست {post_id} پیدا نشد")
                return
            
            new_text = self.build_reaction_text(reactions, post_id)
            
            self.bot.edit_message(
                chat_id=chat_id,
                message_id=int(post_id),
                text=new_text
            )
            print(f"✅ پست {post_id} به‌روز شد")
            
        except Exception as e:
            print(f"❌ خطا در به‌روزرسانی پست {post_id}: {e}")

    def build_reaction_text(self, reactions, post_id):
        reaction_links = []
        for emoji_name in EMOJIS:
            count = reactions.get(emoji_name, 0)
            emoji_char = EMOJI_CHARS.get(emoji_name, emoji_name)
            link = f"{BASE_URL}?post={post_id}&emoji={emoji_name}"
            reaction_links.append(f"[{emoji_char}{count}]({link})")
        return " ".join(reaction_links)

    def run(self):
        self.bot.on_ready(self.on_ready)
        print("🔑 در حال اتصال به ایتا...")
        self.bot.start(phone=PHONE_NUMBER)
        print("♻️ ربات در حال اجرا است. برای توقف Ctrl+C را بزنید.")
        self.bot.run()

if __name__ == "__main__":
    bot = ReactionBot()
    bot.run()
