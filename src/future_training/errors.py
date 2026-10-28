"""Sanitized application failures: never carry raw requests or driver exceptions."""


class ServiceError(Exception):
    def __init__(self, status: int, code: str, *, retryable: bool = False):
        self.status = status
        self.code = code
        self.retryable = retryable
        super().__init__(code)
