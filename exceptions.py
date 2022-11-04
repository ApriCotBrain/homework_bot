class BasedException(Exception):
    """Штатные отклонения от основного сценария."""


class HomeworkException(BasedException):
    """От сервера не пришли домашние работы."""


class TimeException(BasedException):
    """Сервер не прислал новую отсечку времени."""


class TelegramException(Exception):
    """Требуют пересылки в TELEGRAM."""


class EndpointError(TelegramException):
    """Недоступен Эндпоинт."""
