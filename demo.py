import PyFed.money_stock as ms
import matplotlib.pyplot as plt
import importlib
importlib.reload(ms)

get_ms = ms.vendor()

cp = get_ms.FRED_CP()

cp
