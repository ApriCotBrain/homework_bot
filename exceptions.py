class BasedException(Exception):
    """Штатные отклонения от основного сценария."""


class HomeworkException(BasedException):
    """От сервера не пришли домашние работы."""


class TimeException(BasedException):
    """Сервер не прислал новую отсечку времени."""


class EndpointError(BasedException):
    """Недоступен Эндпоинт."""


class TelegramException(Exception):
    """Ошибка отправки в TELEGRAM."""
