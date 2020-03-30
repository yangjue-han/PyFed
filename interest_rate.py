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
