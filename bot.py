import requests
import json
import time
import re
from auto_eitaa import Bot

API_URL = "https://script.google.com/macros/s/AKfycbwh0JqZAQaKI0UjbAY08US5Ah79FXH0ThVeoIbdSl_jx7Xk3wAbgxLQV2N1xzCFi8XG/exec"
SAVE_URL = "https://amirmahdicode.github.io/EitaaReaction/save.html"

EMOJI_MAP = {
    'rofl': '🤣',
    'heart_eyes': '😍',
    'neutral': '😐',
    'cursing': '🤬',
    'mind_blown': '🤯',
    'poop': '💩',
    'heart': '❤️',
    'broken_heart': '💔',
    'kiss': '💋',
    'clap': '👏🏻',
    'thumbs_up': '👍🏻',
    'thumbs_down': '👎🏻',
    'moon': '🌚',
    'otter': '🦦',
    'cherry': '🍒',
    'peach': '🍑',
    'banana': '🍌',
    'party': '🎉',
    'cool': '🕶️',
    'iran': '🇮🇷',
    'fire': '🔥'
}

post_list = {}

def extract_channel_link(post_link):
    match = re.match(r'(https://eitaa\.com/[^/]+/)', post_link)
    if match:
        return match.group(1)
    return None

def is_channel(chat_type):
    return chat_type == 'chatTypeChannel'

def get_post_id(eitaa_link):
    try:
        encoded_link = requests.utils.quote(eitaa_link, safe='')
        response = requests.get(
            f"{API_URL}?action=get_post_id&eitaa_link={encoded_link}"
        )
        data = response.json()
        if data['success'] and data['post_id']:
            return data['post_id']
        return None
    except:
        return None

def add_link(eitaa_link, post_id):
    try:
        encoded_link = requests.utils.quote(eitaa_link, safe='')
        requests.get(
            f"{API_URL}?action=add_link&eitaa_link={encoded_link}&post_id={post_id}"
        )
    except:
        pass

def get_reactions(post_id):
    try:
        response = requests.get(f"{API_URL}?action=get&post={post_id}")
        return response.json()
    except:
        return None

def generate_reaction_text(post_id):
    data = get_reactions(post_id)
    if not data or 'reactions' not in data:
        return ""
    
    parts = []
    reactions = data['reactions']
    
    for key, emoji in EMOJI_MAP.items():
        value = reactions.get(key, False)
        if value is not False and value != 'false' and value != 'FALSE':
            link = f"{SAVE_URL}?post={post_id}&emoji={key}"
            parts.append(f"[{emoji} {value}]({link})")
    
    return " ".join(parts)

def save_post_list():
    with open('post_list.json', 'w', encoding='utf-8') as f:
        json.dump(post_list, f, ensure_ascii=False, indent=2)

def load_post_list():
    global post_list
    try:
        with open('post_list.json', 'r', encoding='utf-8') as f:
            post_list = json.load(f)
    except:
        post_list = {}

def process_messages(bot):
    global post_list
    
    while True:
        try:
            for chat_index in range(1, 20):
                try:
                    messages = bot.on_new_message(chat_index)
                    if messages:
                        for key, msg in messages.items():
                            if isinstance(msg, dict):
                                eitaa_link = msg.get('link', '')
                                chat_type = msg.get('chat', {}).get('type', '')
                                
                                if not eitaa_link or not is_channel(chat_type):
                                    continue
                                
                                channel_link = extract_channel_link(eitaa_link)
                                if not channel_link:
                                    continue
                                
                                post_id = get_post_id(channel_link)
                                
                                if not post_id:
                                    post_id = channel_link.rstrip('/').split('/')[-1]
                                    add_link(channel_link, post_id)
                                
                                message_id = msg.get('message_id', '')
                                post_list[post_id] = {
                                    'channel_link': channel_link,
                                    'last_message_id': message_id
                                }
                                save_post_list()
                                
                                reaction_text = generate_reaction_text(post_id)
                                
                                original_text = msg.get('text', '')
                                new_text = original_text + "\n\n" + reaction_text
                                
                                message_map = msg.get('map', None)
                                if message_map:
                                    bot.edit_message(new_text, message_map)
                                
                                print(f"New post {post_id}: {reaction_text}")
                except:
                    continue
            
            time.sleep(1800)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

def update_reactions_periodically(bot):
    global post_list
    
    while True:
        try:
            for post_id in list(post_list.keys()):
                reaction_text = generate_reaction_text(post_id)
                
                channel_link = post_list[post_id].get('channel_link', '')
                
                if channel_link:
                    bot.go_chat(channel_link)
                    time.sleep(5)
                    
                    messages = bot.on_new_message(1)
                    if messages:
                        for key, msg in messages.items():
                            if isinstance(msg, dict):
                                eitaa_link = msg.get('link', '')
                                current_channel_link = extract_channel_link(eitaa_link)
                                
                                if current_channel_link == channel_link:
                                    original_text = msg.get('text', '')
                                    
                                    lines = original_text.split('\n')
                                    cleaned_text = '\n'.join(
                                        line for line in lines 
                                        if not line.strip().startswith('[')
                                    ).strip()
                                    
                                    new_text = cleaned_text + "\n\n" + reaction_text
                                    
                                    message_map = msg.get('map', None)
                                    if message_map:
                                        bot.edit_message(new_text, message_map)
                                    
                                    print(f"Updated reactions for post {post_id}")
                                    break
                
                time.sleep(2)
            
            time.sleep(1800)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

load_post_list()

bot = Bot(headless=False, autologin=True, Browser="2")

print("ربات ریکشن ایتا آماده است...")

import threading
threading.Thread(target=update_reactions_periodically, args=(bot,), daemon=True).start()

process_messages(bot)
