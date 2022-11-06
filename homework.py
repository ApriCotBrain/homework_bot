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
        logging.FileHandler('debug.log'),
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


def send_message(bot, message) -> None:
    """Отправляет сообщение в чат."""
    try:
        logging.info('Начало отправки сообщения в TELEGRAM')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        raise exceptions.TelegramException(
            'Ошибка отправки сообщения в TELEGRAM')
    else:
        logging.info('Сообщение отправлено успешно.')


def get_api_answer(current_timestamp) -> dict:
    """Делает запрос к эндпоинту сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params)
        if response.status_code != HTTPStatus.OK:
            raise exceptions.BasedException(
                f'Ошибка статуса {response.status_code}!',
                f'{response.reason}',
                f'{response.text}',
                f'{ENDPOINT}',
                f'{HEADERS}',
                f'{params}!'
            )
    except Exception:
        raise exceptions.BasedException(
            'Эндпоинт недоступен!')
    return response.json()


def check_response(response) -> list:
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


def parse_status(homework) -> str:
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


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Не доступна переменная окружения!')
        sys.exit("Отсутствуют необходимые переменные окружения")
    logging.info('Все переменные окружения доступны.')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    message = ''
    error_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug('Нет новых статусов.')
            else:
                homework = homeworks[0]
                new_message = parse_status(homework)
                if new_message != message:
                    send_message(bot, new_message)
                    message = new_message
            current_timestamp = response.get('current_date')

        except exceptions.TelegramException as error:
            logging.error(error, exc_info=error)
        except Exception as error:
            logging.error(Exception, exc_info=error)
            new_error_message = f'Сбой в работе программы: {error}'
            if new_error_message != error_message:
                send_message(bot, new_error_message)
                error_message = new_error_message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
