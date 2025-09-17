import requests
import os
import telegram
import time
import logging

from handlers import TelegramLogsHandler
from dotenv import load_dotenv


def send_message(tg_bot, chat_id, lesson_title, is_negative, lesson_url):

    if is_negative:
        is_negative = 'К сожалению, в работе нашлись ошибки.'
    else:
        is_negative = '''Преподавателю все понравилось,
            можно приступать к следующему уроку!'''

    text = f'''У вас проверили работу {lesson_title}. \n
            {lesson_url} \n\n {is_negative}'''
    tg_bot.send_message(text=text, chat_id=chat_id)


def get_notifications(token_devman):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': token_devman
    }
    payload = {}

    while True:
        try:
            response = requests.get(
                url, params=payload, headers=headers, timeout=60
                )
            response.raise_for_status()
        except requests.ReadTimeout:
            logger.warning(
                '''Сервер занял слишком много времени, 
                чтобы отправлять данные из API Devman.'''
                )
            continue
        except requests.exceptions.ConnectionError:
            logger.warning('Была ошибка подключения с Devman API.')
            time.sleep(60)
            continue

        timestamp_response_expired = response.json().get(
            'timestamp_to_request'
            )
        timestamp_response_received = response.json().get(
            'last_attempt_timestamp'
            )

        if timestamp_response_received:
            new_attempts = response.json()['new_attempts'][0]

            lesson_title = new_attempts['lesson_title']
            is_negative = new_attempts['is_negative']
            lesson_url = new_attempts['lesson_url']

            send_message(
                tg_bot, chat_id, lesson_title, is_negative, lesson_url
                )
            continue

        if timestamp_response_expired:
            payload.update({
                'timestamp': timestamp_response_expired
            })


if __name__ == "__main__":
    load_dotenv()
    token_devman = os.environ['TOKEN_DEVMAN']
    chat_id = os.environ['CHAT_ID_TG_BOT']
    api_key = os.environ['API_KEY_TG_BOT']

    tg_bot = telegram.Bot(token=api_key)

    logger = logging.getLogger("telegram-bot")
    logger.setLevel(logging.DEBUG)

    tg_handler = TelegramLogsHandler(tg_bot, chat_id)
    tg_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        fmt='%(process)d %(levelname)s %(message)s',
        )
    tg_handler.setFormatter(formatter)
    logger.addHandler(tg_handler)

    get_notifications(token_devman)
