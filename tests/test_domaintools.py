#!/usr/bin/env python

import os
import unittest
from multiprocessing import cpu_count
from unittest import TestCase

from huntlib.domaintools import DomainTools

import pandas as pd 
import numpy as np

class TestDomainTools(TestCase):

    _handle = None

    @classmethod
    def setUpClass(self):
        '''
        Authenticate to DomainTools once, and reuse that connection for all the 
        tests in this module.
        '''

        # This uses the default creds stored in ~/.huntlibrc
        dt = DomainTools()

        self._handle = dt

    def test_account_information(self):
        limits = self._handle.account_information()

        self.assertIsInstance(
            limits, 
            dict,
            f"The return type of account_information was {type(limits)} not 'dict'."
        )

        self.assertGreater(
            len(limits),
            0,
            "account_information() did not return any information."
        )

    def test_available_api_calls(self):

        api_calls = self._handle.available_api_calls()

        self.assertIsInstance(
            api_calls,
            list,
            f"The return type of available_api_calls was {type(api_calls)} not 'list'."
        )

        self.assertGreater(
            len(api_calls),
            0,
            "available_api_calls() did not return any information."
        )

    def test_whois_domain(self):

        whois = self._handle.whois('google.com')

        self.assertIsInstance(
            whois,
            dict,
            f"The return type of whois() was {type(whois)} not 'dict'."
        )

        self.assertIn(
            "registrant",
            whois,
            "Couldn't find the 'registrant' field in whois data."
        )

        self.assertEqual(
            "Google LLC",
            whois['registrant'],
            "The registrant information does not seem to be correct."
        )

    def test_whois_ipv4(self):

        whois = self._handle.whois('172.217.164.164')

        self.assertIsInstance(
            whois,
            dict,
            f"The return type of whois() was {type(whois)} not 'dict'."
        )

        self.assertIn(
            "registrant",
            whois,
            "Couldn't find the 'registrant' field in whois data."
        )

        self.assertEqual(
            "Google LLC",
            whois['registrant'],
            "The registrant information does not seem to be correct."
        )

    def test_parsed_whois_domain(self):

        whois = self._handle.parsed_whois('google.com')

        self.assertIsInstance(
            whois,
            dict,
            f"The return type of whois() was {type(whois)} not 'dict'."
        )

        self.assertIn(
            "registrant",
            whois,
            "Couldn't find the 'registrant_org' field in whois data."
        )

        self.assertEqual(
            "Google LLC",
            whois['registrant'],
            "The registrant information does not seem to be correct."
        )

        self.assertIn(
            'registration',
            whois,
            "Couldn't find the 'registration' field in the parsed whois data."
        )

        self.assertIn(
            'created',
            whois['registration'],
            "Couldn't find the 'created' field in the 'registration' dict."
        )

        self.assertEqual(
            "1997-09-15",
            whois['registration']['created'],
            "The registration create information does not seem to be correct."
        )

    def test_parsed_whois_ipv4(self):

        whois = self._handle.parsed_whois('8.8.8.8')

        self.assertIsInstance(
            whois,
            dict,
            f"The return type of whois() was {type(whois)} not 'dict'."
        )

    def test_enrich(self):

        df = pd.DataFrame(['google.com', 'microsoft.com', '8.8.8.8'], columns=["domain"])

        enriched_df = self._handle.enrich(df, column='domain')

        self.assertEqual(
            enriched_df.shape[1],
            76,
            "Enriched DataFrame does not have the correct number of columns."
        )

        self.assertIn(
            'dt_whois.parsed_whois.contacts.registrant.org',
            enriched_df.columns,
            "Could not find the 'dt_whois.parsed_whois.contacts.registrant.org' column in the enriched frame."
        )

    def test_brand_monitor(self):

        # Because this depends so much on which domains are registered
        # each day, it's hard to find a real term that has guaranteed
        # matches.  So we just look for anything with the letter 'a' in
        # it, which is virtualy assured.
        domains = self._handle.brand_monitor('a')

        self.assertIsInstance(
            domains,
            list,
            f"The return from brand_monitor() was a {type(domains)}, not a list."
        )

        self.assertGreater(
            len(domains),
            0,
            "The brand_monitor search returned no results."
        )

    def test_domain_reputation(self):

        # We can't predict a given domain name's exact reputation for
        # testing purposes, but we can make a couple of assumptions.
        
        # ASSUMPTION 1: We're using the domaintools API, and their own 
        # domain is whitelisted to give a consistent 0.0 risk score.
        risk = self._handle.domain_reputation('domaintools.com')

        self.assertEqual(
            risk['risk_score'],
            0.0,
            "The 'domaintools.com' domain should have a 0.0 risk score."
        )

        # ASSUMPTION 2: Any given domain in a 'risky' TLD should have a positive, 
        # non-zero score
        risk = self._handle.domain_reputation('domaintools.xyz')

        self.assertGreater(
            risk['risk_score'],
            0.0,
            "The non-existent domain should have a non-zero risk score."
        )

        # Finally, we just need to test that we get an empty dict when we pass in
        # an IP, since the API endpoint doesn't actually support IPs
        risk = self._handle.domain_reputation('8.8.8.8')

        self.assertDictEqual(
            risk,
            {},
            "Domain reputation lookup on an IP failed to return an empty dict."
        )