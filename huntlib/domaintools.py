#!/usr/bin/env python3

import pandas as pd
import numpy as np

from configparser import ConfigParser

from domaintools import API
from domaintools.exceptions import BadRequestException, NotFoundException

from tqdm import tqdm

import os.path

from functools import reduce

__all__ = ['DomainTools']

class DomainTools(object):

    _DEFAULT_CONFIG_FILE = os.path.expanduser("~/.huntlibrc")

    _handle = None # API Handle
    _account_information = None # Cached information about the API user's account
    _available_api_calls = None # Cached list of API endpoints the account has access to

    def __init__(self, *args, **kwargs):

        # FIXME: this should be a huntlib-wide config capability
        # Read our config file, if it exists
        config = ConfigParser()
        config.read(self._DEFAULT_CONFIG_FILE)
        
        api_username = ""
        api_key = ""

        if 'api_username' in kwargs:
            api_username = kwargs['api_username']
        elif config.has_option('domaintools', 'api_username'):
            api_username = config.get('domaintools', 'api_username')

        if 'api_key' in kwargs:
            api_key = kwargs['api_key']
        elif config.has_option('domaintools', 'api_key'):
            api_key = config.get('domaintools', 'api_key')

        self.authenticate(
            api_username=api_username,
            api_key=api_key
        )

        self._account_information = self.account_information(force_refresh=True)
        self._available_api_calls = self.available_api_calls(force_refresh=True)


    def authenticate(self, api_username="", api_key=""):
        """
        Authenticate to the DomainTools API. 

        Params:
          api_username: a string containing the account name to log in with
          api_key: a string containing the API secret key (password) to log in with

        Errors:
          Will raise ValueError if the api_username or api_key are not provided
          or are of the wrong type.
        """
        # Sanity check the provided authentication info
        if not api_username:
            raise ValueError("You must supply a value for 'api_username'.")
        elif not isinstance(api_username, str):
            raise ValueError("The 'api_username' field must be a string.")

        if not api_key:
            raise ValueError("You must supply a value for 'api_key'.")
        elif not isinstance(api_key, str):
            raise ValueError("The 'api_key' field must be a string.")


        # Actually authenticate now
        self._handle = API(
            api_username,
            api_key
        )


    def account_information(self, force_refresh=False, **kwargs):

        if self._account_information and not force_refresh:
            return self._account_information

        res = self._handle.account_information(**kwargs)

        if res:
            info = dict()
            for item in res:
                id = item.pop('id')
                info[id] = dict(item)
            self._account_information = info

        return self._account_information

    def available_api_calls(self, force_refresh=False, **kwargs):

        if self._available_api_calls and not force_refresh:
            return self._available_api_calls

        res = self._handle.available_api_calls(**kwargs)

        if res:
            self._available_api_calls = list(res)

        return self._available_api_calls

    def whois(self, query=None, **kwargs):

        if not query:
            raise ValueError("You must supply either a domain or an IP address.")
        elif not isinstance(query, str):
            raise ValueError("The query parameter must be a string.")
        
        whois_info = dict(list(self._handle.whois(query, **kwargs)))

        return whois_info

    def parsed_whois(self, query=None, flatten=False, **kwargs):

        if not query:
            raise ValueError(
                "You must supply either a domain or an IP address.")
        elif not isinstance(query, str):
            raise ValueError(
                "The query parameter must be a string.")

        whois_info = dict(list(self._handle.parsed_whois(query, **kwargs)))
        
        if flatten:
            # Normalize the nested dictionary keys into a single level.
            whois_info = pd.json_normalize(whois_info).iloc[0].to_dict()

        return whois_info

    def brand_monitor(self, query=None, **kwargs):
        if not query:
            raise ValueError("You must specify a query pattern.")
        elif isinstance(query, list):
            query = "|".join(query)
        elif not isinstance(query, str):
            raise ValueError("The 'query' parameter must be either a string or a list of strings.")

        return list(self._handle.brand_monitor(query, **kwargs))

    def domain_profile(self, query=None, flatten=False, **kwargs):
        if not query:
            raise ValueError("You must specify a query domain.")
        elif not isinstance(query, str):
            raise ValueError("query parameter must be a string.")

        profile = dict(list(self._handle.domain_profile(query, **kwargs)))

        if flatten:
            # Normalize the nested dictionary keys into a single level.
            profile = pd.json_normalize(profile).iloc[0].to_dict()

        return profile

    def domain_reputation(self, domain=None, reasons=False, **kwargs):
        if not domain:
            raise ValueError("You must specify a query domain.")
        elif not isinstance(domain, str):
            raise ValueError("The domain parameter must be a string.")

        try:
            reputation = dict(list(self._handle.reputation(domain, reasons, **kwargs)))
        except (BadRequestException, NotFoundException):
            return dict()

        return reputation

    def enrich(self, df=None, column=None, prefix='dt_whois.', progress_bar=False, fields=None):
        if df is None:
            raise ValueError("You must supply a pandas DataFrame in the 'df' parameter.")
        elif not isinstance(df, pd.core.frame.DataFrame):
            raise ValueError("The argument for the 'df' parameter must be a pandas DataFrame.")

        if not column:
            raise ValueError("You must supply a column name to enrich.")
        elif not isinstance(column, str):
            raise ValueError("The column name must be a 'str'.")
        elif not column in df.columns:
            raise ValueError(f"The column '{column}' does not exist in the frame.")

        if prefix is None or not isinstance(prefix, str):
            raise ValueError("The column name prefix must be a 'str'.")

        if fields is not None and not isinstance(fields, list):
            raise ValueError("The 'fields' parameter must be a list of strings.")

        # WHOIS Enrichment
        if progress_bar:
            tqdm.pandas(desc='Enriching WHOIS')
            apply_func = df[column].progress_apply
        else:
            apply_func = df[column].apply

        whois_df = apply_func(
            lambda d: pd.Series(self.parsed_whois(d, flatten=True))
        )

        whois_df = whois_df.add_prefix('dt_whois.')

        # Domain reputation enrichment
        if progress_bar:
            tqdm.pandas(desc='Enriching Reputation')
            apply_func = df[column].progress_apply
        else:
            apply_func = df[column].apply

        reputation_df = apply_func(
            lambda d: pd.Series(self.domain_reputation(d), dtype=object)
        )

        reputation_df = reputation_df.add_prefix('dt_reputation.')

        # Combine all the enrichment data into a single DataFrame
        data_dfs = [whois_df, reputation_df]

        enrichment_df = reduce(
            lambda left, right: pd.merge(
                left, 
                right, 
                left_index=True, 
                right_index=True
            ), 
            data_dfs
        )

        # If we asked for only certain fields, filter for those
        if fields:
            enrichment_df = enrichment_df[fields]

        df = df.merge(
            enrichment_df,       
            left_index=True, 
            right_index=True
        )

        return df

