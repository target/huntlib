import pandas as pd 
import numpy as np 

from glob import glob 

import os

__all__ = ['read_json', 'read_csv']

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