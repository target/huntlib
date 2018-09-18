"""
Miscellaneous functions useful for Threat Hunting and cybersecurity data analytics
"""
from __future__ import division

from builtins import input
import getpass
import math

__all__ = ['elastic', 'splunk', 'entropy', 'entropy_per_byte', 'promptCreds']

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
