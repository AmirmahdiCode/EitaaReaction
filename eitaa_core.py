from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from colorama import Fore
import requests
import pyperclip
import json
import time
import os


class EitaaBot:
    def __init__(self, headless=False, autologin=True, browser="2"):
        try:
            requests.get("https://web.eitaa.com/")
        except:
            print(Fore.RED + "Eitaa is down or system is offline!" + Fore.WHITE)
            return

        print(Fore.CYAN + "Starting..." + Fore.WHITE)

        if browser == "1":
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            self.driver = webdriver.Firefox(options=options)
        else:
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            self.driver = webdriver.Chrome(options=options)

        try:
            self.driver.get("https://web.eitaa.com/")
        except:
            print("Error loading Eitaa")
            return

        if autologin:
            self._auto_login()
        else:
            self._login()

    def _login(self):
        while True:
            try:
                phone_input = self.driver.find_element(By.CSS_SELECTOR, "div.input-field:nth-child(2) > div:nth-child(1)")
            except:
                continue
            else:
                phone = input("Phone number (+98): ")
                phone_input.send_keys(Keys.CONTROL + 'a')
                phone_input.send_keys(Keys.BACKSPACE)
                phone_input.send_keys(str(phone))
                self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary:nth-child(4)").click()
                break

        while True:
            try:
                code_input = self.driver.find_element(By.CSS_SELECTOR, "input.input-field-input")
            except:
                continue
            else:
                otp = input("OTP Code: ")
                code_input.send_keys(str(otp))
                break

        while True:
            try:
                self.driver.find_element(By.CSS_SELECTOR, '#main-search')
            except:
                try:
                    status = self.driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[3]/div/div[3]/div/label/span")
                    if status.text == "کد نامعتبر است":
                        print("Wrong OTP!")
                        return
                except:
                    print("Waiting...", end="\r")
                    continue
            else:
                os.system('cls')
                time.sleep(15.5)
                print(Fore.GREEN + "Logged in!" + Fore.WHITE)
                
                save = input("Save login? (y/n): ")
                if save == "y":
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
                    print("Login saved!")
                break

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
                os.system('cls')
                time.sleep(15.5)
                print(Fore.GREEN + "Auto-login successful!" + Fore.WHITE)
        except:
            print(Fore.RED + "Login data not found!" + Fore.WHITE)
            self._login()

    def go_chat(self, chat_id):
        self.driver.get("https://web.eitaa.com/#" + str(chat_id))
        time.sleep(3)

    def chat_id(self):
        try:
            chat = self.driver.find_element(By.CSS_SELECTOR, "div.user-title > span:nth-child(1)")
            return str(chat.get_attribute("data-peer-id"))
        except:
            return None

    def edit_message(self, new_text, message_element):
        try:
            action = ActionChains(self.driver)
            action.context_click(on_element=message_element)
            action.perform()
            time.sleep(1)
            
            edit_btn = self.driver.find_element(By.CSS_SELECTOR, 'div.tgico-edit > div:nth-child(1)')
            edit_btn.click()
            time.sleep(0.5)
            
            input_box = self.driver.find_element(By.CSS_SELECTOR, 'div.input-message-input:nth-child(1)')
            input_box.send_keys(Keys.CONTROL + 'a')
            input_box.send_keys(Keys.BACKSPACE)
            
            new_text = new_text.replace('\n', '\n')
            lines = new_text.split('\n')
            for i, line in enumerate(lines):
                input_box.send_keys(line)
                if i < len(lines) - 1:
                    input_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            input_box.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            print(f"Edit error: {e}")
            return False

    def on_new_message(self, chat_position=1):
        try:
            chat = self.driver.find_element(By.CSS_SELECTOR, f"li.chatlist-chat:nth-child({chat_position})")
            chat_id = str(chat.get_attribute('data-peer-id'))
            cp = chat.find_element(By.CLASS_NAME, "user-caption")
            sub = cp.find_element(By.CLASS_NAME, "dialog-subtitle")
            
            try:
                badge = sub.find_element(By.CLASS_NAME, "dialog-subtitle-badge")
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
                    content_wrapper = bubble.find_element(By.CLASS_NAME, "bubble-content-wrapper")
                    content = content_wrapper.find_element(By.CLASS_NAME, "bubble-content")
                    message_div = content.find_element(By.CLASS_NAME, "message")
                    
                    text = message_div.text
                    time_element = message_div.find_element(By.TAG_NAME, "span")
                    
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

    def _get_link(self, message_element):
        try:
            action = ActionChains(self.driver)
            action.context_click(on_element=message_element)
            action.perform()
            time.sleep(1)
            
            link_btn = self.driver.find_element(By.CSS_SELECTOR, "div.tgico-link:nth-child(12)")
            link_btn.click()
            time.sleep(0.2)
            return str(pyperclip.paste())
        except:
            return ""

    def get_message_link(self, message_element):
        return self._get_link(message_element)

    def close(self):
        try:
            self.driver.quit()
        except:
            pass
