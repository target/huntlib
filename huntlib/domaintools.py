#!/usr/bin/env python3

import pandas as pd
import numpy as np

from configparser import ConfigParser

from domaintools import API
from domaintools.exceptions import BadRequestException, NotFoundException

from tqdm.auto import tqdm

import os.path

from functools import reduce

from .decorators import retry
from .data import flatten as huntlib_data_flatten

__all__ = ['DomainTools']

class DomainTools(object):
    '''
    The DomainTools class allows you to easily perform some common types of calls
    to the DomainTools API.  It uses their official `domaintools_api` Python module
    to do most of the work but is not a complete replacement for that module. In
    particular, this class concentrates on a few calls that are most relevant for
    data analytic style threat hunting (risk & reputation scores, WHOIS info, etc).

    This most methods pass through any kwargs to the underlying domaintools methods, 
    with one important exception: the class consults the user's ~/.huntlibrc 
    (if present) to determine the API username and key so you don't always have to provide
    them during authentication.

    :param api_username: The API authentication username (OPTIONAL)
    :type api_username: str
    :param api_key: The API authentication key (OPTIONAL)
    :type api_key: str
    :param `**kwargs`: Additional keyword args are passed to the underlying domaintools module init
    '''

    _DEFAULT_CONFIG_FILE = os.path.expanduser("~/.huntlibrc")

    _handle = None # API Handle
    _account_information = None # Cached information about the API user's account
    _available_api_calls = None # Cached list of API endpoints the account has access to

    def __init__(self, *args, **kwargs):

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

        # Remove these from kwargs, so we don't have duplicate args.
        kwargs.pop('api_username', None)
        kwargs.pop('api_key', None)

        self.authenticate(
            api_username=api_username,
            api_key=api_key,
            **kwargs
        )

        self._account_information = self.account_information(force_refresh=True)
        self._available_api_calls = self.available_api_calls(force_refresh=True)

    @retry()
    def authenticate(self, api_username="", api_key="", **kwargs):
        """
        Authenticate to the DomainTools API. Calling this function directly is OK,
        but you won't get the benefit of consulting ~/.huntlibrc for default creds
        if you do.  

        :param api_username: The API authentication username (OPTIONAL)
        :type api_username: str
        :param api_key: The API authentication key (OPTIONAL)
        :type api_key: str
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Exceptions:
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
            api_key,
            **kwargs
        )

    @retry()
    def account_information(self, force_refresh=False, **kwargs):
        '''
        Return a dict containing information about limits and usage of the various
        domaintools API calls for the authenticated API user.

        :param force_refresh: A boolean controlling whether or not to refresh the cached info
        :type force_refresh: bool
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value:
        A single dict, where each key is the name of an endpoint from the underlying
        domaintools API, and the values are dicts containing detailed about that endpoint.

        For example:

        {
            'domain-profile': {
                'per_month_limit': None, 
                'per_minute_limit': '180', 
                'absolute_limit': None, 
                'usage': {
                    'today': '0', 
                    'month': '100'
                }, 
                'expiration_date': '2020-12-31'
            }, 
            'whois': {
                'per_month_limit': None, 
                'per_minute_limit': '180', 
                'absolute_limit': None, 
                'usage': {
                    'today': '9', 
                    'month': '997'
                }, 
                'expiration_date': '2020-12-31'
            }
        }
        '''

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

    @retry()
    def available_api_calls(self, force_refresh=False, **kwargs):
        '''
        Returns a list of endpoints available to the authenticated API user.

        :param force_refresh: A boolean controlling whether or not to refresh the cached info
        :type force_refresh: bool
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value:

        A list of strings containing the API endpoint names.

        For example:

        [
            'domain_profile', 
            'whois', 
            'whois_history', 
            'reverse_ip', 
            ...
        ]
        '''

        if self._available_api_calls and not force_refresh:
            return self._available_api_calls

        res = self._handle.available_api_calls(**kwargs)

        if res:
            self._available_api_calls = list(res)

        return self._available_api_calls

    @retry()
    def whois(self, query=None, **kwargs):
        '''
        Return basic WHOIS info for a given domain or IP address.

        :param query: A domain or IP address
        :param type: string
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value:
        A dict containing basic WHOIS information.

        For example:

        {
            'registrant': 'Google LLC', 
            'registration': {
                'created': '1997-09-15', 
                'expires': '2028-09-14', 
                'updated': '2019-09-09', 
                'registrar': 'MarkMonitor Inc.', 
                'statuses': [
                    'clientDeleteProhibited', 
                    'clientTransferProhibited', 
                    'clientUpdateProhibited', 
                    'serverDeleteProhibited', 
                    'serverTransferProhibited', 
                    'serverUpdateProhibited'
                ]
            }, 
            'name_servers': [
                'NS1.GOOGLE.COM', 
                'NS2.GOOGLE.COM', 
                'NS3.GOOGLE.COM', 
                'NS4.GOOGLE.COM'
            ], 
            'whois': {
                'date': '2020-07-12', 
                'record': 'Domain Name: google.com\nRegistry Domain ID: 2138514_DOMAIN_COM-VRSN\n...'
            }, 
            'record_source': 'google.com'
        }

        :Exceptions:
        Will raise ValueError if no query is supplied, or if the query is not a string.

        '''

        if not query:
            raise ValueError("You must supply either a domain or an IP address.")
        elif not isinstance(query, str):
            raise ValueError("The query parameter must be a string.")
        
        try:
            whois_info = dict(
                list(
                    self._handle.whois(query, **kwargs)
                )
            )
        except (BadRequestException, NotFoundException):
            return dict()

        return whois_info

    @retry()
    def parsed_whois(self, query=None, flatten=False, **kwargs):

        '''
        Return extended WHOIS info for a given domain or IP address.

        :param query: A domain or IP address
        :param type: string
        :param flatten: A boolean controlling whether to attempt to normalize the nested dicts or lists into a single flat dict (DEFAULT False)
        :type flatten: bool 
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value:
        A dict containing basic and extended WHOIS information.

        For example:

        {
            ...
            'parsed_whois': {
                'domain': 'google.com', 
                'created_date': '1997-09-15T00:00:00-07:00', 
                'updated_date': '2019-09-09T08:39:04-07:00', 
                'expired_date': '2028-09-13T00:00:00-07:00', 
                'statuses': [
                    'clientDeleteProhibited', 
                    'clientTransferProhibited', 
                    'clientUpdateProhibited', 
                    'serverDeleteProhibited', 
                    'serverTransferProhibited', 
                    'serverUpdateProhibited'
                ], 
                'name_servers': [
                    'ns1.google.com', 
                    'ns2.google.com', 
                    'ns3.google.com', 
                    'ns4.google.com'
                ], 
                'registrar': {
                    'name': 'MarkMonitor, Inc. MarkMonitor Inc.', 
                    'abuse_contact_phone': '12083895770', 
                    'abuse_contact_email': 'abusecomplaints@markmonitor.com', 
                    'iana_id': '292', 
                    'url': 'http://www.markmonitor.com', 
                    'whois_server': 'whois.markmonitor.com'
                }, 
                'contacts': {
                    'registrant': {
                        'name': '', 
                        'org': 'Google LLC', 
                        'street': [], 
                        'city': '', 
                        'state': 'CA', 
                        'postal': '', 
                        'country': 'us', 
                        'phone': '', 
                        'fax': '', 
                        'email': 'REDACTED FOR PRIVACY (DT)'
                    }
                    ...
                }
            }
            ...
        }

        :Exceptions:
        Will raise ValueError if no query is supplied, or if the query is not a string.

        '''

        if not query:
            raise ValueError(
                "You must supply either a domain or an IP address.")
        elif not isinstance(query, str):
            raise ValueError(
                "The query parameter must be a string.")

        try:
            whois_info = dict(
                list(
                    self._handle.parsed_whois(query, **kwargs)
                )
            )
        except (BadRequestException, NotFoundException):
            return dict()

        
        if flatten:
            # Normalize the nested dictionary keys into a single level.
            whois_info = huntlib_data_flatten(whois_info)

        return whois_info

    @retry()
    def brand_monitor(self, query=None, **kwargs):
        '''
        Given a query string containing one or more search terms (separated by '|'),
        return a list of any newly-active or pending domain registrationations 
        containing ALL of the terms.

        :param query: A string containing one or more search terms (separated by '|')
        :type query: string
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value:

        A list of dicts, with each dict containing a result.

        For example:

        [
            {
                'domain': '54google.com', 
                'status': 'new'
            }, 
            {
                'domain': 'aboutmicrosoftandgoogleapps.com',
                 'status': 'on-hold'
            },
            ...
        ]

        :Exceptions:

        Will raise ValueError if no query is supplied or if the query is not a string.
        '''

        if not query:
            raise ValueError("You must specify a query pattern.")
        elif isinstance(query, list):
            query = "|".join(query)
        elif not isinstance(query, str):
            raise ValueError("The 'query' parameter must be either a string or a list of strings.")

        return list(self._handle.brand_monitor(query, **kwargs))

    @retry()
    def domain_profile(self, query=None, flatten=False, **kwargs):
        '''
        Look up basic information about a domain, including DNS, WHOIS, history and
        web site info along with pointers to more detailed info.

        :param query: The domain to look up
        :type query: string
        :param flatten: A boolean controlling whether to attempt to normalize the nested dicts/lists into a single flat dict (DEFAULT False)
        :type flatten: bool 
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value:

        A dict containing the various pieces of info.  

        For example:

        {
            'registrant': {
                'name': 'Google LLC', 
                'domains': 18696, 
                'product_url': 'https://reversewhois.domaintools.com/?all[]=Google+LLC&none[]='
            }, 
            'server': {
                'ip_address': '172.217.14.196', 
                'other_domains': 151, 
                'product_url': 'https://reverseip.domaintools.com/search/?q=google.com'
            }, 
            'registration': {
                'created': '1997-09-15', 
                'expires': '2028-09-14', 
                'updated': '2019-09-09', 
                'registrar': 'MarkMonitor Inc.', 
                'statuses': [
                    'clientDeleteProhibited', 
                    'clientTransferProhibited', 
                    'clientUpdateProhibited', 
                    'serverDeleteProhibited', 
                    'serverTransferProhibited', 
                    'serverUpdateProhibited'
                ]
            }, 
            'name_servers': [
                {
                    'server': 'NS1.GOOGLE.COM', 
                    'product_url': 'https://reversens.domaintools.com/search/?q=NS1.GOOGLE.COM'
                }, 
                {
                    'server': 'NS2.GOOGLE.COM', 
                    'product_url': 'https://reversens.domaintools.com/search/?q=NS2.GOOGLE.COM'
                }, 
                {
                    'server': 'NS3.GOOGLE.COM', 
                    'product_url': 'https://reversens.domaintools.com/search/?q=NS3.GOOGLE.COM'
                }, 
                {
                    'server': 'NS4.GOOGLE.COM', 
                    'product_url': 'https://reversens.domaintools.com/search/?q=NS4.GOOGLE.COM'
                }
            ], 
            ...
        }

        :Exceptions:

        Raises ValueError if no query is supplied or if it is not a string.
        '''
        if not query:
            raise ValueError("You must specify a query domain.")
        elif not isinstance(query, str):
            raise ValueError("query parameter must be a string.")

        profile = dict(
            list(
                self._handle.domain_profile(query, **kwargs)
            )
        )

        if flatten:
            # Normalize the nested dictionary keys into a single level.
            profile = huntlib_data_flatten(profile)

        return profile

    @retry()
    def domain_reputation(self, domain=None, reasons=False, **kwargs):
        '''
        Return a risk score based on the reputation of the given domain, 
        with an optional list of reasons contributing to the score.

        :param domain: The domain for which to retrieve the score
        :type domain: string
        :param reasons: Determines whether or not to include a list of reasons for the score (DEFAULT False)
        :type reasons: bool
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value: 

        A Dict containing the requested information.  If the domain cannot be found, return
        an empty dict.

        For example:

        {
            'domain': 'domaintools.xyz', 
            'risk_score': 18.69, 
            'reasons': [
                'registrant'
            ]
        }

        :Exceptions:

        Raises ValueError if no domain is provided, or if the domain is not a string.

        '''
        if not domain:
            raise ValueError("You must specify a query domain.")
        elif not isinstance(domain, str):
            raise ValueError("The domain parameter must be a string.")

        try:
            reputation = dict(
                list(
                    self._handle.reputation(domain, reasons, **kwargs)
                )
            )
        except (BadRequestException, NotFoundException):
            return dict()

        return reputation

    @retry()
    def risk(self, domain=None,  **kwargs):
        '''
        Return risk scores for a domain with respect to individual risk factors.

        :param domain: The domain for which to retrieve the score
        :type domain: string
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value: 

        A Dict containing the requested information.  If the domain cannot be found, return
        an empty dict.

        For example:

        {
            'proximity': 18, 
            'threat_profile': 36, 
            'threat_profile_phishing': 36, 
            'threat_profile_malware': 17, 
            'threat_profile_spam': 2
        }

        :Exceptions:

        Raises ValueError if no domain is provided, or if the domain is not a string.

        '''
        if not domain:
            raise ValueError("You must specify a query domain.")
        elif not isinstance(domain, str):
            raise ValueError("The domain parameter must be a string.")

        try:
            risk = self._handle.risk(domain, **kwargs)
            # Turn the list of individual dictionaries (with duplicate
            # keys) into a single dictionary.
            risk = {x['name']: x['risk_score'] for x in risk}
        except (BadRequestException, NotFoundException):
            return dict()


        return risk
    
    @retry() 
    def iris_enrich(self, query=None, flatten=False, asframe=False, **kwargs):
        '''
        Bulk enrichment for lists of domains against the DomainTools IRIS database.
        This will do basic deduplication (e.g., 'google.com' will only be looked up 
        once no matter how many times it appears in the input list, but 'google.com',
        'www.google.com' and 'drive.google.com' are not considered duplicates).  

        :param query: The domain(s) to enrich
        :type query: list or pandas Series object
        :param flatten: A boolean controlling whether to attempt to normalize the nested dicts/lists into a single flat dict (DEFAULT False)
        :type flatten: bool 
        :param asframe: Return the enriched data as a pandas DataFrame instead of a dict (DEFAULT False)
        :param `**kwargs`: Additional arguments to pass to the underlying domaintools module

        :Return Value:
        
        Returns a dict where each key is an enriched domain and the corresponding
        value is a dict with the enrichment data for that domain.  For example:

        {
            'google.com': {
                'whois_url': 'https://whois.domaintools.com/google.com',
                'active': True,
                [...]
            },
            'microsoft.com': {
                'whois_url': 'https://whois.domaintools.com/microsoft.com',
                'active': True,
                [...]
            }
        }

        If `asframe` is True, the result is returned instead as a pandas DataFrame 
        object, where the 'domain' column contains the enriched domains, with their
        enrichment data flattened into columns, like so:

                domain          whois_url                                   active  [...]
            0   google.com      https://whois.domaintools.com/google.com    True    [...]
            1   microsoft.com   https://whois.domaintools.com/microsoft.com True    [...]
        
        '''
        if query is None:
            raise ValueError("You must specify a domain or list of domains to query.")

        if isinstance(query, list) or isinstance(query, pd.core.series.Series):
            # Convert a list of strings to a single comma-separated string
            query = ','.join(query)
        elif not isinstance(query, str):
            raise ValueError("The query must be either a string or a list of strings.")
        
        try:
            enrich = list(self._handle.iris_enrich(query, **kwargs))
        except (BadRequestException, NotFoundException):
            return dict()

        data = dict()
        for i in enrich:
            if 'domain' in i:
                domain = i.pop('domain')
                if flatten:
                    data[domain] = huntlib_data_flatten(i)
                else:
                    data[domain] = i

        if asframe:
            return pd.DataFrame(data).transpose().reset_index().rename(columns={'index': 'domain'})
        else:
            return data 
    
    def enrich(self, df=None, column=None, prefix='dt_enrich.', progress_bar=False, fields=None, batch_size=100):
        '''
        Enrich a pandas DataFrame object with information from DomainTools.  Note that the 
        original DataFrame is not modified, so you must assign the return value to a variable
        if you want to keep it.  e.g. `df = dt.enrich(df, column='domains')`.

        :param df: The DataFrame to enrich
        :type df: pandas.DataFrame
        :param column: The name of the column containin domains and/or IPs to enrich (as strings)
        :type column: string
        :param prefix: Naming prefix for the newly-added columns (DEFAULT 'dt_whois.')
        :type prefix: string
        :param progress_bar: If True, attempt to show enrichment progress (DEFAULT False)
        :type progress_bar: bool
        :param fields: A list of specific enrichment field names to add (DEFAULT add all fields)
        :type fields: list of strings
        :param batch_size: The number of domains/IPs to enrich in one "batch" (DEFAULT 100)
        :type batch_size: integer

        :Return Value:

        A pandas DataFrame object containing all of the original information plus many 
        additional enrichment columns.

        :Exceptions:
        Raises ValueError if the required options are not present or are of the wrong type.

        '''

        if df is None:
            raise ValueError(
                "You must supply a pandas DataFrame in the 'df' parameter.")
        elif not isinstance(df, pd.core.frame.DataFrame):
            raise ValueError(
                "The argument for the 'df' parameter must be a pandas DataFrame.")

        if not column:
            raise ValueError("You must supply a column name to enrich.")
        elif not isinstance(column, str):
            raise ValueError("The column name must be a 'str'.")
        elif not column in df.columns:
            raise ValueError(
                f"The column '{column}' does not exist in the frame.")

        if prefix is None or not isinstance(prefix, str):
            raise ValueError("The column name prefix must be a 'str'.")

        if fields is not None and not isinstance(fields, list):
            raise ValueError(
                "The 'fields' parameter must be a list of strings.")

        # Attempt some basic deduplication to save API calls
        unique_domains = pd.Series(
            df[column].unique(),
            dtype='object'
        )

        if progress_bar:
            tqdm.pandas(desc='Enriching')

        enrichment_df = pd.DataFrame()

        with tqdm(desc="Enriching", total=unique_domains.size, disable=not progress_bar) as pbar:

            for batch in [unique_domains[i:i+batch_size] for i in range(0, unique_domains.size, batch_size)]:

                res = self.iris_enrich(
                    batch,
                    flatten=True,
                    asframe=True
                )

                # We have to do this the hard way, instead of just DataFrame(res)
                # because some of the items in res contain lists of unequal length,
                # which causes pandas to throw an exception.
                results = pd.DataFrame(
                    dict(
                        [(k, pd.Series(v, dtype='object')) for k,v in res.items()]
                    )
                )
                
                enrichment_df = enrichment_df.append(
                    results,
                    ignore_index=True
                )
            
                pbar.update(batch.size)

        enrichment_df = enrichment_df.add_prefix(prefix)

        # If we asked for only certain fields, filter for those
        if fields:
            if not f'{prefix}domain' in fields:
                # Make sure this is in the final fields list no matter what,
                # because we rely on it as a merge column below
                fields.append(f'{prefix}domain')
            enrichment_df = enrichment_df[fields]

        df = pd.merge(
            df,
            enrichment_df,
            how='left',
            left_on=column,
            right_on=f'{prefix}domain'
        )

        df = df.drop(f'{prefix}domain', axis='columns')

        return df
