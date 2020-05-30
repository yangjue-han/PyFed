# basic packages
import os
import functools
import csv
import urllib
import datetime
from datetime import date

# analysis packages
import pandas as pd
import numpy as np
import scipy.interpolate as interp
from pandas.tseries.offsets import BMonthEnd

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class ts:

    '''
    Time-series ("ts") objects are the basis of this database, representing
    a balance sheet item in H8 table.
    '''

    def __init__(self,
                 unit: str,
                 multiplier: int,
                 currency: str,
                 UI: str,
                 depth: int,
                 family: list,
                 value):
        self.unit = unit
        self.multiplier = multiplier
        self.currency = currency
        self.UI = UI
        self.depth = depth # the hierachy of item within the table
        self.family = family
        self.value = value
        self.name = family[depth]


class page:

    '''
    "page" object corresponds to a single sheet in the H8 table. For example,
    seasonally-adjusted data for large domestic banks.
    '''

    def __init__(self,
                 category: str,
                 sa: str,
                 value):

        self.category = category
        self.sa = sa  # seasonally-adjusted?
        self.value = value


class H8:

    '''
    Loading and parsing data from Federal Reserve Board H8 table.
    '''

    def __init__(self):
        '''
        At initialization, raw csv files are parsed into "ts" objects for each type of
        institution and aggregated as a book of pages.

        Raw data will further be transformed into easy-to-use format such as Dataframe.
        '''

        #super(frb_h8, self).__init__()

        # csv file urls for H8 tables
        all_nsa_w = 'https://www.federalreserve.gov/datadownload/Output.aspx?rel=H8&series=2f71e49efe1992f5ed44db0a0e9b1df5&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn&type=package'
        large_dom_nsa_w = 'https://www.federalreserve.gov/datadownload/Output.aspx?rel=H8&series=9c63d449a29567bd0b2f67dfb9365663&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn&type=package'
        small_dom_nsa_w = 'https://www.federalreserve.gov/datadownload/Output.aspx?rel=H8&series=15eff2a9a5b8fbc8f3115a60b2af1cb8&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn&type=package'
        for_nsa_w = 'https://www.federalreserve.gov/datadownload/Output.aspx?rel=H8&series=4071e886104457c921ccb0b3d2669c7e&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn&type=package'

        self.urls = [all_nsa_w,large_dom_nsa_w,small_dom_nsa_w,for_nsa_w]
        self.pages = []

        for path in self.urls:

            df = pd.read_csv(path)
            col_names = df.columns.values
            category, sa = col_names[1].split(',')[-2:]
            category = category.strip().title()

            if sa.split(' ')[1] == 'not':
                sa = 'NSA'
            else:
                sa = 'SA'

            ts_list = []

            # securities
            col_names[2] = 'Bank credit: Securities in bank credit'
            col_names[3] = 'Bank credit: Securities in bank credit: ' + col_names[3]
            col_names[4] = 'Bank credit: Securities in bank credit: Treasury and agency securities: Agency MBS'
            col_names[5] = 'Bank credit: Securities in bank credit: Treasury and agency securities: Treasuries'
            col_names[6] = 'Bank credit: Securities in bank credit: ' + col_names[6]
            col_names[7] = 'Bank credit: Securities in bank credit: Other securities: Non-Agency MBS'
            col_names[8] = 'Bank credit: Securities in bank credit: Other securities: Securities other than MBS or Treasuries'

            # loans
            col_names[9] = 'Bank credit: ' + col_names[9]
            col_names[25] = 'All other loans and leases'
            col_names[26] = 'All other loans and leases: Loans to nondepository financial institutions'
            col_names[27] = 'All other loans and leases: Other loans not elsewhere classified'

            for iname in range(10, 28):
                col_names[iname] = 'Bank credit: Loans and leases in bank credit: ' \
                    + col_names[iname]


            col_names[28] = 'Bank credit: (Less) Allowance for loan and lease losses'
            col_names[30] = 'Total fed funds sold and reverse repo'
            col_names[35] = 'Deposits: ' + col_names[35]
            col_names[36] = 'Deposits: ' + col_names[36]

            df.columns = col_names

            for col in col_names[1:]:
                family = col.split(',')[0].split(':')
                family = list(map(lambda x: x.strip(), family))

                depth = len(family) - 1

                unit = df.loc[df[col_names[0]] == 'Unit:', col].values[0]

                multiplier = df.loc[df[col_names[0]] == 'Multiplier:',
                                    col].values[0]

                currency = df.loc[df[col_names[0]] == 'Currency:',
                                  col].values[0]

                UI = df.loc[df[col_names[0]] ==
                            'Unique Identifier: ', col].values[0]
                UI = UI.split('/')[-1]

                value = df.loc[5:, [col_names[0], col]]
                value.columns = ['Date', family[depth]]
                value['Date'] = pd.to_datetime(value['Date'], yearfirst=True)
                value[family[depth]] = value[family[depth]].astype(float)
                value.set_index('Date', inplace=True)

                ts_list.append(ts(unit=unit, multiplier=multiplier,
                                  currency=currency, UI=UI,
                                  depth=depth, family=family,
                                  value=value))
            pg = page(category=category, sa=sa, value=ts_list)
            self.pages.append(pg)

        # Combine different pages into a single dataframe using the "combine" method (defined below).

        variables = [ts.name for ts in self.pages[1].value]
        self.book = self.combine(self.pages[1:],variables).swaplevel(axis=1).stack()

    def info(self):
        for page in self.pages:
            page_header = page.category + ', ' + page.sa
            tsname_list = ['{}: {}{}'.format(ts.UI, ts.depth * '\t', ts.name)
                           for ts in page.value]
            page_body = '\n'.join(tsname_list)

            print(color.BOLD + color.RED + page_header + color.END)
            print(page_body)
            print('\n')

    def search(self, page, tsname: str):
        i_ts = 0
        for i, ts in enumerate(page.value):
            if ts.name == tsname:
                i_ts = i
        return i_ts

    def combine(self, pages, terms):
        '''
        Combine given pages and variables into a single dataframe with MultiIndex.
        '''

        n = 0
        levels = [(a.category.split(' ')[0], b) for a in pages for b in terms]
        columns = pd.MultiIndex.from_tuples(levels, names=['page', 'ts'])

        for p in pages:
            tslist = [ p.value[self.search(p,name)].value for name in terms]
            _f = lambda x, y: pd.merge(x, y, left_index=True, right_index=True, how='outer')
            tempdf = functools.reduce(_f,tslist)

            if n == 1:
                df = df.merge(tempdf, left_index=True,right_index=True, how='outer')
            else:
                df = tempdf
            n = 1

        df.columns = columns

        return df
