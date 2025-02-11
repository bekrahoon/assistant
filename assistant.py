import speech_recognition as sr
import pyttsx3
import os
import pyautogui
import webbrowser
import torch
import subprocess
import time
import pygetwindow as gw
from transformers import AutoModelForCausalLM, AutoTokenizer
import keyboard

# Загрузка модели GPT-2 через transformers
MODEL_NAME = "sberbank-ai/rugpt3small_based_on_gpt2"
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Устанавливаем pad_token
tokenizer.pad_token = tokenizer.eos_token  # Используем eos_token как pad_token

# Настройка синтеза речи
engine = pyttsx3.init()
voices = engine.getProperty("voices")


# Выбор голоса (по умолчанию 0 — Irina, 1 — Pavel)
selected_voice = 5
engine.setProperty("voice", voices[selected_voice].id)
engine.setProperty("rate", 150)


def speak(text):
    """Озвучивание текста"""
    engine.say(text)
    engine.runAndWait()


def recognize_speech(language="ru-RU"):
    """Распознавание речи"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Слушаю...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language=language).lower()
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None


def switch_to_english():
    """Переключить раскладку на английский"""
    keyboard.press_and_release("ctrl+shift")  # Комбинация для переключения раскладки


def switch_to_russian():
    """Переключить раскладку на русский"""
    keyboard.press_and_release("ctrl+shift")  # Комбинация для переключения раскладки


def safe_type(text):
    """Безопасный ввод текста с переключением раскладки"""
    print(f"Текст для ввода: {text}")
    switch_to_english()  # Переключаем на английскую раскладку
    time.sleep(1)  # Даем время на переключение

    # Вводим текст посимвольно
    for char in text:
        keyboard.write(char)
        time.sleep(0.1)  # Задержка между символами

    time.sleep(1)  # Задержка для надежности
    switch_to_russian()  # Переключаем обратно на русскую
    print("Текст введен.")


def ask_ai(prompt):
    """Ответ нейросети, если команда не найдена"""
    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)

    # Обратите внимание на добавление attention_mask
    inputs["attention_mask"] = inputs.get(
        "attention_mask", torch.ones_like(inputs["input_ids"])
    )

    # Генерация ответа с явным указанием pad_token_id
    outputs = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        pad_token_id=tokenizer.pad_token_id,  # Указание pad_token_id
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


def focus_on_window(window_title):
    """Фокусировка на окне по частичному совпадению заголовка"""
    windows = gw.getWindowsWithTitle(window_title)
    print(f"Найденные окна: {[window.title for window in windows]}")
    if windows:
        window = windows[0]
        if not window.isActive:
            try:
                window.activate()  # Фокусируем окно только если оно не активно
                time.sleep(2)  # Добавляем паузу на всякий случай
                return True
            except Exception as e:
                print(f"Ошибка при активации окна: {e}")
                return False
    else:
        print(f"Окно с заголовком '{window_title}' не найдено.")
        return False


def execute_command(command):
    """Обработка команд"""
    global selected_voice  # Используем global для изменения переменной selected_voice

    # Карта программ
    program_map = {
        "telegram": r"C:\Users\user\AppData\Roaming\Telegram Desktop\Telegram.exe",
        "discord": r"C:\Users\user\AppData\Local\Discord\Update.exe --processStart Discord.exe",
        "vscode": r"C:\Users\user\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "проводник": "explorer",
        "блокнот": "notepad",
        "калькулятор": "calc",
        "whatsapp": r"C:\Users\user\Desktop\WhatsApp — ярлык.lnk",
        "docker": r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        "обсидиан": r"C:\Users\user\AppData\Local\Programs\Obsidian\Obsidian.exe",
    }

    # Карта браузеров
    browsers_map = {
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "яндекс": r"C:\Users\user\AppData\Local\Yandex\YandexBrowser\Application\browser.exe",
        "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    }

    web_map = {
        "youtube": "https://www.youtube.com",
        "гугл": "https://www.google.com",
        "вк": "https://vk.com",
        "tiktok": "https://www.tiktok.com",
    }

    # Открытие браузера
    if "открой браузер" in command:
        os.system("start chrome")
        speak("Открываю браузер")

    elif "открой" in command:
        for browser_name, browser_path in browsers_map.items():
            if browser_name in command:
                speak(f"Открываю {browser_name}")
                subprocess.Popen(browser_path, shell=True)
                return

        for prog_name, prog_path in program_map.items():
            if prog_name in command:
                speak(f"Открываю {prog_name}")
                subprocess.Popen(prog_path, shell=True)
                time.sleep(2)  # Ожидание для загрузки программы
                if focus_on_window("Telegram"):  # Используем часть заголовка
                    speak(f"Теперь я в окне {prog_name}")
                return

        for web_name, web_path in web_map.items():
            if web_name in command:
                speak(f"Открываю {web_name}")
                webbrowser.open(web_path)
                time.sleep(2)  # Ожидание для загрузки страницы
                if focus_on_window(web_name):  # Фокусируем на окне браузера
                    speak(f"Теперь я в окне {web_name}")
                return

        speak("Не знаю такую программу. Попробуйте сказать по-другому.")

    elif "закрой" in command:
        if "вкладку" in command:
            pyautogui.hotkey("ctrl", "w")  # Закрыть текущую вкладку
            speak("Закрываю вкладку")
        else:
            pyautogui.hotkey("alt", "f4")  # Закрыть окно
            speak("Закрываю")

    elif "выключи компьютер" in command:
        speak("Выключаю компьютер")
        os.system("shutdown /s /t 5")

    elif "смени голос" in command:
        selected_voice = 4 if selected_voice == 5 else 5
        engine.setProperty("voice", voices[selected_voice].id)
        speak("Голос изменён.")

    elif "управляй курсором" in command:
        speak("Я готов управлять курсором. Скажите, куда двигать.")
        # Пример перемещения курсора:
        pyautogui.moveTo(100, 100, duration=1)  # Переместить в координаты (100, 100)
        speak("Перемещаю курсор.")

    elif "введи текст" in command:
        speak("Какой текст я должен ввести?")
        text_to_input = recognize_speech(language="ru-RU")  # Установим русский язык
        if text_to_input:
            # Пробуем ввести текст с учётом переключения раскладки
            safe_type(text_to_input)
            print(f"Ввёл: {text_to_input}")
            speak(f"Ввёл")

    elif "нажми enter" in command or "enter" in command:
        keyboard.press_and_release("enter")  # Нажимаем Enter
        speak("Нажимаю Enter")

    elif "нажми пробел" in command or "пробел" in command:
        keyboard.press_and_release("space")  # Нажимаем пробел
        speak("Нажимаю пробел")

    elif "нажми tab" in command or "фокус" in command:
        keyboard.press_and_release("tab")  # Нажимаем Tab
        speak("Нажимаю Tab")

    else:
        speak("Я не знаю эту команду, попробуйте еще раз.")


# Главный цикл
speak("Привет! Я ваш голосовой помощник.")
while True:
    command = recognize_speech()
    if command:
        print("Вы сказали:", command)
        execute_command(command)
