"""
Miscellaneous functions useful for Threat Hunting and cybersecurity data analytics
"""
from __future__ import division

from builtins import input
import getpass
import math
from jellyfish import levenshtein_distance, damerau_levenshtein_distance, hamming_distance, jaro_similarity, jaro_winkler_similarity
import sys
import platform
import multiprocessing
import re

import pandas as pd
import numpy as np
from pandas.api.types import is_list_like
from math import trunc
from scipy.stats import chisquare


__all__ = ['entropy', 'entropy_per_byte', 'promptCreds', 'edit_distance']

def entropy(string):
    '''
    Calculates the Shannon entropy of a string.

    string: A string for which to compute the entropy.
    '''
    # get probability of chars in string
    prob = [ string.count(c) / len(string) for c in dict.fromkeys(list(string)) ]
    # calculate the entropy
    entropy = - sum([ p * math.log(p) / math.log(2.0) for p in prob ])
    return entropy

def entropy_per_byte(string):
    '''
    Calculates the Shannon entropy of a string, divided by the total bytes
    in the string.  This is an attempt to normalize entropy values between
    strings of different lengths.

    string: A string for which to compute the entropy per byte
    '''
    e = entropy(string)
    return e / len(string)

def promptCreds(uprompt="Username: ", pprompt="Password: "):
    '''
    Prompt the user for login credentials for some service.  This is a
    helpful convenience when using things like Jupyter notebook, where it
    may not always be obvious how to collect input from the user. The function
    returns a (username, password) tuple.

    uprompt: A string containing the username prompt. Default is "Username: ".
    pprompt: A string containing the password prompt. Default is "Password: ".
    '''
    u = input(uprompt)
    p = getpass.getpass(pprompt)
    return (u,p)

def edit_distance(str1, str2, method="damerau-levenshtein"):
    '''
    Calculate the edit distance between 'str1' and 'str2' using any of a
    number of algorithms.

    'str1', 'str2': Input strings
    'method': The algorithm to use.

    Available algorithms:
        * levenshtein
        * damerau-levenshtein (DEFAULT)
        * hamming
        * jaro
        * jaro-winkler

    Return values:
        "levenshtein", "damerau-levenshtein" and "hamming" return integers
        "jaro" and "jaro-winkler" return floats in the range of 0.0 (completely
        different) to 1.0 (identical strings).
    '''
    algos = {
        "levenshtein":levenshtein_distance,
        "damerau-levenshtein":damerau_levenshtein_distance,
        "hamming":hamming_distance,
        "jaro":jaro_similarity,
        "jaro-winkler":jaro_winkler_similarity
    }

    if not method in list(algos.keys()):
        raise ValueError("Unsupported algorithm type: %s" % method)

    if str1 is None or str2 is None or not isinstance(str1, str) or not isinstance(str2, str):
        raise TypeError("Arguments must be strings.")

    distance_function = algos[method]

    # All the jellyfish distance functions expect unicode, which is the default
    # for Python3.  If we're running in Python2, we need to convert them.
    python_version = sys.version_info
    if python_version.major == 2:
        str1 = unicode(str1)
        str2 = unicode(str2)

    return distance_function(str1, str2)

def benfords(numbers):
    '''
    Examine the distribution of the first digits in a given corpus of numbers to see
    if they correspond to Benford's Law using a chi square test.

    Benford's Law, also known as the "first digit law" or the "law of anomalous numbers"
    states that there is a specific distribution pattern of the first digits of certain 
    groups of numbers.  See https://en.wikipedia.org/wiki/Benford%27s_law for more 
    info.

    :param numbers: The set of numbers to check against Benford's Law
    :type numbers: A list-like object (list, tuple, set, Pandas DataFrame or Series) 
                  containing floats or integers

    :Return Value:

    The function returns three values in a tuple (chi2, p, counts):

      * The 'chi2' value is a float in the range 0..1 that describes how well the observed 
        distribution of first digits matched the predictions of Benford's Law.  Lower is 
        better.  
      * The 'p' value is the probability that the computed 'chi2' is significant (i.e., it 
        tells you whether the chi2 value can be trusted).  Its range is also 0..1, but in 
        this case, higher is better.  Generally speaking, if the p-value is >= 0.95 then 
        the chi2 value is considered significant.
      * 'counts' is a Pandas series where the indices are the possible first digits 1-9 and
        the values are the observed distributions of those digits. If the observed distributions
        didn't match up with Benford's law, the counts may help you identify the anomalous values.

    '''

    def _first_digit(i: float):
        while i >= 10:
            i //= 10
        return trunc(i)

    _BENFORDS = [
        0.301,  # 1
        0.176,  # 2
        0.125,  # 3
        0.097,  # 4
        0.079,  # 5
        0.067,  # 6
        0.058,  # 7
        0.051,  # 8
        0.046  # 9
    ]

    if not is_list_like(numbers):
        raise TypeError(f'The argument must be a list or list-like of numbers, not type {type(numbers)}.')
    if isinstance(numbers, pd.core.series.Series):
        numbers = numbers.values

    numbers = pd.DataFrame(numbers, columns=['numbers'])
    numbers['digits'] = numbers['numbers'].apply(_first_digit)

    counts = numbers['digits'].value_counts()

    # No leading zeroes!
    if 0 in counts.index:
        counts = counts.drop(0)

    # Ensure every digit 1-9 has an count, even if it's 0
    for i in range(1, 10):
        if not i in counts:
            counts[i] = 0

    # Sort by index just to be extra sure they are all in the correct
    # order
    counts = counts.sort_index()

    # Compute the actual distribution of first digits in the input
    # as a proportion of that count to the entire number of samples
    num_samples = counts.sum()
    counts = counts.apply(lambda x: x/num_samples)

    # Compare the actual distribution to Benford's Law
    chi2, p = chisquare(counts.values, _BENFORDS)

    # Return the results of the comparison, plus the observed counts
    return chi2, p, counts

# First time initialization on import

# Set Mac OS systems to use the older "fork" method of spawning 
# procs for the multiprocessing module.  For some reason the newer
# methods don't work (EOFErrors when creating Manager() objects)
system_type = platform.system()
if system_type == "Darwin":
    multiprocessing.set_start_method('fork')

def punctuation_pattern(strings, escape_quotes=False):
    '''
    Return only the non-alphanumeric characters in the input string(s).  
    White spaces in the input will be translated into underscore characters
    in the output. 

    :param strings: The input string(s) to process.
    :type strings: A single string or a list-like object of strings (e.g. a pandas Series)

    :Return Value:
    If the input is a single string, the output will also be a single string.  Otherwise
    the output will be a pandas Series of results in the same order as the input strings.
    '''

    def _get_punct_pattern(s: str) -> str:

        res = re.sub(
            '\s',
            '_',
            re.sub(
                '[a-zA-Z0-9]',
                '',
                s
            )
        )

        if escape_quotes:
            res = re.sub(
                '([\'\"])',
                r'\\\1',
                res
            )

        return res 

    if isinstance(strings, str):
        strings = [strings]
    elif not is_list_like(strings):
        raise TypeError(f'The argument must be a string or list-like of strings, not type {type(strings)}.')

    strings = pd.DataFrame(strings, columns=['strings'])
    strings['punct'] = strings['strings'].apply(_get_punct_pattern)

    res = strings['punct']
    
    # If there's only one result, it was because we passed a single string,
    # just return a single result. Otherwise return all results.
    return res[0] if res.shape[0] == 1 else res 

