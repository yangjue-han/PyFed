# basic packages
import os
import csv
import urllib
import datetime
import functools
from datetime import date

# analysis packages
import pandas as pd
import numpy as np
import scipy.interpolate as interp
from pandas.tseries.offsets import BMonthEnd

# plotting packages
import seaborn as sns
import matplotlib.pyplot as plt

# other data piplelines
import quandl as ql
ql.ApiConfig.api_key = "kzRLWtzrpzxLvSt-Hzo4"
from fredapi import Fred

class vendor:

    def __init__(self):

        self.fred_api = Fred(api_key='4784f4ab3b06abdc6c8cbdfa4c7825db')

    def dtcc_gcf(self):

        # current dataset, the data contains daily time series of the past year
        gcf_current_url = 'https://www.dtcc.com/data/gcfindex.csv'
        gcf_current = pd.read_csv(gcf_current_url,skipfooter=2, engine='python')
        #gcf_current.to_csv(os.getcwd() + '/data/interest rates/gcf_current.csv')

        gcf_current = gcf_current.rename(
                columns = {
                    'MBS Total PAR Value': 'gcf_vol_mbs',
                    'MBS Weighted Average': 'gcf_rate_mbs',
                    'Treasury Total PAR Value': 'gcf_vol_tsy',
                    'Treasury Weighted Average': 'gcf_rate_tsy'
                }
            )

        gcf_current['Date'] = pd.to_datetime(gcf_current['Date'],format = '%m/%d/%Y' )
        gcf_current.set_index('Date', inplace=True)

        # historical dataset
        gcf_hist_url = 'http://dtcc.com/data/GCF_Index_Graph.xlsx'
        gcf_hist = pd.read_excel(gcf_hist_url, skiprows=6)
        #gcf_hist.to_csv(os.getcwd() + '/data/interest rates/gcf_hist.csv')

        gcf_hist = gcf_hist[['Date', 'MBS GCF Repo® \nWeighted Average Rate',
               'Treasury GCF Repo® \nWeighted \nAverage Rate',
               'Agency GCF Repo® \nWeighted \nAverage Rate']].rename(
            columns = {
                'MBS GCF Repo® \nWeighted Average Rate':'gcf_rate_mbs',
                'Treasury GCF Repo® \nWeighted \nAverage Rate': 'gcf_rate_tsy',
                'Agency GCF Repo® \nWeighted \nAverage Rate': 'gcf_rate_agency'
            }
        ).set_index('Date')

        gcf_hist.index = pd.to_datetime(gcf_hist.index,format = '%Y-%m-%d')

        # so far the historical dataset extends to 2019-12-31, needs to be updated next year
        gcf = pd.DataFrame(
            columns=['gcf_tsy','gcf_mbs'],
            index= pd.date_range(start="2005-01-01", end=gcf_current.index[-1])
        )
        gcf.loc[gcf_hist.index,'gcf_tsy'] = gcf_hist['gcf_rate_tsy'].copy()
        gcf.loc[gcf_hist.index,'gcf_mbs'] = gcf_hist['gcf_rate_mbs'].copy()
        gcf.loc['2020-01-01':,'gcf_tsy'] = gcf_current['gcf_rate_tsy']['2020-01-01':]
        gcf.loc['2020-01-01':,'gcf_mbs'] = gcf_current['gcf_rate_mbs']['2020-01-01':]
        gcf=gcf[gcf.index.dayofweek<5] # keep only business days

        gcf.to_csv(os.getcwd() + '/data/interest rates/gcf.csv')

        return gcf

    def fed_repo(self, output = 'both'):

        '''
        Repo and reverse repo operations conducted by Fed, daily frequency.

        The data is identified by Op ID, with each Op ID assigned to an operation
            - Each operation has a single auction methods (e.g. single price, fixed-rate,
                or multiple price), a single term, but different types of collateral.
            - Principal amounts and rates are recorded at the operation-collateral level

        Auction method:
            - If the auction method is fixed-rate or single, then the rrp rate is in 'Tsy-Award'
            - If the auction method is multiple price, then the rrp rate is in 'Tsy-Wght Avg'
                if we are interested in the weighted average, or 'Stop-Out' if we are interested
                in the highest bid (the stop out rate is the highest rate accepted in a reverse repo).
        '''
        
        
        today = datetime.date.today() # pin down the date for today
        
        fedrrp_url='https://websvcgatewayx2.frbny.org/autorates_tomo_external/services/v1_0/tomo/retrieveHistoricalExcel?f=07072000&t={}&ctt=true&&cta=true&ctm=true'.format(today.strftime("%m%d%Y"))
        fed_op = pd.read_excel(fedrrp_url)
        fed_op['Deal Date']=pd.to_datetime(fed_op['Deal Date'], format = '%m/%d/%Y')
        fed_op.columns

        stubs = ['Submit','Accept','Stop-Out','Award','Wght Avg','High','Low','PctAtStopOut']
        collateral = ['Tsy','Agy','MBS']
        suffix_mover = {}
        for x in collateral:
            for y in stubs:
                suffix_mover[x+'-'+y] = y+'-'+x
        fed_op = fed_op.rename(columns = suffix_mover)
        identifier = ['Op ID', 'Deal Date', 'Delivery Date', 'Maturity Date', 'Op Type',
               'Auction Method', 'Settlement', 'Term-BD', 'Term-CD', 'Op Close',
               'Participating Counterparties', 'Accepted Counterparties',
               'Total-Submit', 'Total-Accept']
        fed_op = pd.wide_to_long(fed_op, stubnames = stubs, i = identifier, j = 'collateral', sep = '-', suffix='\w+')
        fed_op.reset_index(inplace=True)

        # define effective rate
        single_rate = (fed_op['Auction Method']=='Fixed-Rate') | (fed_op['Auction Method']=='Single Price')
        multiple_rate = (fed_op['Auction Method']=='Multiple Price')
        fed_op.loc[single_rate,'Effective Rate'] = fed_op[single_rate]['Award']
        fed_op.loc[multiple_rate,'Effective Rate'] = fed_op[multiple_rate]['Wght Avg']

        # Daily volume by collateral
        fed_op['acc_rate'] = fed_op['Accept'].divide(fed_op['Submit'])

        # Operations volume
        fed_op_vol = fed_op.groupby(
            ['Deal Date','collateral','Op Type']
        ).sum()[['Submit','Accept']].unstack().unstack()['Accept']
        fed_op_vol = fed_op_vol[['RP','RRP']]

        # Operations rate
        fed_op_rate = fed_op.groupby(
            ['Deal Date','collateral','Op Type']
        ).mean()[['Effective Rate']].unstack().unstack()['Effective Rate']
        fed_op_rate = fed_op_rate[['RP','RRP']]

        fed_op_rate.to_csv(os.getcwd() + '/data/interest rates/fed_op_rate.csv')
        fed_op_vol.to_csv(os.getcwd() + '/data/interest rates/fed_op_vol.csv')

        if output == 'both':
            return fed_op_rate, fed_op_vol
        elif output == 'rate':
            return fed_op_rate
        elif output == 'vol':
            return fed_op_vol
