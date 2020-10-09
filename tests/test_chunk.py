#!/usr/bin/env python

from huntlib.data import chunk
import numpy as np

from unittest import TestCase

class TestChunk(TestCase):
    def test_chunk(self):
        l = list(np.random.randint(10, size=100))

        res = list(chunk(l))

        # There should be 10 equal chunks with the default chunk size
        self.assertEqual(len(res), 10)

        # All chunks should be size 10
        self.assertEqual(len(res[0]), 10)

        # Rechunk with an odd size that won't result in equal chunks
        res = list(chunk(l, size=9))

        self.assertEqual(len(res), 12)
        self.assertEqual(len(res[0]), 9)
        self.assertEqual(len(res[-1]), 1)