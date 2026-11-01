#!/usr/bin/env python3
"""Print low and high tide times (with heights and coefficients) at
Saint-Malo for every day of the current month, and plot the month's
tide curve with moon-phase markers.

Uses the api-maree.fr REST API, which redistributes official SHOM tide
predictions. Get a free API key at https://api-maree.fr and set it via
the API_MAREE_KEY environment variable.

Usage:
    python saint_malo_tides.py
"""

import calendar
import os
import sys
import json
import urllib.parse
import urllib.request
from datetime import date, datetime

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import ephem
from matplotlib.patches import Ellipse

API_BASE = "https://api-maree.fr"
SITE = "saint-malo"          # site slug; see GET /sites for the full list
TIMEZONE = "Europe/Paris"    # France is UTC+1/+2


def get_api_key() -> str:
    key = os.environ.get("API_MAREE_KEY", "1293ff9183dcc86dc9335a0564b5ded3")
    if not key:
        sys.exit("No API key. Set the API_MAREE_KEY environment variable "
                 "(free key: https://api-maree.fr)")
    return key


def tide_extrema(day1, day2, key: str) -> list:
    """Return the tide extrema (PM = high, BM = low) from day1 to day2."""
    params = urllib.parse.urlencode({
        "site": SITE,
        "from": day1.isoformat(),   # has to be in a 'YYYY-MM-DD' format
        "to": day2.isoformat(),     # has to be in a 'YYYY-MM-DD' format
        "tz": TIMEZONE,
        "key": key,
    })
    url = f"{API_BASE}/tide-extrema?{params}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        payload = json.load(resp)
    return payload


def main():
    t = date.today()
    month = t.month
    year = t.year

    # number of days in the current month (handles leap years)
    dayMax = calendar.monthrange(year, month)[1]

    day1 = date(year, month, 1)
    day2 = date(year, month, dayMax)

    extrema = tide_extrema(day1, day2, get_api_key())

    DATA, DATA_t, DATA_m = [], [], []

    for k in range(dayMax):
        print("Tides at Saint-Malo on {}-{}-{}".format(k + 1, month, year))
        dataframe = extrema["data"][k]["extrema"]
        for e in dataframe:
            label = {"PM": "High tide", "BM": "Low tide"}
            typ = label.get(e["type"], e["type"])
            coeff = f", coefficient {e['coefficient']}" if e.get("coefficient") else ""
            print(f"  {e['time']}  {typ:8s}  {e['height']:.2f} m{coeff}")
            tide_time = datetime.fromisoformat(
                '{:04d}-{:02d}-{:02d}T{}:00'.format(year, month, k + 1, e['time']))
            DATA.append(e['height'])
            DATA_t.append(tide_time)
            moon = ephem.Moon(tide_time)
            DATA_m.append(moon.phase)

    # convert to numpy arrays for plotting and argmax/argmin
    DATA = np.array(DATA)
    DATA_t = np.array(DATA_t, dtype="datetime64[s]")
    DATA_m = np.array(DATA_m)

    return DATA, DATA_t, DATA_m


if __name__ == "__main__":

    plt.close('all')

    t = date.today()
    month = t.month
    year = t.year

    mois = np.array([
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
    ])

    DATA, DATA_t, DATA_m = main()

    fig, ax = plt.subplots(figsize=(16, 4))
    ax.plot(DATA_t, DATA, "k-")
    ax.scatter(DATA_t, DATA, c="red", zorder=3)

    # moon markers: white circle at fullest moon, black circle at darkest
    circle = Ellipse((DATA_t[np.argmax(DATA_m)], 15), width=1, height=2,
                     edgecolor='black', facecolor='white', linewidth=2)
    ax.add_patch(circle)
    circle = Ellipse((DATA_t[np.argmin(DATA_m)], 15), width=1, height=2,
                     edgecolor='black', facecolor='black')
    ax.add_patch(circle)

    ax.set_ylabel('marnage (m)')
    ax.set_title('Marées - Saint-Malo - {} {}'.format(mois[month - 1], year))
    plt.show()

# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Created on Fri Oct 30 12:40:42 2026

# @author: carlotal
# """


# #!/usr/bin/env python3
# """Print low and high tide times (with heights and coefficients) at
# Saint-Malo for a given day.

# Uses the api-maree.fr REST API, which redistributes official SHOM tide
# predictions. Get a free API key at https://api-maree.fr and set it below
# (or via the API_MAREE_KEY environment variable).

# Usage:
#     python saint_malo_tides.py 2026-11-05
#     python saint_malo_tides.py                 # -> today
# """

# import os
# import sys
# import json
# import urllib.parse
# import urllib.request
# from datetime import date, datetime
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import ephem
# from matplotlib.patches import Ellipse

# API_BASE = "https://api-maree.fr"
# SITE = "saint-malo"          # site slug; see GET /sites for the full list
# TIMEZONE = "Europe/Paris"    # France is UTC+1/+2


# def get_api_key() -> str:
#     key = os.environ.get("API_MAREE_KEY", "1293ff9183dcc86dc9335a0564b5ded3")
#     if not key:
#         sys.exit("No API key. Set the API_MAREE_KEY environment variable "
#                  "or hardcode it in the script (free key: https://api-maree.fr)")
#     return key

# def tide_extrema(day1, day2, key: str) -> list:
#     """Return the list of tide extrema (PM = high, BM = low) for `day`."""
#     params = urllib.parse.urlencode({
#         "site": SITE,
#         "from": day1.isoformat(),
#         "to": day2.isoformat(),
#         "tz": TIMEZONE,
#         "key": key,
#     })
#     url = f"{API_BASE}/tide-extrema?{params}"
#     with urllib.request.urlopen(url, timeout=30) as resp:
#         payload = json.load(resp)
#     return payload

# def main():
    
#     t = date.today()
#     month = t.month
#     year = t.year
    
#     if month == 2:
#         dayMax = 28
#     elif np.mod(month,2)==1:
#         dayMax = 30
#     else:
#         dayMax = 31
    
#     day1 = date.fromisoformat('{}-{}-01'.format(year,month))# has to be in a 'YYYY-MM-DD' format
#     day2 = date.fromisoformat('{}-{}-{}'.format(year,month,dayMax))# has to be in a 'YYYY-MM-DD' format

#     DATA = []
#     DATA_t = []
#     DATA_m = []
    
#     extrema = tide_extrema(day1, day2, get_api_key())
    
#     cc=0
    
#     for k in range(dayMax):
        
          
        
#         label = {"PM": "High tide", "BM": "Low tide"}
#         # print(f"Tides at Saint-Malo on {day.strftime('%d %B %Y')} ({TIMEZONE}):")
#         print("Tides at Saint-Malo on {}-{}-{}".format(k+1,month,year))
#         dataframe = extrema["data"][k]["extrema"]
#         for e in dataframe:
#             typ = label.get(e["type"], e["type"])
#             coeff = f", coefficient {e['coefficient']}" if e.get("coefficient") else ""
#             print(f"  {e['time']}  {typ:8s}  {e['height']:.2f} m{coeff}")
#             DATA=np.append(DATA,e['height'])
#             DATA_t=np.append(DATA_t,datetime(year,month,k+1,int(e['time'][:2]),int(e['time'][3:5])))
#             moon = ephem.Moon(datetime.fromisoformat('{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:00'.format(year,month,k+1,int(e['time'][:2]),int(e['time'][3:5]))))
#             DATA_m = np.append(DATA_m,moon.phase) 
#             cc+=1
#     return DATA, DATA_t, DATA_m

# if __name__ == "__main__":  
    
#     plt.close('all')
#     patches = []
    
#     t = date.today()
#     month = t.month
#     year = t.year
    
#     mois = np.array([
#     "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
#     "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
#     ])
    
#     DATA, DATA_t, DATA_m=main()
#     # L=len(DATA)
#     # idx_odd = np.mod(np.arange(L),2)==1
#     # idx_even = np.mod(np.arange(L),2)==0
    
#     fig,ax = plt.subplots(figsize=(16,4))
#     ax.plot(DATA_t, DATA, "k-")
#     # plt.plot(DATA_t[idx_odd], DATA[idx_odd],color='red')
#     # plt.plot(DATA_t[idx_even], DATA[idx_even],color='red')
#     ax.scatter(DATA_t,DATA,c="red", zorder=3)
#     # plt.scatter(DATA_t[np.argmax(DATA_m)],15,c='black',marker='o',s=200)
#     # plt.scatter(DATA_t[np.argmin(DATA_m)],15,c='white',marker=r'$\odot$',s=200)
#     circle = Ellipse((DATA_t[np.argmax(DATA_m)],15), width=1,height=2,edgecolor='black',facecolor='white',linewidth=2)
#     ax.add_patch(circle)
#     circle = Ellipse((DATA_t[np.argmin(DATA_m)],15), width=1,height=2,edgecolor='black',facecolor='black')
#     ax.add_patch(circle)
#     #plt.xlabel('Date (YYYY-MM-DD)')
#     ax.set_ylabel('marnage (m)')
#     ax.set_title('Marées - Saint-Malo - {} {}'.format(mois[month-1],year))
    
#     # times = [datetime(2026, 11, 5, 6, 12), datetime(2026, 11, 5, 9, 0),
#     # datetime(2026, 11, 5, 12, 45), datetime(2026, 11, 5, 18, 30)]
#     # heights = [11.8, 7.2, 2.1, 6.5]

#     # fig, ax = plt.subplots()
#     # ax.plot(times, heights, marker="o")