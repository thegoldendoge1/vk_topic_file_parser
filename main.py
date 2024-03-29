import os
import requests
from dotenv import load_dotenv
import vk_api
import telebot
import time
from datetime import datetime

load_dotenv()

VK_ACCESS_TOKEN = os.getenv('VK_TOKEN')
GROUP_ID = 1818225
TOPIC_ID = 37846957
# GROUP_ID = 203755141
# TOPIC_ID = 50773939
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_IDS = [579264104]  # Список идентификаторов чатов

vk_session = vk_api.VkApi(token=VK_ACCESS_TOKEN)
vk = vk_session.get_api()
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_sent_files():
    if os.path.exists("sent_files.txt"):
        with open("sent_files.txt", "r") as f:
            return f.read().splitlines()
    else:
        return []


def save_sent_files(sent_files):
    with open("sent_files.txt", "w") as f:
        for file_id in sent_files:
            f.write(file_id + "\n")


def send_message_to_multiple_chats(message):
    for chat_id in TELEGRAM_CHAT_IDS:
        bot.send_message(chat_id, message)


def check_new_files():
    try:
        # Получение комментариев к топику
        comments = vk.board.getComments(group_id=GROUP_ID, topic_id=TOPIC_ID, count=100)
        new_files = []
        for comment in comments['items']:
            if 'attachments' in comment:
                for attachment in comment['attachments']:
                    if attachment['type'] == 'doc':
                        doc = attachment['doc']
                        file_id = str(doc['id'])
                        file_name = doc['title']
                        new_files.append(file_id)
                        # Проверяем, был ли файл уже отправлен
                        if file_id not in sent_files:
                            file_url = doc['url']
                            # Скачиваем файл локально
                            response = requests.get(file_url)
                            with open(file_name, 'wb') as f:
                                f.write(response.content)
                            # Отправляем файл в телеграм
                            with open(file_name, 'rb') as f:
                                for chat_id in TELEGRAM_CHAT_IDS:
                                    f.seek(0)  # Перемещаем указатель чтения в начало файла
                                    bot.send_document(chat_id, f, caption=file_name)

                            # Удаляем локальный файл
                            os.remove(file_name)
        # Сохраняем список отправленных файлов
        sent_files.extend(new_files)
        save_sent_files(sent_files)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Проверка завершена в {current_time}. Ожидание следующей проверки...")
    except vk_api.exceptions.ApiError as e:
        print("Ошибка при выполнении запроса:", e)


def main():
    global sent_files
    sent_files = get_sent_files()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Очистка консоли
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Скрипт запущен. Последняя проверка выполнялась в {current_time}")
        check_new_files()
        # Пауза перед следующей проверкой (например, каждые 5 минут)
        time.sleep(300)  # 300 секунд = 5 минут


if __name__ == '__main__':
    main()
