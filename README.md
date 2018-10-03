# HuntLib
A Python library to help with some common threat hunting data analysis operations

[![Target’s CFC-Open-Source Slack](https://cfc-slack-inv.herokuapp.com/badge.svg?colorA=155799&colorB=159953)](https://cfc-slack-inv.herokuapp.com/)

## What's Here?
The `huntlib` module provides two major object classes as well as a few convenience functions.  

* **ElasticDF**: Search Elastic and return results as a Pandas DataFrame
* **SplunkDF**: Search Splunk and return results as a Pandas DataFrame
* **entropy()** / **entropy_per_byte()**: Calculate Shannon entropy
* **promptCreds()**: Prompt for login credentials in the terminal or from within a Jupyter notebook.
* **edit_distance()**: Calculate how "different" two strings are from each other

## huntlib.elastic.ElasticDF
The `ElasticDF()` class searches Elastic and returns results as a Pandas DataFrame.  This makes it easier to work with the search results using standard data analysis techniques.

### Example usage:

Create a plaintext connection to the Elastic server, no authentication

    e = ElasticDF(url="http://localhost:9200")

The same, but with SSL and authentication

    e = ElasticDF(url="https://localhost:9200", ssl=True, username="myuser",
                  password="mypass")

Fetch search results from an index or index pattern for the previous day

    df = e.search_df(lucene="item:5282 AND color:red", index="myindex-*", days=1)

The same, but do not flatten structures into individual columns. This will result in each structure having a single column with a JSON string describing the structure.

    df = e.search_df(lucene="item:5282 AND color:red", index="myindex-*", days=1,
                     normalize=False)

A more complex example, showing how to set the Elastic document type, use Python-style datetime objects to constrain the search to a certain time period, and a user-defined field against which to do the time comparisons.

    df = e.search_df(lucene="item:5285 AND color:red", index="myindex-*",
                    doctype="doc", date_field="mydate",
                    start_time=datetime.now() - timedelta(days=8),
                    end_time=datetime.now() - timedelta(days=6))

## huntlib.splunk.SplunkDF

The `SplunkDF` class search Splunk and returns the results as a Pandas DataFrame. This makes it easier to work with the search results using standard data analysis techniques.

### Example Usage

Establish an connection to the Splunk server. Whether this is SSL/TLS or not depends on the server, and you don't really get a say.

    s = SplunkDF(host=splunk_server, username="myuser", password="mypass")

Fetch all search results across all time

    df = s.search(spl="search index=win_events EventCode=4688")

Fetch only specific fields, still across all time

    df = s.search(spl="search index=win_events EventCode=4688 | table ComputerName _time New_Process_Name Account_Name Creator_Process_ID New_Process_ID Process_Command_Line")

Time bounded search, 2 days prior to now

    df = s.search(spl="search index=win_events EventCode=4688", days=2)

Time bounded search using Python datetime() values

    df = s.search(
                    spl="search index=win_events EventCode=4688",
                    start_time=datetime.now() - timedelta(days=2),
                    end_time=datetime.now()
    )

Time bounded search using Splunk notation

    df = s.search(
                    spl="search index=win_events EventCode=4688",
                    start_time="-2d@d",
                    end_time="@d"
    )

## Miscellaneous Functions

### Entropy

We define two entropy functions, `entropy()` and `entropy_per_byte()`. Both accept a single string as a parameter.  The `entropy()` function calculates the Shannon entropy of the given string, while `entropy_per_byte()` attempts to normalize across strings of various lengths by returning the Shannon entropy divided by the length of the string.  Both return values are `float`.

    >>> entropy("The quick brown fox jumped over the lazy dog.")
    4.425186429663008
    >>> entropy_per_byte("The quick brown fox jumped over the lazy dog.")
    0.09833747621473352

The higher the value, the more data potentially embedded in it.

### Credential Handling

Sometimes you need to provide credentials for a service, but don't want to hard-code them into your scripts, especially if you're collaborating on a hunt.  `huntlib` provides the `promptCreds()` function to help with this. This function works well both in the terminal and when called from within a Jupyter notebook.

Call it like so:

    (username, password) = promptCreds()

You can change one or both of the username/password prompts by passing arguments:

    (username, password) = promptCreds(uprompt="LAN ID: ",
                                       pprompt="LAN Pass: ")

### String Similarity

String similarity can be expressed in terms of "edit distance", or the number of single-character edits necessary to turn the first string into the second string.  This is often useful when, for example, you want to find two strings that very similar but not identical (such as when hunting for [process impersonation](http://detect-respond.blogspot.com/2016/11/hunting-for-malware-critical-process.html)).

There are a number of different ways to compute similarity. `huntlib` provides the `edit_distance()` function for this, which supports several algorithms:

* [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance)
* [Damerau-Levenshtein Distance](https://en.wikipedia.org/wiki/Damerau%E2%80%93Levenshtein_distance)
* [Hamming Distance](https://en.wikipedia.org/wiki/Hamming_distance)
* [Jaro Distance](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance)
* [Jaro-Winkler Distance](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance)

Here's an example:

    >>> huntlib.edit_distance('svchost', 'scvhost')
    1

You can specify a different algorithm using the `method` parameter. Valid methods are `levenshtein`, `damerau-levenshtein`, `hamming`, `jaro` and `jaro-winkler`. The default is `damerau-levenshtein`.

    >>> huntlib.edit_distance('svchost', 'scvhost', method='levenshtein')
    2
