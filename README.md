# HuntLib
A Python library to help with some common threat hunting data analysis operations

[![Target’s CFC-Open-Source Slack](https://cfc-slack-inv.herokuapp.com/badge.svg?colorA=155799&colorB=159953)](https://cfc-slack-inv.herokuapp.com/)

## What's Here?
The `huntlib` module provides three major object classes as well as a few convenience functions.  

* **ElasticDF**: Search Elastic and return results as a Pandas DataFrame
* **SplunkDF**: Search Splunk and return results as a Pandas DataFrame
* **DomainTools**: Convenience functions for accessing the DomainTools API, primarily focused around data enrichment (requires a DomainTools API subscription)
* **data.read_json()**: Read one or more JSON files and return a single Pandas DataFrame
* **data.read_csv()**: Read one or more CSV files and return a single Pandas DataFrame
* **entropy()** / **entropy_per_byte()**: Calculate Shannon entropy
* **promptCreds()**: Prompt for login credentials in the terminal or from within a Jupyter notebook.
* **edit_distance()**: Calculate how "different" two strings are from each other

## Library-Wide Configuration
Beginning with `v0.5.0`, `huntlib` now provides a library-wide configuration file, `~/.huntlibrc` allowing you to set certain runtime defaults.  Consult the file `huntlibrc-sample` in this repo for more information.

## huntlib.elastic.ElasticDF
The `ElasticDF()` class searches Elastic and returns results as a Pandas DataFrame.  This makes it easier to work with the search results using standard data analysis techniques.

### Example usage:

Create a plaintext connection to the Elastic server, no authentication

```python
e = ElasticDF(
                url="http://localhost:9200"
)
```

The same, but with SSL and authentication

```python
e = ElasticDF(
                url="https://localhost:9200",
                ssl=True,
                username="myuser",
                password="mypass"
)
```
Fetch search results from an index or index pattern for the previous day

```python
df = e.search_df(
                  lucene="item:5282 AND color:red",
                  index="myindex-*",
                  days=1
)
```

The same, but do not flatten structures into individual columns. This will result in each structure having a single column with a JSON string describing the structure.

```python
df = e.search_df(
                  lucene="item:5282 AND color:red",
                  index="myindex-*",
                  days=1,
                  normalize=False
)
```

A more complex example, showing how to set the Elastic document type, use Python-style datetime objects to constrain the search to a certain time period, and a user-defined field against which to do the time comparisons. The result size will be limited to no more than 1500 entries.

```python
df = e.search_df(
                  lucene="item:5285 AND color:red",
                  index="myindex-*",
                  doctype="doc", date_field="mydate",
                  start_time=datetime.now() - timedelta(days=8),
                  end_time=datetime.now() - timedelta(days=6),
                  limit=1500
)
```

The `search` and `search_df` methods will raise `InvalidRequestSearchException`
in the event that the search request is syntactically correct but is otherwise
invalid. For example, if you request more results be returned than the server
is able to provide. They will raise `AuthenticationErrorSearchException` in the
event the server denied the credentials during login.  They can also raise an
`UnknownSearchException` for other situations, in which case the exception
message will contain the original error message returned by Elastic so you
can figure out what went wrong.

## huntlib.splunk.SplunkDF

The `SplunkDF` class search Splunk and returns the results as a Pandas DataFrame. This makes it easier to work with the search results using standard data analysis techniques.

### Example Usage

Establish an connection to the Splunk server. Whether this is SSL/TLS or not depends on the server, and you don't really get a say.

```python
s = SplunkDF(
              host=splunk_server,
              username="myuser",
              password="mypass"
)
```

`SplunkDF` will raise `AuthenticationErrorSearchException` during initialization
in the event the server denied the supplied credentials.  

Fetch all search results across all time

```python
df = s.search_df(
                  spl="search index=win_events EventCode=4688"
)
```

Fetch only specific fields, still across all time

```python
df = s.search_df(
                  spl="search index=win_events EventCode=4688 | table ComputerName _time New_Process_Name Account_Name Creator_Process_ID New_Process_ID Process_Command_Line"
)
```

Time bounded search, 2 days prior to now

```python
df = s.search_df(
                  spl="search index=win_events EventCode=4688",
                  days=2
)
```

Time bounded search using Python datetime() values

```python
df = s.search_df(
                  spl="search index=win_events EventCode=4688",
                  start_time=datetime.now() - timedelta(days=2),
                  end_time=datetime.now()
)
```

Time bounded search using Splunk notation

```python
df = s.search_df(
                  spl="search index=win_events EventCode=4688",
                  start_time="-2d@d",
                  end_time="@d"
)
```

Limit the number of results returned to no more than 1500

```python
df = s.search_df(
                  spl="search index=win_events EventCode=4688",
                  limit=1500
)
```

*NOTE: The value specified as the `limit` is also subject to a server-side max
value. By default, this is 50000 and can be changed by editing limits.conf on
the Splunk server. If you use the limit parameter, the number of search results
you receive will be the lesser of the following values: 1) the actual number of
results available, 2) the number you asked for with `limit`, 3) the server-side
maximum result size.  If you omit limit altogether, you will get the **true**
number of search results available without subject to additional limits, though
your search may take much longer to complete.*

Return only specified fields `NewProcessName` and `SubjectUserName`

```python
df = s.search_df(
                  spl="search index=win_events EventCode=4688",
                  fields="NewProcessName,SubjectUserName"
)
```

*NOTE: By default, Splunk will only return the fields you reference in the
search string (i.e. you must explicitly search on "NewProcessName" if you want
that field in the results. Usually this is not what we want. When fields is not `None`, 
the query string will be rewritten with "| fields <fields>" at the end (e.g., 
`search index=win_events EventCode=4688 | fields NewProcessName,SubjectUserName`). This
works fine for most simple cases, but if you have a more complex SPL query and it breaks, 
simply set `fields=None` in your function call to avoid this behavior.*

Try to remove Splunk's "internal" fields from search results:

```python
df = s.search_df(
    spl="search index=win_events EventCode=4688",
    internal_fields=False
)
``` 
This will remove such fields as `_time` and `_sourcetype` as well as any other field who's name begins with `_`.  This behavior occurs by default (`internal_fields` defaults to `False`), but you can disable it by using `internal_fields=True`.  

Remove named field(s) from the search results:

```python
df = s.search_df(
    spl="search index=win_events EventCode=4688",   internal_fields="_bkt,_cd,_indextime,_raw,_serial,_si,_sourcetype,_subsecond,_time"
)
```
In the event you need more control over which "internal" fields to drop, you can pass a comma-separated list of field names (NOTE: these can be any field, not just Splunk internal fields).

Splunk's Python API can be quite slow, so to speed things up you may elect to spread the result retrieval among multiple cores.  The default is to use one (1) extra core, but you can use the `processes` argument to `search()` or `search_df()` to set this higher if you like.  

```python
df = s.search_df(
    spl="search index=win_events EventCode=4688", 
    processes=4
)
```

If you prefer to use all your cores, try something like:

```python
from multiprocessing import cpu_count

df = s.search_df(
    spl="search index=win_events EventCode=4688",
    processes=cpu_count()
)
```

*NOTE: You may have to experiment to find the optimal number of parallel processes for your specific environment. Maxing out the number of workers doesn't always give the best performance.*

## huntlib.domaintools.DomainTools
The `DomainTools` class allows you to easily perform some common types of calls
to the DomainTools API.  It uses their official `domaintools_api` Python module
to do most of the work but is not a complete replacement for that module. In
particular, this class concentrates on a few calls that are most relevant for
data analytic style threat hunting (risk & reputation scores, WHOIS info, etc).

The `DomainTools` class can make use of the global config file `~/.huntlibrc` to store the API username and secret key, if desired.  See the `huntlibrc-sample` file for more info.

### Example Usage

Import the `DomainTools` object:

    from huntlib.domaintools import DomainTools

Instantiate a new `DomainTools` object:

    dt = DomainTools(
        api_username="myuser,
        api_key="mysecretkey
    )

Instatiate a new `DomainTools` object using default creds stored in `~/.huntlibrc`:

    dt = DomainTools()

Look up API call limits and usage info for the authenticated user:

    dt.account_information()

Return the list of API calls to which the authenticated user has access:

    dt.available_api_calls()

Return basic WHOIS info for a domain or IP address:

    dt.whois('google.com')
    dt.whois('8.8.8.8')

Return WHOIS info with additional fields parsed from the text part of the record:

    dt.parsed_whois('google.com')
    dt.parsed_whois('8.8.8.8')

Find newly-activated or pending domain registrations matching all the supplied search terms:

    dt.brand_monitor('myterm')
    dt.brand_monitor('myterm1|myterm2|myterm3') # terms are ANDed together

Look up basic info about a domain's DNS, WHOIS, hosting and web site in one query.

    dt.domain_profile('google.com')

Return a list of risk scores for a domain, according to different risk factors:

    dt.risk('google.com')

Return a single consolidated risk score for a domain:

    dt.domain_reputation('google.com')

Enrich a pandas DataFrame containing a mixture of domains and/or IP address in a column called 'iocs':

    df = dt.enrich(df, column='iocs')

Enrichment tends to add a large number of columns, which you may not need. Use the `fields` parameter if you know exactly what you want:

    df = dt.enrich(
        df, 
        column='iocs', 
        fields=[
            'dt_whois.registration.created',
            'dt_reputation.risk_score'
        ]
    )

Enrichment may take quite some time with a large dataset. If you're antsy, try turning on the progress bars:

    df = dt.enrich(df, column='iocs', progress_bar=True)

## Data Module

The `huntlib.data` module contains functions that make it easier to deal with data files.  

### Reading Multiple Data Files

`huntlib` provides two convenience functions to replace the standard Pandas `read_json()` and `read_csv()` functions.  These replacement functions work exaclty the same as their originals, and take all the same arguments.  The only difference is that they are capable of accepting a filename wildcard in addition to the name of a single file.  All files matching the wildcard expression will be read and returned as a single `DataFrame`.

Start by importing the functions from the module:

```python
from huntlib.data import read_csv, read_json
```

Here's an example of reading a single JSON file, where each line is a separate JSON document:

```python
df = read_json("data.json", lines=True)
```

Similarly, this will read all JSON files in the current directory:

```python
df = read_json("*.json", lines=True)
```

The `read_csv` function works the same way:

```python
df = read_csv("data.csv)
```

or 

```python
df = read_csv("*.csv")
```

Consult the Pandas documentation for information on supported options for `read_csv()` and `read_json()`.

## Miscellaneous Functions

### Entropy

We define two entropy functions, `entropy()` and `entropy_per_byte()`. Both accept a single string as a parameter.  The `entropy()` function calculates the Shannon entropy of the given string, while `entropy_per_byte()` attempts to normalize across strings of various lengths by returning the Shannon entropy divided by the length of the string.  Both return values are `float`.

```python
>>> entropy("The quick brown fox jumped over the lazy dog.")
4.425186429663008
>>> entropy_per_byte("The quick brown fox jumped over the lazy dog.")
0.09833747621473352
```

The higher the value, the more data potentially embedded in it.

### Credential Handling

Sometimes you need to provide credentials for a service, but don't want to hard-code them into your scripts, especially if you're collaborating on a hunt.  `huntlib` provides the `promptCreds()` function to help with this. This function works well both in the terminal and when called from within a Jupyter notebook.

Call it like so:

```python
(username, password) = promptCreds()
```

You can change one or both of the username/password prompts by passing arguments:

```python
(username, password) = promptCreds(uprompt="LAN ID: ",
                                   pprompt="LAN Pass: ")
```

### String Similarity

String similarity can be expressed in terms of "edit distance", or the number of single-character edits necessary to turn the first string into the second string.  This is often useful when, for example, you want to find two strings that very similar but not identical (such as when hunting for [process impersonation](http://detect-respond.blogspot.com/2016/11/hunting-for-malware-critical-process.html)).

There are a number of different ways to compute similarity. `huntlib` provides the `edit_distance()` function for this, which supports several algorithms:

* [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance)
* [Damerau-Levenshtein Distance](https://en.wikipedia.org/wiki/Damerau%E2%80%93Levenshtein_distance)
* [Hamming Distance](https://en.wikipedia.org/wiki/Hamming_distance)
* [Jaro Distance](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance)
* [Jaro-Winkler Distance](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance)

Here's an example:

```python
>>> huntlib.edit_distance('svchost', 'scvhost')
1
```

You can specify a different algorithm using the `method` parameter. Valid methods are `levenshtein`, `damerau-levenshtein`, `hamming`, `jaro` and `jaro-winkler`. The default is `damerau-levenshtein`.

```python
>>> huntlib.edit_distance('svchost', 'scvhost', method='levenshtein')
2
```
