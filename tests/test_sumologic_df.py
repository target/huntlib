#!/usr/bin/env python

from huntlib.sumologic import SumologicDF

from unittest import TestCase

class TestSumologicDF(TestCase):
    _sumo_url = "https://api.us2.sumologic.com/api/v1"
    _sumo_accessid = "xxxxx"
    _sumo_accesskey = "xxxxx"

    _sumo_conn = None

    @classmethod
    def setUpClass(self):
        '''
        Log into the Sumologic server once, and reuse that connection for all the 
        tests in this module.
        '''
        e = SumologicDF(
            url=self._sumo_url,
            accessid=self._sumo_accessid,
            accesskey=self._sumo_accesskey,
        )

        self.assertNotEqual(
            e, None, "SumologicDF() returned a None object at login.")

        self.sumo_conn = e

    def test_basic_search(self):
        '''
        Do the most basic search we can (all events in the index over all
        time).  Then make sure we got the number of events we think we should
        have. This version returns results as a generator.
        '''
        results = self.sumo_conn.search(
            "* | count _sourceCategory"
        )

        l = list(results)

        self.assertGreaterEqual(
            len(l), 
            5, 
            "There should be exactly 5 search results or more."
        )

        for col in ['_count', '_sourcecategory']:
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
        df = self._sumo_conn.search_df(
            "* | count _sourceCategory"
        )

        self.assertGreaterEqual(
            df.shape[0],
             5, 
             "There should be 5 search results or more."
        )

        for col in ['_count', '_sourcecategory']:
            self.assertTrue(
                col in df.columns,
                f"Column '{col}' was not found in the search results.'"
            )

    def test_filtered_search(self):
        '''
        Test a simple search and return a generator of results. Make sure we have 
        the proper number of results.
        '''

        results = self._sumo_conn.search(
            "* | count _sourceCategory"
        )

        self.assertEqual(
            len(list(results)),
            3,
            "There should be exactly 3 search results with min <= 2"
        )

    def test_filtered_search_df(self):
        '''
        Test a simple search and return a DataFrame of results. Make sure we have 
        the proper number of results.
        '''

        df = self._sumo_conn.search_df(
            "* | count _sourceCategory"
        )

        self.assertEqual(
            df.shape[0],
            3,
            "There should be exactly 3 search results with min <= 2"
        )
