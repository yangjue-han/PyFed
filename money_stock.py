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
        return None

    def FRED_H4_asofwed(self):

        """
        Federal Reserve Board H4 Table
        ----------------------------------
        Units: Millions USD,
        Frequency: weekly, as of Wednesday
        ----------------------------------
        Variables:
        * WLRRAOL: Fed RRP with MMF
        * WLRRAFOIAL: Fed RRP with foreign officials
        * WRBWFRBL: Reserve balances with the Fed
        * WDTGAL: TGA
        * WTFSRFL: Total factors supplying reserve funds

        """

        keys = ['WLRRAOL','WLRRAFOIAL','WRBWFRBL','WDTGAL','WTFSRFL']
        names = ['fedrrp_mmf','fedrrp_fo','res_bal','tga','tot_res']
        fred_list = [self.fred_api.get_series(x) for x in keys]
        df = pd.DataFrame(dict(zip(names,fred_list)))/1000

        return df


    def FRED_H4_weeklyavg(self):

        """
        Federal Reserve Board H4 Table
        ----------------------------------
        Units: Million USD,
        Frequency: weekly averages
        ----------------------------------
        * WTFSRFA: Total factors supplying reserve funds
        * WREPOFOR: Fed RRP with Foreign Official
        * WREPODEL: Fed RRP with MMF

        ----------------------------------
        Units: Billion USD,
        Frequency: weekly averages
        ----------------------------------
        * WCURCIR: currency in circulation
        * WTREGEN: TGA
        * WOTHLB: Other deposits (international orgnizations, GSE balances)
        * WRESBAL: Reserve balances with the Fed
        """

        keys = ['WTFSRFA','WREPOFOR','WREPODEL']
        names = ['tot_res','fedrrp_fo','fedrrp_mmf']
        fred_list = [self.fred_api.get_series(x) for x in keys]
        df1 = pd.DataFrame(dict(zip(names,fred_list)))/1000

        keys = ['WCURCIR','WTREGEN','WOTHLB','WRESBAL']
        names = ['cur_in_cir','tga','gse_bal','res_bal']
        fred_list = [self.fred_api.get_series(x) for x in keys]
        df2 = pd.DataFrame(dict(zip(names,fred_list)))

        df=df1.merge(df2, left_index=True,right_index=True,how='outer')

        return df

    def FRED_H6(self):

        """
        Federal Reserve Board H6 Table
        ----------------------------------
        Units: Billion USD,
        Frequency: weekly, as of Monday
        ----------------------------------
        * WRMFNS: retail money funds
        * WIMFNS: institutinoal money funds
        * WSMTMNS: small time deposits
        * WDDNS: demand deposits
        * WOCDNS: Other checkable deposits
        * WSAVNS: total savings deposits
        """

        keys = ['WRMFNS','WIMFNS','WSMTMNS','WDDNS','WOCDNS','WSAVNS']
        names = ['mmf_retail','mmf_inst','dep_small_time','dep_demand','dep_other_checkable','dep_savings']
        fred_list = [self.fred_api.get_series(x) for x in keys]
        df = pd.DataFrame(dict(zip(names,fred_list)))

        return df

    def FoF(self):

        FoF_house_ID, FoF_house_Name = read_ID('FoF_Households_README.txt')
        FoF_firm_ID, FoF_firm_Name = read_ID('FoF_Firms_README.txt')
        fred_ID = FoF_house_ID + FoF_firm_ID
        fred_name = FoF_house_Name + FoF_firm_Name
        FRED_FoF = api.database('fred','4784f4ab3b06abdc6c8cbdfa4c7825db', fred_ID)

        # Household financial assets
        House_FA = ['CDCABSHNO', 'TSDABSHNO', 'MMFSABSHNO', 'SCABSHNO', 'FDABSHNO',
                  'CFBABSHNO', 'CMIABSHNO',
                  'HNOCEA', 'HNOMFSA',
                  'HNOREMV', 'HOOREVLMHMV', 'OEHRENWBSHNO']

        # Firm financial asset
        Firm_FA = ['AGSEBSABSNNCB', 'CCABSNNCB', 'CPABSNNCB', 'MMFSABSNNCB', 'NCBCDCA', 'FDABSNNCB',
                   'NCBMFSA', 'MABSNNCB', 'MAABSNNCB',
                   'SRPSABSNNCB', 'TSABSNNCB', 'TSDABSNNCB', 'TRABSNNCB', 'TFAABSNNCB', 'TTAABSNNCB']

        # Firm's liabilities
        Firm_liab = ['BLNECLBSNNCB', 'CBLBSNNCB', 'CPLBSNNCB', 'NCBCEL', 'TCMILBSNNCB', 'TXPLBSNNCB', 'TNWMVBSNNCB']
        House_LM = ['CDCABSHNO', 'MMFSABSHNO']
        Firm_LM = ['MMFSABSNNCB', 'NCBCDCA', 'FDABSNNCB','SRPSABSNNCB']

        return FoF, House_FA, Firm_FA, Firm_liab, House_LM, Firm_LM, fred_ID, fred_name


    def read_ID(self,filename):
        fp = open(filename)
        ID = []
        Name = []
        series = 0
        title = 0
        for line in fp:
            series = series - 1
            title = title - 1
            if line.strip() == "Series ID":
                series = 2
            if series == 0:
                ID.append(line.strip())
            if line.strip() == "Title":
                title = 2
            if title == 0:
                Name.append(line.strip())
        return ID, Name
