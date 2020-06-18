from huntlib.exceptions import AuthenticationErrorSearchException, InvalidRequestSearchException, UnknownSearchException
from builtins import object
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import elasticsearch.exceptions
import pandas as pd
from datetime import datetime, timedelta

class ElasticDF(object):
    '''
    The ElasticDF() class searches Elastic and returns results as a Pandas
    DataFrame.  This makes it easier to work with the search results with
    standard data analysis techniques.

    Example usage:

        # Create a plaintext connection to the Elastic server, no authentication
        e = ElasticDF(url="http://localhost:9200")

        # The same, but with SSL and authentication
        e = ElasticDF(url="https://localhost:9200", ssl=True, username="myuser",
                      password="mypass")

        # Fetch search results from an index or index pattern for the previous day
        df = e.search_df(lucene="item:5282 AND color:red", index="myindex-*", days=1)

        # The same, but do not flatten structures into individual columns.
        # This will result in each structure having a single column with a
        # JSON string describing the structure.
        df = e.search_df(lucene="item:5282 AND color:red", index="myindex-*", days=1,
                         normalize=False)

        # A more complex example, showing how to set the Elastic document type,
        # use Python-style datetime objects to constrain the search to a certain
        # time period, and a user-defined field against which to do the time
        # comparisons.
        df = e.search_df(lucene="item:5285 AND color:red", index="myindex-*",
                         doctype="doc", date_field="mydate",
                         start_time=datetime.now() - timedelta(days=8),
                         end_time=datetime.now() - timedelta(days=6))

    The search() and search_df() methods will raise
    InvalidRequestSearchException() in the event that the search request is
    syntactically correct but is otherwise invalid. For example, if you request
    more results be returned than the server is able to provide.
    They will raise AuthenticationErrorSearchException() in the event the server 
    denied the credentials during login.  They can also raise an
    UnknownSearchException() for other situations, in which case the exception
    message will contain the original error message returned by Elastic so you
    can figure out what went wrong.
    '''

    es_conn = None # The connection to the ES server

    def __init__(self, url=None, timeout=250, ssl=False, username="", password="", verify_certs=True, ca_certs=None):
        '''
        Create the ElasticDF object and log into the Elastic server.
        '''

        self.es_conn = Elasticsearch(
            url,
            timeout=timeout,
            use_ssl=ssl,
            verify_certs=verify_certs,
            ca_certs=ca_certs,
            http_auth=(username, password)
        )

    def search(self, lucene, index="*", doctype="doc", fields=None,
               date_field="@timestamp", days=None, start_time=None,
               end_time=None, limit=None):
        '''
        Search Elastic and return the results as a list of dicts.

        lucene: A string containing the Elastic search (e.g., 'item:5282 AND color:red')
        index: A string containing the index name to search, or an index name pattern
               if you want to search multiple indices (e.g., 'myindex' or 'myindex-*')
        doctype: The document type you are interested in.
        fields: A string containing a comma-separated list of field names to return.
                The default is to return all fields, but using this list you can
                select only certain fields, which may make things a bit faster.
        date_field: The name of the field used for date/time comparison.
        days: Search the past X days. If provided, this supercedes both start_time
              and end_time.
        start_time: A datetime() object representing the start of the search
                    window. If used without end_time, the end of the search
                    window is the current time.
        end_time: A datetime() object representing the end of the search window.
                  If used without start_time, the search start will be the earliest
                  time in the index.
        limit: An integer describing the max number of search results to return.
        '''

        s = Search(using=self.es_conn, index=index, doc_type=doctype)

        s = s.query("query_string", query=lucene)

        if fields:
            s = s.source(fields.split(','))

        # Add timestamp filters, if provided.  Days takes precendence over
        # use of either/both of start_time and end_time.
        # Note the weird unpacked dictionary syntax in the call to s.filter().
        # We have to do it this way because Python has an issue naming things
        # with "@" in them, but the default timestamp field in many ES servers is
        # "@timestamp".
        # ref:  https://github.com/elastic/elasticsearch-dsl-py/blob/master/docs/search_dsl.rst
        if days:
            end = datetime.now()
            start = end - timedelta(days=days)
            s = s.filter('range', ** {date_field: {"gte": start, "lte": end}})
        elif start_time and not end_time:
            s = s.filter('range', ** {date_field: {"gte": start_time}})
        elif end_time and not start_time:
            s = s.filter('range', ** {date_field: {"lte": end_time}})
        elif start_time and end_time:
            s = s.filter('range', ** {date_field: {"gte": start_time, "lte": end_time}})

        # Add a search limit, if one is specified. Note that this is per-shard,
        # not total results.  Since this is where the search actually runs (the
        # call to excute() does this) then we also have to handle authentication
        # issues.
        try:
            if limit:
                s = s.params(size=limit)
                response = s.execute()
            else:
                # Scan to explicitly return all results
                response = s.execute()
                s = s.scan()
        except elasticsearch.exceptions.AuthenticationException:
            raise AuthenticationErrorSearchException("Login failed.")

        if response.success():
            for hit in s:
                yield hit.to_dict()
        else:
            reason = response._shards.failures[0].reason
            if "Result window is too large" in reason['reason']:
                raise InvalidRequestSearchException("Too many results requested (more than index.max_result_window settings on the index). Either reduce the result limit or remove the limit paramter entirely.")
            else:
                raise UnknownSearchException("Message from Elastic was: %s" % reason['reason'])

    def search_df(self, lucene, index="*", doctype="doc", fields=None,
                  date_field="@timestamp", days=None, start_time=None,
                  end_time=None, normalize=True, limit=None):
        '''
        Search Elastic and return the results as a Pandas DataFrame.

        lucene: A string containing the Elastic search (e.g., 'item:5282 AND color:red')
        index: A string containing the index name to search, or an index name pattern
               if you want to search multiple indices (e.g., 'myindex' or 'myindex-*')
        doctype: The document type you are interested in.
        fields: A string containing a comma-separated list of field names to return.
                The default is to return all fields, but using this list you can
                select only certain fields, which may make things a bit faster.
        date_field: The name of the field used for date/time comparison.
        days: Search the past X days. If provided, this supercedes both start_time
              and end_time.
        start_time: A datetime() object representing the start of the search
                    window. If used without end_time, the end of the search
                    window is the current time.
        end_time: A datetime() object representing the end of the search window.
                  If used without start_time, the search start will be the earliest
                  time in the index.
        normalize: If set to True, fields containing structures (i.e. subfields)
                   will be flattened such that each field has it's own column in
                   the dataframe. If False, there will be a single column for the
                   structure, with a JSON string encoding all the contents.
        limit: An integer describing the max number of search results to return.
        '''
        results = list()

        for hit in self.search(lucene=lucene, index=index, doctype=doctype,
                               fields=fields, date_field=date_field, days=days,
                               start_time=start_time, end_time=end_time,
                               limit=limit):
            results.append(hit)

        if normalize:
            df = pd.json_normalize(results)
        else:
            df = pd.DataFrame(results)

        return df
