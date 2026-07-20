import requests
import json
import time
import re
import threading
from eitaa_core import EitaaBot

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
    return match.group(1) if match else None

def is_channel(chat_type):
    return chat_type == 'chatTypeChannel'

def get_post_id(eitaa_link):
    try:
        encoded_link = requests.utils.quote(eitaa_link, safe='')
        response = requests.get(f"{API_URL}?action=get_post_id&eitaa_link={encoded_link}")
        data = response.json()
        return data['post_id'] if data.get('success') and data.get('post_id') else None
    except:
        return None

def add_link(eitaa_link, post_id):
    try:
        encoded_link = requests.utils.quote(eitaa_link, safe='')
        requests.get(f"{API_URL}?action=add_link&eitaa_link={encoded_link}&post_id={post_id}")
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

def add_reactions_to_message(bot, post_id, message_map, original_text):
    reaction_text = generate_reaction_text(post_id)
    lines = original_text.split('\n')
    cleaned_text = '\n'.join(line for line in lines if not line.strip().startswith('[')).strip()
    new_text = cleaned_text + "\n\n" + reaction_text
    bot.edit_message(new_text, message_map)

def process_messages(bot):
    global post_list
    
    while True:
        try:
            for chat_index in range(1, 20):
                try:
                    messages = bot.on_new_message(chat_index)
                    if not messages:
                        continue
                    
                    for key, msg in messages.items():
                        if not isinstance(msg, dict):
                            continue
                        
                        chat_type = msg.get('chat', {}).get('type', '')
                        if not is_channel(chat_type):
                            continue
                        
                        message_map = msg.get('map')
                        if not message_map:
                            continue
                        
                        eitaa_link = bot.get_message_link(message_map)
                        if not eitaa_link:
                            continue
                        
                        channel_link = extract_channel_link(eitaa_link)
                        if not channel_link:
                            continue
                        
                        post_id = get_post_id(channel_link)
                        if not post_id:
                            post_id = channel_link.rstrip('/').split('/')[-1]
                            add_link(channel_link, post_id)
                        
                        post_list[post_id] = {'channel_link': channel_link}
                        save_post_list()
                        
                        add_reactions_to_message(bot, post_id, message_map, msg.get('text', ''))
                        print(f"Added reactions to post {post_id}")
                        
                except Exception as e:
                    print(f"Chat {chat_index} error: {e}")
                    continue
            
            time.sleep(1800)
            
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(60)

def update_reactions_periodically(bot):
    global post_list
    
    while True:
        try:
            for post_id in list(post_list.keys()):
                try:
                    channel_link = post_list[post_id].get('channel_link', '')
                    if not channel_link:
                        continue
                    
                    bot.go_chat(channel_link)
                    time.sleep(5)
                    
                    messages = bot.on_new_message(1)
                    if not messages:
                        continue
                    
                    for key, msg in messages.items():
                        if not isinstance(msg, dict):
                            continue
                        
                        message_map = msg.get('map')
                        if not message_map:
                            continue
                        
                        eitaa_link = bot.get_message_link(message_map)
                        current_channel_link = extract_channel_link(eitaa_link)
                        
                        if current_channel_link == channel_link:
                            add_reactions_to_message(bot, post_id, message_map, msg.get('text', ''))
                            print(f"Updated reactions for post {post_id}")
                            break
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Update post {post_id} error: {e}")
                    continue
            
            time.sleep(1800)
            
        except Exception as e:
            print(f"Update loop error: {e}")
            time.sleep(60)

load_post_list()

bot = EitaaBot(headless=False, autologin=True, browser="2")

print("ربات ریکشن ایتا آماده است...")

threading.Thread(target=update_reactions_periodically, args=(bot,), daemon=True).start()

process_messages(bot)
