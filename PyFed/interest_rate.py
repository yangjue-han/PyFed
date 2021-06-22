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
        self.rootdir = os.getcwd()

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
        current_start_date = '{}-01-01'.format(date.today().year)
        gcf = pd.DataFrame(
            columns=['gcf_tsy','gcf_mbs'],
            index= pd.date_range(start="2005-01-01", end=gcf_current.index[-1])
        )
        gcf.loc[gcf_hist.index,'gcf_tsy'] = gcf_hist['gcf_rate_tsy'].copy()
        gcf.loc[gcf_hist.index,'gcf_mbs'] = gcf_hist['gcf_rate_mbs'].copy()
        gcf.loc[current_start_date:,'gcf_tsy'] = gcf_current['gcf_rate_tsy'][current_start_date:]
        gcf.loc[current_start_date:,'gcf_mbs'] = gcf_current['gcf_rate_mbs'][current_start_date:]
        gcf=gcf.resample('b').last().ffill() # keep only business days

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

        fed_op_rate.to_csv(os.path.join(os.getcwd(),'data/interest rates/fed_op_rate.csv'))
        fed_op_vol.to_csv(os.path.join(os.getcwd(),'data/interest rates/fed_op_vol.csv'))

        if output == 'both':
            return fed_op_rate, fed_op_vol
        elif output == 'rate':
            return fed_op_rate
        elif output == 'vol':
            return fed_op_vol

    def remove_prime(self,x):
        if len(x)>3:
            x = x[:-4]+x[-3:]
        return float(x)

    def nyfed_repo_indices(self):
        #################################################################
        # Tri-party, GCF, and Bilateral repo markets, NY Fed
        #################################################################
        today = datetime.date.today() # pin down the date for today
        date_index = pd.bdate_range(start="1950-01-01", end=today.strftime("%Y-%m-%d"))
        url = "https://websvcgatewayx2.frbny.org/mktrates_external_httponly/services/v1_0/mktRates/excel/retrieve?multipleRateTypes=true&startdate=04022018&enddate={}&rateType=R1%2cR2%2cR3".format(today.strftime("%m%d%Y"))
        repo = pd.read_excel(url, skiprows = 3, skipfooter = 7)
        colnames = ['Date', 'Index', 'Repo Rate', 'RP: 1st', 'RP: 25th', 'RP: 75th', 'RP: 99th', 'RP: Vol']
        repo = repo.rename(columns = dict(zip(repo.columns,colnames)))
        repo.head()
        ######################
        # repo rates, current
        ######################
        reporates = repo.groupby(['Date', 'Index']).mean().unstack('Index')['Repo Rate']
        reporates.index = pd.to_datetime(list(map(lambda x: x.strip()[:10] , reporates.index.values)))
        reporates.index.name=None
        ############################################
        # repo rates, historical 2014-2018.4.2
        ###########################################
        reporates_hist = pd.read_excel(os.path.join(self.rootdir,'data/interest rates/NYFed_repo_hist.xlsx'),
                                       sheet_name = 'VWM Rates', header = 1, usecols = [0,1,2,3])
        colnames = ['Date', 'TGCR', 'BGCR', 'SOFR']
        reporates_hist = reporates_hist.rename(columns = dict(zip(reporates_hist.columns,colnames)))
        reporates_hist.set_index('Date', inplace = True)
        reporates_hist = reporates_hist.divide(100)
        ############################################
        # combine two repo rates
        ############################################
        rp = pd.DataFrame()
        for x in reporates.columns:
            rp[x] = pd.concat([reporates[x],reporates_hist[x]])
        rp.sort_index(inplace = True)
        #sum(rp.index.duplicated())>0 #check whether there is duplicated values in the index
        rp=rp.reindex(index=date_index).ffill() # resample to business day and fill missing values
        rp=rp.astype(float).interpolate(method = 'linear',limit_area='inside').dropna(how='all')
        ########################################
        # Repo volume, current
        ########################################
        repo['RP: Vol'] = repo['RP: Vol'].apply(self.remove_prime)
        repovol = repo.groupby(['Date', 'Index']).mean().unstack('Index')['RP: Vol']
        repovol.index = list(map(lambda x: x.strip()[:10] , repovol.index.values))
        repovol.index = pd.to_datetime(repovol.index)
        #############################################################
        # Repo volume historical 2014-2018.4.2
        ###########################################
        repovol_hist = pd.read_excel(os.path.join(self.rootdir,'data/interest rates/NYFed_repo_hist.xlsx'),
                                    sheet_name = 'Volumes', header = 1, usecols = [0,1,2,3])
        colnames = ['Date', 'TGCR', 'BGCR', 'SOFR']
        repovol_hist = repovol_hist.rename(columns = dict(zip(repovol_hist.columns,colnames)))
        repovol_hist.set_index('Date', inplace = True)
        ########################################
        # combine two repo volumes
        ########################################
        rpvol = pd.DataFrame()
        for x in repovol.columns:
            rpvol[x] = pd.concat([repovol[x],repovol_hist[x]])
        rpvol.sort_index(inplace = True)
        rpvol.rename(columns = dict(zip(rpvol.columns, [x + '_vol' for x in rpvol.columns])), inplace = True)
        sum(rpvol.index.duplicated())>0 #check whether there is duplicated values in the index
        rpvol=rpvol.reindex(index=date_index).ffill()
        rpvol=rpvol.astype(float).interpolate(method = 'linear',limit_area='inside').dropna(how='all')

        return rp, rpvol
