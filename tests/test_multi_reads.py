#!/usr/bin/env python

import huntlib.data 

from unittest import TestCase

class TestMultiReads(TestCase):

    def test_read_json(self):
        df = huntlib.data.read_json("support/*.json", lines=True)
        (rows, cols) = df.shape

        self.assertEqual(cols, 6, "The resulting DataFrame had the wrong number of columns.")
        self.assertEqual(rows, 3000015, "The resulting DataFrame had the wrong number of rows.")
        self.assertEqual(df.index.nunique(), 3000015, "DataFrame index values are not unique.")

    def test_read_csv(self):
        df = huntlib.data.read_csv("support/*.csv")
        (rows, cols) = df.shape

        self.assertEqual(cols, 3, "The resulting DataFrame had the wrong number of columns.")
        self.assertEqual(rows, 6, "The resulting DataFrame had the wrong number of rows.")
        self.assertEqual(df.index.nunique(), 6, "DataFrame index values are not unique.")

    def test_read_json_post_process(self):
        def _post_process(df, filename):
            if 'ts' in df.columns:
                df = df.drop('ts', axis='columns')
            df['filename'] = filename 
            return df

        df = huntlib.data.read_json(
            "support/*.json", 
            lines=True,
            post_function=_post_process
        )

        (rows, cols) = df.shape

        self.assertEqual(cols, 6, "The resulting DataFrame had the wrong number of columns.")
        self.assertEqual(rows, 3000015, "The resulting DataFrame had the wrong number of rows.")
        self.assertEqual(df.index.nunique(), 3000015, "DataFrame index values are not unique.")
        self.assertNotIn('ts', df.columns, "The 'ts' field was present, but should have been dropped in post processing.")
        self.assertIn('filename', df.columns, "The 'filename' field should have been created in post processing, but was not present.")

    def test_read_csv_post_process(self):
        def _post_process(df, filename):
            if 'c' in df.columns:
                df = df.drop('c', axis='columns')
            df['filename'] = 'filename'
            return df

        df = huntlib.data.read_csv(
            "support/*.csv",
            post_function=_post_process
        )
        (rows, cols) = df.shape

        self.assertEqual(cols, 3, "The resulting DataFrame had the wrong number of columns.")
        self.assertEqual(rows, 6, "The resulting DataFrame had the wrong number of rows.")
        self.assertEqual(df.index.nunique(), 6, "DataFrame index values are not unique.")
        self.assertNotIn('c', df.columns, "The 'c' field was present, but should have been dropped in post processing.")
        self.assertIn('filename', df.columns, "The 'filename' field should have been created in post processing, but was not present.")
