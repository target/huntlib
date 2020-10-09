#!/usr/bin/env python

from huntlib.util import punctuation_pattern
import pandas as pd
import numpy as np 

from unittest import TestCase

class TestPunctuationPattern(TestCase):
    _event_message_1 = '192.168.1.1 - - [10/Oct/2020:12:32:27 +0000] "GET /some/web/app?param=test&param2=another_test" 200 9987'
    _event_message_2 = 'ERROR: Can\'t resolve "nosuchhost": No such host.'
    _punct_pattern_1 = '..._-_-_[//:::_+]_\"_///?=&=_\"__'
    _punct_pattern_2 = ':_\'__\"\":___.'

    _expected_pattern_result = pd.Series([_punct_pattern_1, _punct_pattern_2])

    def test_punctuation_pattern_single_string(self):
        res = punctuation_pattern(self._event_message_1)

        self.assertEqual(res, self._punct_pattern_1) 

    def test_punctuation_pattern_list(self):
        res = punctuation_pattern(
            [
                self._event_message_1,
                self._event_message_2
            ]
        )

        self.assertListEqual(list(res), list(self._expected_pattern_result))

    def test_punctuation_pattern_series(self):
        res = punctuation_pattern(
            pd.Series(
                [
                    self._event_message_1,
                    self._event_message_2
                ]
            )
        )

        self.assertListEqual(list(res), list(self._expected_pattern_result))

    def test_punctuation_pattern_escape_quotes(self):
        res = punctuation_pattern("\'\"")
        self.assertEqual(res, '\'\"')

        res = punctuation_pattern("\'\"", escape_quotes=False)
        self.assertEqual(res, '\'\"')

        res = punctuation_pattern("\'\"", escape_quotes=True)
        self.assertEqual(res, '\\\'\\\"')


