#!/usr/bin/env python

import huntlib

from unittest import TestCase

class TestEntropy(TestCase):
    def test_entropy(self):
        r = huntlib.entropy("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus eget turpis vitae metus posuere dapibus eget in ligula.")
        self.assertAlmostEqual(r, 4.0668415928803086)

    def test_entropy_per_byte(self):
        r = huntlib.entropy_per_byte("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus eget turpis vitae metus posuere dapibus eget in ligula.")
        self.assertAlmostEqual(r, 0.033334767154756625)
