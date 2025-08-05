import requests
import os
import telegram

from dotenv import load_dotenv


def send_message(chat_id, api_key, lesson_title, is_negative, lesson_url):
    bot = telegram.Bot(token=api_key)

    if is_negative:
        is_negative = 'К сожалению, в работе нашлись ошибки.'
    else:
        is_negative = '''Преподавателю все понравилось,
                        можно приступать к следующему уроку!'''

    text = f'''У вас проверили работу {lesson_title}. \n
            {lesson_url} \n\n {is_negative}'''
    bot.send_message(text=text, chat_id=chat_id)


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
            continue
        except requests.exceptions.ConnectionError:
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
                chat_id, api_key, lesson_title, is_negative, lesson_url
                )
            continue

        if timestamp_response_expired:
            payload.update({
                'timestamp': timestamp_response_expired
            })


if __name__ == "__main__":
    load_dotenv()
    token_devman = os.getenv('TOKEN_DEVMAN')
    chat_id = os.getenv('CHAT_ID_TG_BOT')
    api_key = os.getenv('API_KEY_TG_BOT')

    get_notifications(token_devman)
