from __future__ import print_function

import multiprocessing
import multiprocessing.managers
import platform
import time
from builtins import object
from datetime import datetime
from multiprocessing import (Manager, Process, Queue, cpu_count,
                             set_start_method)
from sys import stderr

import pandas as pd
import splunklib.client as client
import splunklib.results as results
import splunklib.binding

from huntlib.exceptions import AuthenticationErrorSearchException


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

    SplunkDF() will raise AuthenticationErrorSearchException() during
    initialization in the event the server denied the supplied credentials.          
    '''

    splunk_conn = None # The connection to the Splunk server (Splunk client)

    def __init__(self, host=None, username=None, password=None, token=None, port=8089):
        '''
        Create the SplunkDF object and login to the Splunk server.
        '''
        try:
            if token:
                self.splunk_conn = client.connect(
                                                host=host, port=port,
                                                token=token,
                                                autoLogin=True, max_count=0,
                                                max_time=0
                )
            else:
                self.splunk_conn = client.connect(
                                                host=host, username=username,
                                                password=password, port=port,
                                                autoLogin=True, max_count=0,
                                                max_time=0
                )
        except splunklib.binding.AuthenticationError:
            raise AuthenticationErrorSearchException("Login failed.")

    def _retrieve_parallel_worker(self, job, offset_queue, page_size, search_results):

        while not offset_queue.empty():
            offset = offset_queue.get()

            paginate_args = dict(
                count=page_size,
                offset=offset
            )

            page_results = job.results(**paginate_args)

            for result in results.ResultsReader(page_results):
                if isinstance(result, dict):
                    search_results.append(result)


    def _retrieve_parallel(self, job, page_size=1000, processes=4):


        manager = Manager()
        search_results = manager.list()
        offset_queue = Queue()


        result_count = int(job['resultCount'])

        offset = 0

        while (offset < result_count):
            offset_queue.put(offset)
            offset += page_size

        workers = list()

        for _ in range(processes):
            p = Process(
                target=self._retrieve_parallel_worker,
                args=(
                    job,
                    offset_queue,
                    page_size,
                    search_results
                )
            )

            workers.append(p)
            p.start()

        for p in workers:
            p.join()

        return list(search_results)

    def _process_result(self, result, **kwargs):
        if isinstance(result, results.Message):
            if kwargs['verbose']:
                print(f"Message: {result}")
            return None

        if isinstance(result, dict):
            # Remove internal fields if requested
            if kwargs['internal_fields'] is False:
                for field in [key for key in result.keys() if key.startswith('_')]:
                    result.pop(field)
            elif isinstance(kwargs['internal_fields'], str):
                for field in list(map(lambda x: x.strip(), kwargs['internal_fields'].split(','))):
                    result.pop(field)

        return result


    def search(self, *args, **kwargs):
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
        limit: An integer describing the max number of search results to return.
        fields: A comma-separated string listing all of the fields to be returned in
                the results. If not 'None', this is appended to the end of the 'spl'
                query, like so: "| fields field1,field2,field3".  The default is '*',
                meaning all fields.
        internal_fields: Control whether or not to return Splunk's internal fields.
                If set to False, all fields with names beginning with an underscore 
                will be removed from the results.  If set to True, nothing will be removed.
                If this is a string, treat it as a comma-separated list of fields to remove
                from the results. Default is False.
        '''

        # Valid argument checking
        valid_args = [
            'spl', 
            'mode', 
            'search_args', 
            'verbose', 
            'days', 
            'start_time',
            'end_time', 
            'limit',
            'fields',
            'internal_fields',
            'processes',
            'page_size'
        ]
        for arg in kwargs.keys():
            if not arg in valid_args:
                raise TypeError(f"search() got an unexpected keyword argument '{arg}'")

        # Make sure args contain what we think they should

        # Set default values, but only if they don't already exist
        kwargs['mode'] = kwargs.get('mode', 'normal')
        kwargs['search_args'] = kwargs.get('search_args', None)
        kwargs['verbose'] = kwargs.get('verbose', False)
        kwargs['days'] = kwargs.get('days', None)
        kwargs['start_time'] = kwargs.get('start_time', None)
        kwargs['end_time'] = kwargs.get('end_time', None)
        kwargs['limit'] = kwargs.get('limit', None)
        kwargs['fields'] = kwargs.get('fields', '*')
        kwargs['internal_fields'] = kwargs.get('internal_fields', False)
        kwargs['processes'] = kwargs.get('processes', 1)
        kwargs['page_size'] = kwargs.get('page_size', 1000)

        # SPL query can be either the first positional argument or the 'spl' keyword arg
        spl = None
        if len(args) > 0:
            spl = args[0]
        elif "spl" in kwargs:
            spl = kwargs['spl']

        if spl is None:
            raise ValueError("You must specify an SPL search string.")

        # If present, internal_fields must be either bool or str
        if not (isinstance(kwargs['internal_fields'], bool) or isinstance(kwargs['internal_fields'], str)):
            raise ValueError(f"internal_fields must be a boolean or a string, not {type(kwargs['internal_fields'])}.")

        spl += f"| fields {kwargs['fields']}"

        if not kwargs['search_args'] or not isinstance(kwargs['search_args'], dict):
            kwargs['search_args'] = dict()
        kwargs['search_args']["search_mode"] = kwargs['mode']

        if kwargs['days']:
            # Search from current time backwards
            kwargs['search_args']["earliest_time"] = "-%dd" % kwargs['days']
        else:
            if kwargs['start_time']:
                # convert to string if it's a datetime
                if isinstance(kwargs['start_time'], datetime):
                    kwargs['start_time'] = kwargs['start_time'].isoformat()
                kwargs['search_args']["earliest_time"] = kwargs['start_time']
            if kwargs['end_time']:
                # convert to string if it's a datetime
                if isinstance(kwargs['end_time'], datetime):
                    kwargs['end_time'] = kwargs['end_time'].isoformat()
                kwargs['search_args']["latest_time"] = kwargs['end_time']

        if kwargs['limit']:

            kwargs['search_args']['exec_mode'] = 'blocking'
            kwargs['search_args']['search_mode'] = 'normal'
            kwargs['search_args']['max_count'] = kwargs['limit']

            job = self.splunk_conn.jobs.create(
                spl,
                **kwargs['search_args']
            )

            for res in self._retrieve_parallel(job):
                res = self._process_result(res, **kwargs)
                if res is not None:      
                    yield res
        else:
            search_results = self.splunk_conn.jobs.export(
                spl, 
                **kwargs['search_args']
            )

            reader = results.ResultsReader(search_results)

            for res in reader:
                    res = self._process_result(res, **kwargs)
                    if res is not None:
                        yield res

#    def search_df(self, spl, mode="normal", search_args=None, verbose=False,
#                  days=None, start_time=None, end_time=None, normalize=True,
#                  limit=None, fields="*", internal_fields=False, processes=1,
#                  page_size=1000):

    def search_df(self, *args, **kwargs):
        '''
        Search Splunk and return the results as a Pandas DataFrame.

        Accepts all the same arguments as the search() function
        '''

        normalize = kwargs.get('normalize', True)

        results = list()
        for hit in self.search(*args, **kwargs):
            results.append(hit)

        if normalize:
            df = pd.json_normalize(results)
        else:
            df = pd.DataFrame(results)

        return df

