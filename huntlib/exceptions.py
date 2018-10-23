__all__ = [
    'BaseSearchException',
    'InvalidRequestSearchException',
    'AuthenticationErrorSearchException',
    'UnknownSearchException'
]

class BaseSearchException(Exception):
    '''
    A generic base class for exceptions from the ElasticDF and SplunkDF classes.
    '''
    pass

class InvalidRequestSearchException(BaseSearchException):
    '''
    Used when the user's request search is syntactically correct but
    invalid (e.g., they requested more results be returned than the server
    is capable of returning).
    '''
    pass

class AuthenticationErrorSearchException(BaseSearchException):
    '''
    Raised when the search server rejected the supplied credentials.
    '''
    pass

class UnknownSearchException(BaseSearchException):
    '''
    Returned when we must raise an exception but we don't have a better
    defined exception.
    '''
