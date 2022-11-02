class RegularCasesException(Exception):
    """Штатные отклонения от основного сценария."""
    pass


class MyException(Exception):
    """Требуют пересылки в TELEGRAM."""
    pass
