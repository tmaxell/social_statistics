import re
import json
import requests
import threading
import multiprocessing
import string
import nltk
from collections import Counter
from PyQt5 import QtWidgets
from pyrogram import Client

from configuration import *

DATA = {
    'vk': {},
    'telegram': {}
}

bad_symb = set(['❤️', '❤', ':', 'https', 'это'])

stop_words = set(nltk.corpus.stopwords.words('russian')).union(set(nltk.corpus.stopwords.words('english'))).union(bad_symb)


def get_channel_messages(api_id, api_hash, channel_names):
    data = {}
    with Client("acc", api_id, api_hash) as app:
        for channel in channel_names:
            data[channel] = []
            channel_info = app.get_chat(channel)
            for post in app.get_chat_history(channel_info.id, limit=100):
                if post.caption:
                    data[channel].append(post.caption)
    DATA['telegram'] = data


def get_group_messages(access_token, group_ids):
    messages = {}
    for group in group_ids:
        messages[group] = []
        response = requests.get(
            f"https://api.vk.com/method/wall.get?owner_id=-{group}&access_token={access_token}&v=5.131")
        if response.status_code == 200:
            data = response.json()
            for item in data["response"]["items"]:
                messages[group].append(item["text"])
    DATA['vk'] = messages


def get_data_in_parallel(telegram_func, *functions):
    threads = []
    telegram_func()
    for function in functions:
        thread = threading.Thread(target=function)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


def remove_stopwords(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'http\S+', '', text)
    words = text.split()
    filtered_words = [word for word in words
                      if word.strip().lower() not in stop_words]
    return ' '.join(filtered_words)


def remove_punctuation_test(text):
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator)


def remove_punctuation(text):
    words = nltk.word_tokenize(text)
    words_without_punct = [word for word in words if word.isalnum()]
    return ' '.join(words_without_punct)


def process_messages(messages):
    return [remove_punctuation(remove_stopwords(message)) for message in messages]


def process_data(data):
    with multiprocessing.Pool() as pool:
        for source, messages in data.items():
            for key, value in messages.items():
                messages[key] = pool.map(process_messages, [value])[0]


def analyze_messages(messages, sort=True):
    text = ' '.join(messages)

    words = nltk.tokenize.word_tokenize(text)

    hashtags = [word[1:] for word in words if word.startswith('#')]
    keywords = [word for word in words if word.lower() not in hashtags]

    hashtag_counts = Counter(hashtags)
    keyword_counts = Counter(keywords)

    topics = [topic for topic, count in keyword_counts.most_common(10)]

    if sort:
        return {
            'hashtags': dict(hashtag_counts.most_common()),
            'keywords': dict(keyword_counts.most_common()),
            'topics': topics
        }

    return {
        'hashtags': dict(hashtag_counts),
        'keywords': dict(keyword_counts),
        'topics': topics
    }


def analyze(data):
    result = {
        "common_keywords": Counter(),
        "common_hashtags": Counter()
    }
    for media, source in data.items():
        result[media] = {
            "common_keywords": Counter(),
            "common_hashtags": Counter()
        }
        for channel, messages in source.items():
            analyzed_messages = analyze_messages(messages)
            result[media][channel] = analyzed_messages
            result[media]['common_keywords'] += Counter(analyzed_messages['keywords'])
            result[media]['common_hashtags'] += Counter(analyzed_messages['hashtags'])

        result['common_keywords'] += result[media]['common_keywords']
        result['common_hashtags'] += result[media]['common_hashtags']

        result[media]['common_topics'] = [topic for topic, count in result[media]['common_keywords'].most_common(10)]
        result[media]['common_keywords'] = dict(result[media]['common_keywords'].most_common())
        result[media]['common_hashtags'] = dict(result[media]['common_hashtags'].most_common())
    result['common_topics'] = [topic for topic, count in result['common_keywords'].most_common(10)]
    result['common_keywords'] = dict(result['common_keywords'].most_common())
    result['common_hashtags'] = dict(result['common_hashtags'].most_common())

    return result


def save_res_to_file(data, filename):
    with open(f'{filename}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_input_id_list(s):
    return [int(i.strip()) for i in s.split(',')]


def get_input_channel_list(s):
    return [i.strip() for i in s.split(',')]


def start():
    result_text.clear()
    if entry1.text():
        tg_ch = get_input_channel_list(entry1.text())
    else:
        result_text.append("Enter tg channels separated by @")

    if entry2.text():
        vk_id = get_input_id_list(entry2.text())
    else:
        result_text.append("Enter vk group IDs")

    vk_messages = lambda: get_group_messages(vk_token, vk_id)

    tele_messages = lambda: get_channel_messages(teleapi_id, teleapi_hash, tg_ch)
    get_data_in_parallel(tele_messages, vk_messages)
    process_data(DATA)

    result = analyze(DATA)
    save_res_to_file(result, 'dump')
    result_str = "- Common Topics:\n" + '\n'.join(result["common_topics"]) + "\n- Common Topics vk:\n" + '\n'.join(
        result['vk']["common_topics"]) + "\n- Common Topics telegram:\n" + '\n'.join(
        result['telegram']["common_topics"])

    result_text.append(result_str)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    # Create labels
    label1 = QtWidgets.QLabel("Enter Telegram channels:")
    label2 = QtWidgets.QLabel("Enter VK group IDs:")

    # Create input fields
    entry1 = QtWidgets.QLineEdit()
    entry2 = QtWidgets.QLineEdit()

    # Create start button
    button = QtWidgets.QPushButton("Start")
    button.clicked.connect(start)

    result_text = QtWidgets.QTextEdit()
    result_text.setReadOnly(True)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(label1)
    layout.addWidget(entry1)
    layout.addWidget(label2)
    layout.addWidget(entry2)
    layout.addWidget(button)
    layout.addWidget(result_text)

    window = QtWidgets.QWidget()
    window.setLayout(layout)
    window.show()

    app.exec_()
