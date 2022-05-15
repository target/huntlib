from huntlib.exceptions import AuthenticationErrorSearchException, InvalidRequestSearchException, UnknownSearchException
from builtins import object
from sumologic import SumoLogic
import time
import re
import pandas as pd
from datetime import datetime, timedelta
import os
from configparser import ConfigParser
import sys

class SumologicDF(object):
    '''
    The SumologicDF() class searches Sumologic and returns results as a Pandas
    DataFrame.  This makes it easier to work with the search results with
    standard data analysis techniques.

    Example usage:

        # Create a connection to the Sumologic endpoint and authentication
        # https://help.sumologic.com/APIs/General-API-Information/Sumo-Logic-Endpoints-and-Firewall-Security
        e = SumologicDF(url="https://api.us2.sumologic.com/api/v1", accessid="xyz",
                      accesskey="xxxxx")

        # Fetch search results from an index or index pattern for the previous day
        # https://help.sumologic.com/05Search
        df = e.search_df(query="_index=WINDOWS eventid=5282 color=red", days=1)

        # The same, but do not flatten structures into individual columns.
        # This will result in each structure having a single column with a
        # JSON string describing the structure.
        df = e.search_df(query="_index=WINDOWS eventid=5282 color=red", days=1,
                         normalize=False)

        # A more complex example, showing how to
        # use Python-style datetime objects to constrain the search to a certain
        # time period, specify timezone and if time should used _receiptTime
        # (time when Sumologic got message) instead of _messageTime (time present
        # in log message).
        df = e.search_df(query="_index=WINDOWS eventid=5282 color=red",
                         start_time=datetime.now() - timedelta(days=8),
                         end_time=datetime.now() - timedelta(days=6),
                         timezone='EST',
                         byReceiptTime=True)

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

    sumo_conn = None
    timeout = 5

    _DEFAULT_CONFIG_FILE = os.path.expanduser("~/.huntlibrc")

    def __init__(self, *args, **kwargs):
        '''
        Create the SumologicDF object and log into Sumologic
        '''

        # Read our config file, if it exists
        config = ConfigParser()
        config.read(self._DEFAULT_CONFIG_FILE)

        url = ''
        accessid = ''
        accesskey = ''

        if 'accessid' in kwargs:
            accessid = kwargs['accessid']
        elif config.has_option('sumologic', 'accessid'):
            accessid = config.get('sumologic', 'accessid')

        if 'accesskey' in kwargs:
            accesskey = kwargs['accesskey']
        elif config.has_option('sumologic', 'accesskey'):
            accesskey = config.get('sumologic', 'accesskey')

        if 'url' in kwargs:
            url = kwargs['url']
        elif config.has_option('sumologic', 'url'):
            url = config.get('sumologic', 'url')
        else:
            print("FATAL: missing url!")
            sys.exit(1)

        if 'timeout' in kwargs:
            timeout = kwargs['timeout']
        elif config.has_option('sumologic', 'timeout'):
            timeout = config.get('sumologic', 'timeout')
        else:
            timeout = 250

        # Remove these from kwargs, so we don't have duplicate args.
        kwargs.pop('accessid', None)
        kwargs.pop('accesskey', None)
        kwargs.pop('url', None)
        kwargs.pop('timeout', None)

        # https://github.com/SumoLogic/sumologic-python-sdk/blob/master/scripts/search-job.py
        self.sumo_conn = SumoLogic(
            accessid,
            accesskey,
            url
        )
        print("Connected to Sumologic: url {0} accessid {1}".format(url, accessid))
        self.timeout = timeout

    def search(self, query,
               fields=None,
               days=None, start_time=None,
               end_time=None,
               timeZone='EST',
               byReceiptTime=False,
               limit=10000,
               forceMessagesResults=False,
               verbosity=0):
        '''
        Search Sumologic and return the results as a list of dicts.

        query: A string containing the Sumologic query search (e.g., 'item=5282 color=red')
        fields: A string containing a comma-separated list of field names to return.
                The default is to return all fields, but using this list you can
                select only certain fields, which may make things a bit faster.
        days: Search the past X days. If provided, this supercedes both start_time
              and end_time.
        start_time: A datetime() object representing the start of the search
                    window. If used without end_time, the end of the search
                    window is the current time.
        end_time: A datetime() object representing the end of the search window.
                  If used without start_time, the search start will be the earliest
                  time in the index.
        timeZone: timezone used for time range search
        byReceiptTime:  if time reference should used _receiptTime (time when Sumologic
                        got message) instead of _messageTime (time present in log message).
        limit: An integer describing the max number of search results to return.
        forceMessagesResults: Force results to be raw messages even if aggregated query.
        verbosity: Provide more verbose state. from 0 least verbose to 4 most one.
        '''

        if fields:
            query += "| fields {0}".format(fields)
        if limit:
            query += "| limit {0}".format(limit)

        # Add timestamp filters, if provided.  Days takes precendence over
        # use of either/both of start_time and end_time.
        # Note the weird unpacked dictionary syntax in the call to s.filter().
        # We have to do it this way because Python has an issue naming things
        # with "@" in them, but the default timestamp field in many ES servers is
        # "@timestamp".
        # ref:  https://github.com/elastic/elasticsearch-dsl-py/blob/master/docs/search_dsl.rst
        if days:
            end = datetime.now()
            end_time = end.strftime("%Y-%m-%dT%H:%M:%S")
            start_time = end - timedelta(days=days)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        elif start_time and not end_time:
            end = datetime.now()
            end_time = end.strftime("%Y-%m-%dT%H:%M:%S")
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
            s = s.filter('range', ** {date_field: {"gte": start_time}})
        elif not days and not start_time:
            print("Error! require either days or start_time")
            sys.exit(1)
        elif end_time and start_time:
            end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S")
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        #elif end_time and not start_time:
            # error, should have days or start_time
        #elif start_time and end_time:
            # nothing to do

        if verbosity >=1:
            print("INFO: from {0} to {1}, timezone {2}".format(start_time, end_time, timeZone))
        if verbosity >=2:
            print("DEBUG: query {0}".format(query))
            print("DEBUG: byReceiptTime {0}".format(byReceiptTime))
        try:
            sj = self.sumo_conn.search_job(query, start_time, end_time, timeZone, byReceiptTime)
        except Exception as e:
            print("Exception: Failed to submit search job: {0}".format(e))
            sys.exit(1)
        if verbosity >=2:
            print("DEBUG: search job {0}".format(sj))

        status = self.sumo_conn.search_job_status(sj)
        if verbosity >=2:
            print("DEBUG: status {0}".format(status))
        while status['state'] != 'DONE GATHERING RESULTS':
            if status['state'] == 'CANCELLED':
                break
            time.sleep(self.timeout)
            status = self.sumo_conn.search_job_status(sj)

        print(status['state'])

        if verbosity >=2:
            print("DEBUG: messages or records? {0}".format(re.search(r'\|\s*count', query, re.IGNORECASE)))
        if status['state'] == 'DONE GATHERING RESULTS' and (
                not re.search(r'\|\s*count', query, re.IGNORECASE) or forceMessagesResults
                ):
            # Non-aggregated results, Messages only
            count = status['messageCount']
            limit2 = count if count < limit and count != 0 else limit # compensate bad limit check
            try:
                r = self.sumo_conn.search_job_messages(sj, limit=limit2)
                return(r['messages'])
            except Exception as e:
                print("Exception: Failed to get search messages: {0}".format(e))
        elif status['state'] == 'DONE GATHERING RESULTS':
            # Aggregated results
            count = status['recordCount']
            limit2 = count if count < limit and count != 0 else limit # compensate bad limit check
            try:
                r = self.sumo_conn.search_job_records(sj, limit=limit2)
                return(r['records'])
            except Exception as e:
                print("Exception: Failed to get search records: {0}".format(e))

        return []


    def search_df(self, query, fields=None,
                  date_field="@timestamp", days=None, start_time=None,
                  end_time=None,
                  timeZone='EST',
                  byReceiptTime=False,
                  normalize=True,
                  limit=10000,
                  forceMessagesResults=False,
                  verbosity=0,
                  export=False,
                  export_path=''
                ):
        '''
        Search Sumologic and return the results as a Pandas DataFrame.

        query: A string containing the Sumologic query search (e.g., 'item=5282 color=red')
        fields: A string containing a comma-separated list of field names to return.
                The default is to return all fields, but using this list you can
                select only certain fields, which may make things a bit faster.
        days: Search the past X days. If provided, this supercedes both start_time
              and end_time.
        start_time: A datetime() object representing the start of the search
                    window. If used without end_time, the end of the search
                    window is the current time.
        end_time: A datetime() object representing the end of the search window.
                  If used without start_time, the search start will be the earliest
                  time in the index.
        timeZone: timezone used for time range search
        byReceiptTime:  if time reference should used _receiptTime (time when Sumologic
                        got message) instead of _messageTime (time present in log message).
        normalize: If set to True, fields containing structures (i.e. subfields)
                   will be flattened such that each field has it's own column in
                   the dataframe. If False, there will be a single column for the
                   structure, with a JSON string encoding all the contents.
        limit: An integer describing the max number of search results to return.
        forceMessagesResults: Force results to be raw messages even if aggregated query.
        verbosity: Provide more verbose state. from 0 least verbose to 4 most one.
        export: Export result to file.
        export_path: file path for exporte results.
        '''
        results = list()

        for hit in self.search(query,
                               fields=fields, days=days,
                               start_time=start_time, end_time=end_time,
                               timeZone=timeZone, byReceiptTime=byReceiptTime,
                               limit=limit, forceMessagesResults=forceMessagesResults,
                               verbosity=verbosity):
            results.append(hit)

        if verbosity >=3:
            print("DEBUG: {0}".format(results))
        if normalize:
            df = pd.json_normalize(results)
        else:
            df = pd.DataFrame(results)

        for c in df.columns:
            if c == "map._count" or c == "map._timeslice":
                df[c] = pd.to_numeric(df[c])

        if export and export_path.endswith('.xlsx'):
            if verbosity >=2:
                print("DEBUG: Exporting results to excel file {0}".format(export_path))
            df.to_excel(export_path, index=False)
        elif export and export_path.endswith('.csv'):
            if verbosity >=2:
                print("DEBUG: Exporting results to csv file {0}".format(export_path))
            df.to_csv(export_path, index=False)

        return df
