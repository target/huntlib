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



# First time initialization on import

# Set Mac OS systems to use the older "fork" method of spawning 
# procs for the multiprocessing module.  For some reason the newer
# methods don't work (EOFErrors when creating Manager() objects)
system_type = platform.system()
if system_type == "Darwin":
    multiprocessing.set_start_method('fork')
