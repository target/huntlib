from __future__ import print_function
from builtins import object
import splunklib.client as client
import splunklib.results as results
import pandas as pd
from pandas.io.json import json_normalize
from datetime import datetime

class SplunkDF(object):
    '''
    The SplunkDF() class searches Splunk and returns results as a Pandas
    DataFrame.  This makes it easier to work with the search results with
    standard data analysis techniques.

    Example Usage:

        # Establish an connection to the Splunk server. Whether this is SSL/TLS
        # or not depends on the server, and you don't really get a say.
        s = SplunkDF(host=splunk_server, username="myuser", password="mypass")

        # Fetch all search results across all time
        df = s.search(spl="search index=win_events EventCode=4688")

        # Fetch only specific fields, still across all time
        df = s.search(spl="search index=win_events EventCode=4688 | table ComputerName _time New_Process_Name Account_Name Creator_Process_ID New_Process_ID Process_Command_Line")

        # Time bounded search, 2 days prior to now
        df = s.search(spl="search index=win_events EventCode=4688", days=2)

        # Time bounded search using Python datetime() values
        df = s.search(
                        spl="search index=win_events EventCode=4688",
                        start_time=datetime.now() - timedelta(days=2),
                        end_time=datetime.now()
        )

        # Time bounded search using Splunk notation
        df = s.search(
                        spl="search index=win_events EventCode=4688",
                        start_time="-2d@d",
                        end_time="@d"
        )
    '''

    splunk_conn = None # The connection to the Splunk server (Splunk client)

    def __init__(self, host=None, username=None, password=None, port=8089):
        '''
        Create the SplunkDF object and login to the Splunk server.
        '''

        self.splunk_conn = client.connect(host=host, username=username,
                                          password=password, port=port,
                                          autoLogin=True, max_count=0,
                                          max_time=0)

    def search(self, spl, mode="normal", search_args=None, verbose=False,
               days=None, start_time=None, end_time=None):
        '''
        Search Splunk and return the results as a list of dicts.

        spl: A string containing the Splunk search in SPL form
        mode: A string specifying the type of Splunk search to run ("normal" or "realtime")
        search_args: A dict containing any additional search parameters to pass to
              the Splunk server.
        days: Search the past X days. If provided, this supercedes both start_time
              and end_time.
        start_time: A datetime() object representing the start of the search
                    window, or a string in Splunk syntax (e.g., "-2d@d"). If used
                    without end_time, the end of the search window is the current time.
        end_time: A datetime() object representing the end of the search window, or a
                  string in Splunk syntax (e.g., "-2d@d"). If used without start_time,
                  the search start will be the earliest timestamp in Splunk.
        verbose: If True, any errors, warnings or other messages encountered
                 by the search process will be printed to stdout.  The default is False
                 (suppress these messages).
        '''
        if not search_args or not isinstance(search_args, dict):
            search_args = dict()
        search_args["search_mode"] = mode

        if days:
            # Search from current time backwards
            search_args["earliest_time"] = "-%dd" % days
        else:
            if start_time:
                # convert to string if it's a datetime
                if isinstance(start_time, datetime):
                    start_time = start_time.isoformat()
                search_args["earliest_time"] = start_time
            if end_time:
                # convert to string if it's a datetime
                if isinstance(end_time, datetime):
                    end_time = end_time.isoformat()
                search_args["latest_time"] = end_time

        # Use the "export" job type, since that's the most reliable way to return possibly large result sets
        export_results = self.splunk_conn.jobs.export(spl, **search_args)

        reader = results.ResultsReader(export_results)

        for res in reader:
            if isinstance(res, dict):
                yield res
            elif isinstance(res, results.Message) and verbose:
                print("Message: %s" % res)

    def search_df(self, spl, mode="normal", search_args=None, verbose=False,
                  days=None, start_time=None, end_time=None, normalize=True):
        '''
        Search Splunk and return the results as a Pandas DataFrame.

        spl: A string containing the Splunk search in SPL form
        mode: A string specifying the type of Splunk search to run ("normal" or "realtime")
        search_args: A dict containing any additional search parameters to pass to
              the Splunk server.
        days: Search the past X days. If provided, this supercedes both start_time
              and end_time.
        start_time: A datetime() object representing the start of the search
                    window, or a string in Splunk syntax (e.g., "-2d@d"). If used
                    without end_time, the end of the search window is the current time.
        end_time: A datetime() object representing the end of the search window, or a
                  string in Splunk syntax (e.g., "-2d@d"). If used without start_time,
                  the search start will be the earliest timestamp in Splunk.
        verbose: If True, any errors, warnings or other messages encountered
                 by the search process will be printed to stdout.  The default is False
                 (suppress these messages).
        normalize: If set to True, fields containing structures (i.e. subfields)
                   will be flattened such that each field has it's own column in
                   the dataframe. If False, there will be a single column for the
                   structure, with a JSON string encoding all the contents.
        '''

        results = list()
        for hit in self.search(spl=spl, mode=mode,
                               search_args=search_args, verbose=verbose,
                               days=days, start_time=start_time,
                               end_time=end_time):
            results.append(hit)

        if normalize:
            df = json_normalize(results)
        else:
            df = pd.DataFrame(results)

        return df
