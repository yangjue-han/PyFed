# Test money_stock package
import os
os.chdir('/Users/yangjuehan/Documents/GitHub/fed_api')
import money_stock as ms
import FRB_H8
import plotly.express as px

# load the data vendor
get_data = ms.vendor()

# Load H6 table
H6 = get_data.FRED_H6()

fig = px.line(H6.reset_index(), x= 'index', y = ['mmf_retail','mmf_inst'])
fig.show()

H4_avg = get_data.FRED_H4_weeklyavg()
H4_avg.plot(figsize=(15,10))

H4_wed = get_data.FRED_H4_asofwed()
H8 = get_data.H8()

h8_api = FRB_H8.H8()
h8_api.info()

items = ['Cash assets',
         'Treasuries',
         'Total fed funds sold and reverse repo',
         'Loans to nondepository financial institutions']
H8[items].unstack()['2009':].plot(figsize=(20,6))
