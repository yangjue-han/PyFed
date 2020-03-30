# Test money_stock package
import os
os.chdir('/Users/yangjuehan/Documents/GitHub/fed_api')
import money_stock as ms
from FRB_H8 import *

get_data = ms.vendor()
H6 = get_data.FRED_H6()
H4_avg = get_data.FRED_H4_weeklyavg()
H4_wed = get_data.FRED_H4_asofwed()

h8 = H8()

list_of_columns = [] # a list of column names, one entry for each group
list_of_dataframes = [] # a list of dataframes, one entry for each group

for p in [1,2,3]:
    cols = [] # column names
    list_of_ts = [] # ts objects
    group = h8.pages[p].category
    page = h8.pages[p].value
    print("{}) Page for {}.".format(p,group))
    N_ts = len(page) # number of ts objects
    print("The number of items in this page is {}.".format(N_ts))
    print('\n')
    for i in range(N_ts):
        ts = page[i]
        cols.append(ts.name)
        list_of_ts.append(ts.value)

    df = list_of_ts[0]
    for ts in list_of_ts[1:]:
        df = df.merge(ts,left_index=True,right_index=True,how='outer')

    list_of_columns.append(cols)
    list_of_dataframes.append(df)
