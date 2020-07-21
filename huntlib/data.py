import pandas as pd 
import numpy as np 

from glob import glob 

import os

__all__ = ['read_json', 'read_csv', 'flatten']

def _read_multi(func=None, path_or_buf=None, *args, **kwargs):
    """
    Given a wildcard filename pattern (which may be just a single static
    filename), expand the wildcard and read all the files into a single
    pandas DataFrame() object.  

    :param func: Reference to the function which will read an individual data file (e.g., pd.read_csv)
    :param path_or_buf: A wildcard specifying which file(s) to read
    :type func: A reference to a valid function which returns a pd.DataFrame() object
    :type path_or_buf: A `str`, `bytes` or os.PathLike object
    """

    # Make sure we have specified a read function.  This should never
    # be called by an end user, so our code should always include one,
    # but you never know.
    if not func:
        raise ValueError("Must specify a read function in the `func` arg.")

    # Make sure we have a valid type of data for `path_or_buf` in glob(),
    # otherwise raise the same exception the original pandas function 
    # would
    if not type(path_or_buf) in [str, bytes, os.PathLike]:
        raise ValueError(f"Invalid file path or buffer object type: {type(path_or_buf)}")

    combined_df = pd.concat(
        [
            func(f, *args, **kwargs)
            for f in glob(path_or_buf)
        ],
        ignore_index=True
    )

    return combined_df

def read_json(path_or_buf=None, *args, **kwargs):
    """
    A convenience wrapper for _read_multi() that uses pd.read_json as the
    read function.
    """

    return _read_multi(
        func=pd.read_json,
        path_or_buf=path_or_buf,
        *args,
        **kwargs
    )

def read_csv(path_or_buf=None, *args, **kwargs):
    """
    A convenience wrapper for _read_multi() that uses pd.read_csv as the
    read function.
    """

    return _read_multi(
        func=pd.read_csv,
        path_or_buf=path_or_buf,
        *args,
        **kwargs
    )


def flatten(obj, sep='.'):
    '''
    Given a dictionary or list that may contain other dictionaries
    or lists, recursively flatten all the values into a single 
    level and return them as a list.

    :param obj: The possibly-multilevel object to flatten
    :param type: dict or list object
    :param sep: The character to use to separate the path names. (DEFAULT '.')
    :param sep: string

    :Return Value:
    A dict containing all the entries of member dicts or lists in a single
    flat keyspace. 

    For example:

    >>> flatten({"key1": "val1", "subkeys": {"subkey1": "subval1"}})
    {'key1': 'val1', 'subkeys.subkey1': 'subval1'}

    Lists are flattened according to their indices:

    >>> flatten([1, 2, 3])
    {'0': 1, '1': 2, '2': 3}

    A more complex example:

    >>> huntlib.flatten([dict(a='a', b='b'), dict(a='a1', c='c')])
    {'0.a': 'a', '0.b': 'b', '1.a': 'a1', '1.c': 'c'}

    '''
    def _flatten(obj, keypath='', sep='.'):

        if isinstance(obj, dict):
            keypath = keypath + sep if keypath else keypath
            for k in obj:
                yield from _flatten(obj[k], keypath + str(k), sep=sep)
        elif isinstance(obj, list):
            keypath = keypath + sep if keypath else keypath
            for k in range(len(obj)):
                yield from _flatten(obj[k], keypath + str(k), sep=sep)
        else:
            yield keypath, obj

    return dict(_flatten(obj=obj, sep=sep))
