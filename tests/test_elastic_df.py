#!/usr/bin/env python

from huntlib.elastic import ElasticDF

from unittest import TestCase

class TestElasticDF(TestCase):
    _es_url = "https://localhost:9200"
    _es_user = "elastic"
    _es_pass = "testpass"
    _es_ca_certs = "support/certs/ca/ca.crt"

    _es_conn = None

    @classmethod
    def setUpClass(self):
        '''
        Log into the Elastic server once, and reuse that connection for all the 
        tests in this module.
        '''
        e = ElasticDF(
            url=self._es_url,
            username=self._es_user,
            password=self._es_pass,
            ca_certs=self._es_ca_certs
        )

        self.assertNotEqual(
            e, None, "ElasticDF() returned a None object at login.")

        self._es_conn = e

    def test_basic_search(self):
        '''
        Do the most basic search we can (all events in the index over all
        time).  Then make sure we got the number of events we think we should
        have. This version returns results as a generator.
        '''
        results = self._es_conn.search(
            lucene="*",
            index="testdata"
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
        df = self._es_conn.search_df(
            lucene="*",
            index="testdata"
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
        Test a simple search and return a generator of results. Make sure we have 
        the proper number of results.
        '''

        results = self._es_conn.search(
            lucene="min:<=2",
            index="testdata"
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

        df = self._es_conn.search_df(
            lucene="min:<=2",
            index="testdata"
        )

        self.assertEqual(
            df.shape[0],
            3,
            "There should be exactly 3 search results with min <= 2"
        )
