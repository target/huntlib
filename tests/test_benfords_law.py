#!/usr/bin/env python

import os
import unittest
from unittest import TestCase

from huntlib.util import benfords

import pandas as pd 
import numpy as np

class TestBenfordsLaw(TestCase):

    def test_benfords_random(self):
        chi2, p, counts = benfords(np.random.randint(low=1, high=10000, size=1000))

        self.assertGreaterEqual(
            chi2,
            0.05,
            f"Somehow, random numbers conformed to Benford's Law, which is highly unlikely. (chisquare={chi2})"
        )

        self.assertGreaterEqual(
            p,
            0.99,
            f"Chi square p-value was too low."
        )

    def test_benfords_benfords(self):
        nums = [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2,
                3, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 9]

        chi2, p, counts = benfords(nums)

        self.assertLessEqual(
            chi2,
            0.05,
            f"The chosen distribution did not conform to Benford's law, but should have. (chisquare={chi2})"
        )

        self.assertGreaterEqual(
            p,
            0.99,
            f"Chi square p-value was too low."
        )
