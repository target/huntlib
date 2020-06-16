#!/usr/bin/env python

import os
import unittest
from multiprocessing import cpu_count
from unittest import TestCase

from huntlib.splunk import SplunkDF


class TestSplunkDF(TestCase):
    _splunk_host = "localhost"
    _splunk_port = 8089 # This is the API port, NOT the UI port
    _splunk_user = "admin"
    _splunk_pass = "testpass"

    _splunk_conn = None

    @classmethod
    def setUpClass(self):
        '''
        Log into the splunk server once, and reuse that connection for all the 
        tests in this module.
        '''
        s = SplunkDF(
            host=self._splunk_host,
            port=self._splunk_port,
            username=self._splunk_user,
            password=self._splunk_pass
        )

        self.assertNotEqual(
            s, None, "SplunkDF() returned a None object at login.")

        self._splunk_conn = s

    def test_basic_search(self):
        '''
        Do the most basic search we can (all events in the index over all
        time).  Then make sure we got the number of events we think we should
        have. This version returns results as a generator.
        '''
        results = self._splunk_conn.search(
            spl="search index=main"
        )

        l = list(results)

        self.assertEqual(
            len(l), 
            5, 
            "There should be exactly 5 search results."
        )

        for key in ['min', 'max', 'label', 'ts']:
            self.assertTrue(
                # Just test the first item in the results list
                key in l[0].keys(),
                f"Key '{key}' was not found in the search results.'"
            )


    def test_basic_search_df(self):
        '''
        Do the most basic search we can (all events in the index over all
        time).  Then make sure we got the number of events we think we should
        have and that all data columns are present. 
        This version returns results as a pandas DataFrame().
        '''
        df = self._splunk_conn.search_df(
            spl="search index=main"
        )

        self.assertEqual(
            df.shape[0],
             5, 
             "There should be exactly 5 search results."
        )

        for col in ['min', 'max', 'label', 'ts']:
            self.assertTrue(
                col in df.columns,
                f"Column '{col}' was not found in the search results.'"
            )

    def test_filtered_search(self):
        '''
        Test a simple SQL search and return a generator of results. Make sure we have 
        the proper number of results.
        '''

        results = self._splunk_conn.search(
            spl="search index=main min<=2"
        )

        self.assertEqual(
            len(list(results)),
            3,
            "There should be exactly 3 search results with min <= 2"
        )

    def test_filtered_search_df(self):
        '''
        Test a simple SQL search and return a DataFrame of results. Make sure we have 
        the proper number of results.
        '''

        df = self._splunk_conn.search_df(
            spl="search index=main min<=2"
        )

        self.assertEqual(
            df.shape[0],
            3,
            "There should be exactly 3 search results with min <= 2"
        )

    def test_internal_fields(self):
        '''
        Test to ensure the internal_fields parameter is working correctly. We
        test search_df() since that actually calls search() underneath everything
        else, so we're effectively testing both in one shot.
        '''

        # The default is to filter internal fields, so make sure we do that
        df = self._splunk_conn.search_df(
            spl="search index=main"
        )

        self.assertEqual(
            df.shape[1],
            21,
            "Default call did not filter out internal fields correctly. Wrong number of columns."
        )

        # The same, but explicitly asking for internal field filtering
        df = self._splunk_conn.search_df(
            spl="search index=main",
            internal_fields=False
        )

        self.assertEqual(
            df.shape[1],
            21,
            "Explicit 'internal_fields=False' did not filter out internal fields correctly. Wrong number of columns."
        )

        # Explicitly ask for internal fields to be preserved
        df = self._splunk_conn.search_df(
            spl="search index=main",
            internal_fields=True
        )

        self.assertEqual(
            df.shape[1],
            30,
            "Explicit 'internal_fields=True' call did not return all internal fields correctly. Wrong number of columns."
        )

        # Filter only named fields, with spaces to make sure they're split and stripped correctly
        df = self._splunk_conn.search_df(
            spl="search index=main",
            internal_fields=" _si, _time ,_sourcetype,_subsecond "
        )

        self.assertEqual(
            df.shape[1],
            26,
            "Explicitly named internal_fields did not return the correct fields correctly. Wrong number of columns."
        )

    def test_basic_search_df_parallel(self):
        '''
        Do the most basic search we can (all events in the index over all
        time).  Then make sure we got the number of events we think we should
        have and that all data columns are present. 
        This version returns results as a pandas DataFrame().
        '''
        df = self._splunk_conn.search_df(
            spl="search index=main",
            processes=cpu_count(),
            limit=10
        )

        self.assertEqual(
            df.shape[0],
            5,
            "There should be exactly 5 search results."
        )

        for col in ['min', 'max', 'label', 'ts']:
            self.assertTrue(
                col in df.columns,
                f"Column '{col}' was not found in the search results.'"
            )

    @unittest.skipUnless("HUNTLIB_TEST_EXTENDED" in os.environ, "Skipping test_large_search() because it takes a long time...")
    def test_large_search_df(self):
        '''
        Do a basic search that should return a lot of rows.  This requires
        you to have loaded the "bigdata" index with data.

        We skip this by default because it takes a very long time, but you can
        re-enable it by setting the HUNTLIB_TEST_EXTENDED environment variable.
        '''
        df = self._splunk_conn.search_df(
            spl="search index=bigdata",
            fields='val'
        )

        self.assertEqual(
            df.shape[0],
            1000000,
            "Wrong number of search results."
        )

        self.assertTrue(
            "val" in df.columns,
            "Column 'val' was not found in the search results."
        )
