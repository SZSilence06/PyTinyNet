class RequestError(Exception):
    pass

class InvalidRequestError(RequestError):
    def __init__(self, message):
        super(InvalidRequestError, self).__init__(message)

class RequestFailedError(RequestError):
    def __init__(self, message):
        super(RequestFailedError, self).__init__(message)

class RequestTimeoutError(RequestError):
    def __init__(self):
        super(RequestTimeoutError, self).__init__('Request time out.')


