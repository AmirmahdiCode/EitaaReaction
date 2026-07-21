from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from colorama import Fore
import requests
import json
import time
import os
import pyperclip


class EitaaBot:
    def __init__(self, headless=False, autologin=True, browser="2"):
        try:
            requests.get("https://web.eitaa.com/")
        except:
            print(Fore.RED + "Eitaa is down or system is offline!" + Fore.WHITE)
            return

        print(Fore.CYAN + "Starting..." + Fore.WHITE)

        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

        try:
            self.driver.get("https://web.eitaa.com/")
            time.sleep(5)
        except:
            print("Error loading Eitaa")
            return

        if autologin:
            self._auto_login()
        else:
            self._manual_login()

    def _manual_login(self):
        print("\n" + Fore.YELLOW + "Please login manually in the Chrome window..." + Fore.WHITE)
        print("After login is complete, come back here and press ENTER.")
        input("Press ENTER to continue...")
        
        save = input("Save login for next time? (y/n): ")
        if save.lower() == "y":
            data_auth = self.driver.execute_script("""
                var items = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            """)
            with open("login.json", "w") as f:
                json.dump(data_auth, f, indent=4)
            print(Fore.GREEN + "Login saved!" + Fore.WHITE)

    def _auto_login(self):
        try:
            with open("login.json", "r") as f:
                account_data = json.load(f)
                script = ""
                for key, value in account_data.items():
                    escaped_key = json.dumps(key)
                    escaped_value = json.dumps(value)
                    script += f"localStorage.setItem({escaped_key}, {escaped_value});"
                self.driver.execute_script(script)
                self.driver.refresh()
                time.sleep(10)
                print(Fore.GREEN + "Auto-login successful!" + Fore.WHITE)
        except:
            print(Fore.RED + "Login data not found!" + Fore.WHITE)
            self._manual_login()

    def go_chat(self, chat_id):
        self.driver.get("https://web.eitaa.com/#" + str(chat_id))
        time.sleep(5)

    def edit_message(self, new_text, message_element):
        try:
            action = ActionChains(self.driver)
            action.context_click(on_element=message_element)
            action.perform()
            time.sleep(2)
            
            edit_btn = self.driver.find_element(By.CSS_SELECTOR, 'div.tgico-edit > div:nth-child(1)')
            edit_btn.click()
            time.sleep(1)
            
            input_box = self.driver.find_element(By.CSS_SELECTOR, 'div.input-message-input:nth-child(1)')
            input_box.send_keys(Keys.CONTROL + 'a')
            input_box.send_keys(Keys.BACKSPACE)
            
            pyperclip.copy(new_text)
            input_box.send_keys(Keys.CONTROL + 'v')
            time.sleep(1)
            
            input_box.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            print(f"Edit error: {e}")
            return False

    def on_new_message(self, chat_position=1):
        try:
            chat = self.driver.find_element(By.CSS_SELECTOR, f"li.chatlist-chat:nth-child({chat_position})")
            chat_id = str(chat.get_attribute('data-peer-id'))
            
            try:
                badge = chat.find_element(By.CLASS_NAME, "dialog-subtitle-badge")
                unread_count = int(badge.get_attribute('innerHTML'))
            except:
                return None
            
            chat.click()
            time.sleep(5)
            
            result = {}
            for i in range(1, min(unread_count + 1, 10)):
                try:
                    bubble = self.driver.find_elements(By.CLASS_NAME, "bubble")[-i]
                except:
                    continue
                
                message_id = bubble.get_attribute("data-mid")
                
                try:
                    message_div = bubble.find_element(By.CLASS_NAME, "message")
                    text = message_div.text
                    
                    result[str(i)] = {
                        'message_id': str(message_id),
                        'text': str(text),
                        'map': message_div,
                        'chat': {
                            'id': str(chat_id),
                            'type': str(self._get_dialog_type(chat_id))
                        }
                    }
                except:
                    continue
            
            return result
        except Exception as e:
            print(f"on_new_message error: {e}")
            return None

    def _get_dialog_type(self, chat_id):
        try:
            return self.driver.execute_script(f"return appPeersManager.getDialogType({chat_id});")
        except:
            return "unknown"

    def get_message_link(self, message_element):
        try:
            action = ActionChains(self.driver)
            action.context_click(on_element=message_element)
            action.perform()
            time.sleep(2)
            
            link_btn = self.driver.find_element(By.CSS_SELECTOR, "div.tgico-link:nth-child(12)")
            link_btn.click()
            time.sleep(0.5)
            
            return pyperclip.paste()
        except:
            return ""

    def close(self):
        try:
            self.driver.quit()
        except:
            pass
