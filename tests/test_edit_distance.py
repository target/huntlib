#!/usr/bin/env python

from huntlib.util import edit_distance

from unittest import TestCase

class TestDistance(TestCase):
    _str1 = "Lorem ipsum dolor sit amet"
    _str2 = "Lorem ipsim dollar sit aemt"

    def test_default_algo(self):
        '''
        Tests that the default algorithm is 'damerau-levenshtein'.
        '''
        r_default = edit_distance(self._str1, self._str2)
        r_dameraulevenshtein = edit_distance(self._str1, self._str2, method="damerau-levenshtein")
        self.assertEqual(r_default, r_dameraulevenshtein)

    def test_levenshtein(self):
        '''
        Tests that the Levenshtein algorithm returns expected value.
        '''
        r = edit_distance(self._str1, self._str2, method='levenshtein')
        self.assertEqual(r, 5)

    def test_damerau_levenshtein(self):
        '''
        Tests that the Damerau-Levenshtein algorithm returns expected value.
        '''
        r = edit_distance(self._str1, self._str2, method='damerau-levenshtein')
        self.assertEqual(r, 4)

    def test_hamming(self):
        '''
        Tests that the Hamming algorithm returns expected value.
        '''
        r = edit_distance(self._str1, self._str2, method='hamming')
        self.assertEqual(r, 12)

    def test_jaro(self):
        '''
        Tests that the Jaro algorithm returns expected value.
        '''
        r = edit_distance(self._str1, self._str2, method='jaro')
        self.assertAlmostEqual(r, 0.8400997)

    def test_jaro_winkler(self):
        '''
        Tests that the Jaro-Winkler algorithm returns expected value.
        '''
        r = edit_distance(self._str1, self._str2, method='jaro-winkler')
        self.assertAlmostEqual(r, 0.9040598)

    def test_invalid_algo(self):
        '''
        Tests that we raise an exception when method isn't one of the supported
        methods, it's None, or it's some other invalid data type.
        '''
        self.assertRaises(ValueError, edit_distance, self._str1, self._str2, method='nosuchmethod')
        self.assertRaises(ValueError, edit_distance, self._str1, self._str2, method=None)
        self.assertRaises(ValueError, edit_distance, self._str1, self._str2, method=3)

    def test_none_strings(self):
        '''
        Tests that we raise an exception if either or both of the strings is
        None or some other invalid data type.
        '''
        self.assertRaises(TypeError, edit_distance, None, self._str2)
        self.assertRaises(TypeError, edit_distance, self._str1, None)
        self.assertRaises(TypeError, edit_distance, None, None)
        self.assertRaises(TypeError, edit_distance, self._str1, 4)
        self.assertRaises(TypeError, edit_distance, 4, self._str1)
        self.assertRaises(TypeError, edit_distance, 4, 4)
