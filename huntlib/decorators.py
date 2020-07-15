#!/usr/bin/env python

from functools import wraps
import time

#import random

def retry(retries=3, delay=1):
    '''
    In the case of transient exceptions, transparently retry the wrapped 
    function a fewtimes.  If the exception persists, re-raise the exception
    to the calling process.

    :param retries: The number of retries (DEFAULT: 3)
    :type retries: integer
    :param delay: The number of seconds to sleep between retries
    :type delay: integer
    '''

    def _retry(func):
        @wraps(func) 
        def wrapper(*args, **kwargs):
            # Do the stuff 
            retval = None
            for i in range(1, retries+1):
                try:
                    retval = func(*args, **kwargs)
                except Exception as e:
                    # If we're all out of retries, raise the exception.
                    # Otherwise sleep and try again
                    if i == retries:
                        raise
                    else:
                        time.sleep(delay)
                        continue
                break
            return retval
        return wrapper

    return _retry 
