from datetime import datetime


class Clock:
    @staticmethod
    def now():
        return datetime.now()