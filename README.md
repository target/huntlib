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
* **data.flatten()**: Recursively flatten dicts/lists into a single level dict. Useful for data normalization and creating DataFrames.
* **data.chunk()**: Break up a large list into smaller chunks for processing.
* **util.entropy()** / **util.entropy_per_byte()**: Calculate Shannon entropy
* **util.promptCreds()**: Prompt for login credentials in the terminal or from within a Jupyter notebook.
* **util.edit_distance()**: Calculate how "different" two strings are from each other.
* **util.benfords()**: Determine whether a given collection of numbers obeys Benford's Law.
* **util.punctuation_pattern()**: Return only the non-alphanumeric characters from a given string or collection of strings.

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

If you prefer, you use a Splunk session token in place of a username/password (ask your Splunk administator to create one for you):

````python
s = SplunkDF(
    host=splunk_server,
    token="<your token>"
)
````

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

See what DomainTools' IRIS database has to say about a certain domain. This typically provides quick info from a variety of DomainTools sources:

    dt.iris_enrich('google.com')

Enrich a pandas DataFrame containing a mixture of domains and/or IP address in a column called 'iocs'.  It calls `DomainTools.iris_enrich()` to gather the data, and tries to be efficient by handling duplicate values and by sending multiple queries in the same batch:

    df = dt.enrich(df, column='iocs')

The default is to send batches of 100 domains at a time, but you can decrease this number if necessary (usually because the query string becomes so long the DomainTools API server rejects it):

    df = dt.enrich(df, column='iocs', batch_size=75)

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

The `huntlib.data` module contains functions that make it easier to deal with data and data files.  

### Reading Multiple Data Files

`huntlib.data` provides two convenience functions to replace the standard Pandas `read_json()` and `read_csv()` functions.  These replacement functions work exaclty the same as their originals, and take all the same arguments.  The only difference is that they are capable of accepting a filename wildcard in addition to the name of a single file.  All files matching the wildcard expression will be read and returned as a single `DataFrame`.

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
#### Post-Processing the Input Data
Both `read_json()` and `read_csv()` support an optional `post_function` parameter, which allows you to specify a function to post-process the data after each individual file is read in, before it is merged into the final returned DataFrame. For example, you might want to split or combine columns, or compute a new value from existing data.  

Start by creating a post-processing function according to the following prototype:

```python
def my_post_processor(df, filename):
    # do some stuff 

    return df
```

When called, the `df` parameter will be a DataFrame containing the chunk of data just read, and the `filename` parameter will be the name of the file it came from, which will be different for each chunk. **IT IS IMPORTANT THAT YOU RETURN `df` no matter whether you modified the input DataFrame or not.**

Once you have defined the post-processor function, you can invoke it during your call to `read_json()` or `read_csv()` like so:

```python
df = read_csv("*.csv", post_function=my_post_processor)
```

#### Additional Read Options
Consult the Pandas documentation for information on other supported options for `read_csv()` and `read_json()`.

### Normalizing nesting dicts and lists

Many times the data that we deal with is not well formatted for our purposes because it contains complex data structures inside itself and we need it to be more regular (e.g., when converting REST API data in JSON format to a pandas DataFrame).  The `huntlib.data.flatten()` function may be just what you need!

Given a dict or list that may itself contain other dicts or lists, `flatten()` will traverse the object recursively and bring all the data into a single dict with a single level of keys (making it 'flat').

Flattening a dict with nested dicts:

    >>> flatten({"key1": "val1", "subkeys": {"subkey1": "subval1"}})
    {'key1': 'val1', 'subkeys.subkey1': 'subval1'}

Flatten a list with nested lists.  Notice that the resulting keys are the list indices in string form:

    >>> flatten([1, 2, 3])
    {'0': 1, '1': 2, '2': 3}

A more complex example:

    >>> flatten([{'a': 'a', 'b': 'b'}, {'a': 'a1', 'c': 'c'}])
    {'0.a': 'a', '0.b': 'b', '1.a': 'a1', '1.c': 'c'}

### Breaking a long list-like object into smaller chunks
Given a list-like object, divide into chunks of `size` and return those as a generator. If the length of the sequence is not evenly divisible by the size, the final chunk will contain however many items remain.

    >>> l = list(range(26))
    >>> for i in chunk(l, size=5):
    ...   print(i)
    [0, 1, 2, 3, 4]
    [5, 6, 7, 8, 9] 
    [10, 11, 12, 13, 14]
    [15, 16, 17, 18, 19]
    [20, 21, 22, 23, 24]
    [25]

## Util Module 

The `huntlib.util` modules contains miscellaneous functions that don't fit anywhere else, but are nevertheless still useful.

### Entropy

`huntlib.util` provides two entropy functions, `entropy()` and `entropy_per_byte()`. Both accept a single string as a parameter.  The `entropy()` function calculates the Shannon entropy of the given string, while `entropy_per_byte()` attempts to normalize across strings of various lengths by returning the Shannon entropy divided by the length of the string.  Both return values are `float`.

```python
>>> entropy("The quick brown fox jumped over the lazy dog.")
4.425186429663008
>>> entropy_per_byte("The quick brown fox jumped over the lazy dog.")
0.09833747621473352
```

The higher the value, the more data potentially embedded in it.

### Credential Handling

Sometimes you need to provide credentials for a service, but don't want to hard-code them into your scripts, especially if you're collaborating on a hunt.  `huntlib.util` provides the `promptCreds()` function to help with this. This function works well both in the terminal and when called from within a Jupyter notebook.

Call it like so:

```python
(username, password) = promptCreds()
```

You can change one or both of the username/password prompts by passing arguments:

```python
(username, password) = promptCreds(
                            uprompt="LAN ID: ",
                            pprompt="LAN Pass: "
                        )
```

### String Similarity

String similarity can be expressed in terms of "edit distance", or the number of single-character edits necessary to turn the first string into the second string.  This is often useful when, for example, you want to find two strings that very similar but not identical (such as when hunting for [process impersonation](http://detect-respond.blogspot.com/2016/11/hunting-for-malware-critical-process.html)).

There are a number of different ways to compute similarity. `huntlib.util` provides the `edit_distance()` function for this, which supports several algorithms:

* [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance)
* [Damerau-Levenshtein Distance](https://en.wikipedia.org/wiki/Damerau%E2%80%93Levenshtein_distance)
* [Hamming Distance](https://en.wikipedia.org/wiki/Hamming_distance)
* [Jaro Distance](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance)
* [Jaro-Winkler Distance](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance)

Here's an example:

```python
>>> edit_distance('svchost', 'scvhost')
1
```

You can specify a different algorithm using the `method` parameter. Valid methods are `levenshtein`, `damerau-levenshtein`, `hamming`, `jaro` and `jaro-winkler`. The default is `damerau-levenshtein`.

```python
>>> edit_distance('svchost', 'scvhost', method='levenshtein')
2
```

### Benford's Law
Benford's Law, also known as the "first digit law" or the "law of anomalous numbers" states that there is a specific distribution pattern of the first digits of certain groups of numbers.  It is often used to detect cheating or tampering in areas such as tax fraud and vote rigging.  

See https://en.wikipedia.org/wiki/Benford%27s_law for more info on Benford's Law and it's potential applications.

The `benfords()` function returns a 3-tuple of values like: `(chi2, p, counts)`.

* `chi2` is a float that describes how well the observed distribution of first digits matched the predictions of Benford's Law.  Lower is better.  
* `p` is the probability that the computed 'chi2' is significant (i.e., it tells you whether the chi2 value can be trusted).  Its range is 0..1, but in this case, higher is better.  Generally speaking, if the p-value is >= 0.95 then the chi2 value is considered significant.
* `counts` is a Pandas series where the indices are the possible first digits 1-9 and the values are the observed distributions of those digits. If the observed distributions didn't match up with Benford's law, the counts may help you identify the anomalous values.

Here's an example of calling the `benfords()` function, with a contrived set of numbers that definitely conform to the expected distribution:

```python
>>> numbers = [1, 1, 1, 1, 1, 1, 1, 1, 
               2, 2, 2, 2,
               3, 3, 3, 
               4, 4, 
               5, 5, 
               6, 6, 
               7, 7, 
               8, 
               9]
>>> benfords(numbers)
(0.019868294035033682, 0.9999999995974126, 1    0.32
2    0.16
3    0.12
4    0.08
5    0.08
6    0.08
7    0.08
8    0.04
9    0.04
Name: digits, dtype: float64)
```

Notice the `chi2` value is quite low (~0.02), meaning these numbers follow Benford's Law quite well.  The `p` value is > 0.999999999 so we can have a high confidence in these results.

Here the input is a set of random numbers, which do not conform to Benford's Law.  Notice the `chi2` value is much higher, but the `p` value is still > 0.9999, indicating that we can trust the fact that it doesn't conform.
```python
>>> numbers = np.random.randint(1, 10, 1000)
>>> benfords(numbers)
(0.391706824115063, 0.9999475565204166, 1    0.114
2    0.119
3    0.118
4    0.099
5    0.110
6    0.116
7    0.120
8    0.083
9    0.121
Name: digits, dtype: float64)
```

### Generate punctuation patterns from strings

For certain types of log analysis, the contents of the individual log messages is not as important as the format of the message itself. This often results in the need to examine the pattern of punctuation (non-alphanumeric characters). To facilitate this, the `punctuation_pattern()` function accepts a single string or a list-like collection of strings and returns *just* the non-alphanumeric characters.

```python
>>> >>> s = '192.168.1.1 - - [10/Oct/2020:12:32:27 +0000] "GET /some/web/app?param=test&param2=another_test" 200 9987'
>>> punctuation_pattern(s)
'..._-_-_[//:::_+]_"_///?=&=_"__'

>>> l = [s, "Another example. This time, of a list of strings!"]
>>> punctuation_pattern(l)
0    ..._-_-_[//:::_+]_"_///?=&=_"__
1                        _.__,_____!
Name: punct, dtype: object
```
