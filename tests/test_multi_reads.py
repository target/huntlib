#!/usr/bin/env python

import huntlib.data 

from unittest import TestCase

class TestMultiReads(TestCase):

    def test_read_json(self):
        df = huntlib.data.read_json("support/*.json", lines=True)
        (rows, cols) = df.shape

        self.assertEqual(cols, 6, "The resulting DataFrame had the wrong number of columns.")
        self.assertEqual(rows, 1000015, "The resulting DataFrame had the wrong number of rows.")
        self.assertEqual(df.index.nunique(), 1000015, "DataFrame index values are not unique.")

    def test_read_csv(self):
        df = huntlib.data.read_csv("support/*.csv")
        (rows, cols) = df.shape

        self.assertEqual(cols, 3, "The resulting DataFrame had the wrong number of columns.")
        self.assertEqual(rows, 6, "The resulting DataFrame had the wrong number of rows.")
        self.assertEqual(df.index.nunique(), 6, "DataFrame index values are not unique.")


