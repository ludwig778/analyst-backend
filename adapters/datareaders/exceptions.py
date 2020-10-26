class DataReaderException(Exception):
    pass


class SymbolNotFound(DataReaderException):
    pass


class TooMuchApiCall(DataReaderException):
    pass


class NoDataAvailable(DataReaderException):
    pass
