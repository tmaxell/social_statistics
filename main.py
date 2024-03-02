import string
import threading
from threading import Thread
from queue import Queue
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy
from collections import Counter
import vk_api
from telethon.sync import TelegramClient
import asyncio
import tkinter as tk

vk_key = ''
tg_id = ''
tg_hash = ''

vk_session = vk_api.VkApi(token=vk_key)
vk_api_instance = vk_session.get_api()

nlp = spacy.load("ru_core_news_sm")

def vk_get_user_id(username):
    try:
        response = vk_api_instance.users.get(user_ids=username)
        user_id = response[0]['id']
        return user_id
    except Exception as e:
        print(f"Ошибка1: {e}")
        return None

def vk_get_wall(owner_id, count):
    try:
        response = vk_api_instance.wall.get(owner_id=owner_id, count=count)
        return response['items']
    except Exception as e:
        print(f"Ошибка2: {e}")
        return []

def scrape_vk(users, groups, data_queue):
    for username in users:
        user_id = vk_get_user_id(username)
        if user_id is not None:
            posts = vk_get_wall(user_id, 30)
            for post in posts:
                data_queue.put(post['text'])

    for group_id in groups:
        posts = vk_get_wall(group_id, 30)
        for post in posts:
            data_queue.put(post['text'])

async def scrape_telegram(group_names, data_queue, num_messages):
    api_id = tg_id
    api_hash = tg_hash

    client = TelegramClient('session_name', api_id, api_hash,
                        system_version='4.16.30-vxCUSTOM')
    await client.start()
    for group_name in group_names:
        group_entity = await client.get_input_entity(group_name)

        async for message in client.iter_messages(group_entity, limit=num_messages):
            data_queue.put(message.text)
    await client.disconnect()
    client.disconnect()
lock = threading.Lock()

def preprocess_data(data_queue, preprocessed_data, stop_words):
    while True:
        data = data_queue.get()
        if data is None:
            break

        data = data.lower()
        tokens = word_tokenize(data, language='russian')
        tokens = [word for word in tokens if word not in stop_words and not all(c in string.punctuation + '–«»—“”''utm_source=telegramoid=-67991642act=a_subscribe_boxhttps//vk.com/widget_community.phpstate=1|подпишись' for c in word)]

        with lock:
            preprocessed_data.extend(tokens)

def analyze(data, keyword_counts):
    doc = nlp(data)
    target_keywords = ["израиль"]
    for token in doc:
        if token.text in target_keywords:
            keyword_counts[token.text] += 1

def main():
    num_threads = 1
    vk_users = ['durov']
    vk_groups = [-67991642, -15755094, -20169232, -40316705, -27532693]
    telegram_groups = ['bbcrussian','dwglavnoe','piterach','Cbpub','bazabazon']

    data_queue_vk = Queue()
    data_queue_telegram = Queue()
    preprocessed_data_vk = []
    preprocessed_data_telegram = []
    keyword_counts_vk = Counter()
    keyword_counts_telegram = Counter()
    stop_words = set(stopwords.words('russian'))

    vk_threads = [Thread(target=scrape_vk, args=(vk_users, vk_groups, data_queue_vk)) for _ in range(num_threads)]
    num_telegram_messages = 30

    telegram_thread = Thread(target=lambda: asyncio.run(scrape_telegram(telegram_groups, data_queue_telegram, num_telegram_messages)))
    preprocessing_threads = [Thread(target=preprocess_data, args=(data_queue_vk, preprocessed_data_vk, stop_words)),
                             Thread(target=preprocess_data, args=(data_queue_telegram, preprocessed_data_telegram, stop_words))]

    for thread in vk_threads:
        thread.start()

    telegram_thread.start()

    for thread in preprocessing_threads:
        thread.start()

    for thread in vk_threads:
        thread.join()

    telegram_thread.join()

    for _ in range(num_threads):
        data_queue_vk.put(None)
        data_queue_telegram.put(None)

    for thread in preprocessing_threads:
        thread.join()

    for data_item in preprocessed_data_vk:
        analyze(data_item, keyword_counts_vk)

    for data_item in preprocessed_data_telegram:
        analyze(data_item, keyword_counts_telegram)

    for keyword, count in keyword_counts_vk.items():
        keyword_counts_vk[keyword] = count // (num_threads + 1)

    for keyword, count in keyword_counts_telegram.items():
        keyword_counts_telegram[keyword] = count // (num_threads + 1)

    result_text_vk.delete(1.0, tk.END)
    result_text_telegram.delete(1.0, tk.END)
    result_text_vk.insert(tk.END, "Количество найденных ключевых слов в VK:\n")
    result_text_vk.insert(tk.END, str(keyword_counts_vk) + "\n")

    result_text_vk.insert(tk.END, "\nТоп 10 слов и их количество в VK:\n")
    word_counts_vk = Counter(preprocessed_data_vk)
    top_words_vk = word_counts_vk.most_common(10)
    for word, count in top_words_vk:
        result_text_vk.insert(tk.END, f'{word}: {count // (num_threads + 1)}\n')
    result_text_telegram.insert(tk.END, "Количество найденных ключевых слов в Telegram:\n")
    result_text_telegram.insert(tk.END, str(keyword_counts_telegram) + "\n")

    result_text_telegram.insert(tk.END, "\nТоп 10 слов и их количество в Telegram:\n")
    word_counts_telegram = Counter(preprocessed_data_telegram)
    top_words_telegram = word_counts_telegram.most_common(10)
    for word, count in top_words_telegram:
        result_text_telegram.insert(tk.END, f'{word}: {count // (num_threads + 1)}\n')
    result_text_vk.insert(tk.END, "Анализ данных в VK завершен. Результаты выведены в текстовом поле.")
    result_text_telegram.insert(tk.END, "Анализ данных в Telegram завершен. Результаты выведены в текстовом поле.")

root = tk.Tk()

instructions_label = tk.Label(root, text="Нажмите кнопку, чтобы проанализировать данные.")
instructions_label.pack(pady=10)
result_text_vk = tk.Text(root)
result_text_vk.pack()
result_text_telegram = tk.Text(root)
result_text_telegram.pack()
analyze_button = tk.Button(root, text="Проанализировать данные", command=main)
analyze_button.pack(pady=10)

root.mainloop()