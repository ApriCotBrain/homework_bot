import logging
import os
import sys
import time
from http import HTTPStatus

import exceptions
import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        logging.info('Начало отправки сообщения в TELEGRAM')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        raise exceptions.MyException(
            'Ошибка отправки сообщения в TELEGRAM')
    else:
        logging.info('Сообщение отправлено успешно.')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_status = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params)
        if homework_status.status_code != HTTPStatus.OK:
            raise exceptions.RegularCasesException(
                'Ошибка статуса!')
    except Exception:
        raise exceptions.RegularCasesException(
            'Эндпоинт недоступен!')
    return homework_status.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем.')
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise KeyError('Отсутствует ключ homeworks.')
    if 'current_date' not in response:
        raise KeyError('Отсутствует ключ current_date.')
    if not isinstance(homeworks, list):
        raise TypeError('Ответ API не является списком.')
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        message = 'Нет домашней работы'
        raise KeyError(message)
    if homework_status is None:
        message = 'Нет новых статусов'
        raise KeyError(message)
    if homework_status not in HOMEWORK_STATUSES:
        message = 'Незнакомый статус'
        raise KeyError(message)
    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Не доступна переменная окружения!')
        sys.exit("Отсутствуют необходимые переменные окружения")
    logging.info('Все переменные окружения доступны.')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_send = {'error': None}
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logging.debug('Нет новых статусов.')
            for homework in homeworks:
                message = parse_status(homework)
                if prev_send.get(homework['homework_name']) != message:
                    send_message(bot, message)
                    prev_send[homework['homework_name']] = message
            current_timestamp = response.get('current_date')

        except exceptions.RegularCasesException:
            logging.error('Что-то пошло не так!')
        except exceptions.MyException as error:
            logging.error('Сбой в работе программы!')
            message = f'Сбой в работе программы: {error}'
            if prev_send['error'] != message:
                send_message(bot, message)
                prev_send['error'] = message
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
