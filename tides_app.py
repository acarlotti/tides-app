"""Saint-Malo tides web app (Streamlit) — monthly view with moon-phase markers.

Run locally:
    pip install streamlit requests matplotlib numpy ephem
    streamlit run tides_app.py

Deploy (free):
    Push this file to a GitHub repo (public) with a requirements.txt, then
    deploy at https://share.streamlit.io (or a Hugging Face Space, SDK:
    Streamlit). Add your api-maree.fr key in app Settings -> Secrets:
        API_MAREE_KEY = "your-key"
"""

import calendar
import os
from datetime import date, datetime

import ephem
import matplotlib.pyplot as plt
import numpy as np
import requests
import streamlit as st
from matplotlib.patches import Ellipse

st.set_page_config(page_title="Marées — Saint-Malo", page_icon="🌊")

API_BASE = "https://api-maree.fr"
SITE = "saint-malo"          # site slug; see GET /sites for the full list
TIMEZONE = "Europe/Paris"    # France is UTC+1/+2

MOIS = np.array([
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
])

LABEL = {"PM": "High tide", "BM": "Low tide"}


@st.cache_data(show_spinner=False)
def tide_extrema(day1: date, day2: date, key: str) -> dict:
    """Return the tide extrema (PM = high, BM = low) from day1 to day2."""
    r = requests.get(
        f"{API_BASE}/tide-extrema",
        params={
            "site": SITE,
            "from": day1.isoformat(),   # has to be in a 'YYYY-MM-DD' format
            "to": day2.isoformat(),     # has to be in a 'YYYY-MM-DD' format
            "tz": TIMEZONE,
            "key": key,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def collect_month(extrema: dict, month: int, year: int):
    """Collect heights, datetimes and moon phases for the whole month."""
    # number of days in the month (handles leap years)
    day_max = calendar.monthrange(year, month)[1]

    data, data_t, data_m = [], [], []

    for k in range(day_max):
        dataframe = extrema["data"][k]["extrema"]
        for e in dataframe:
            tide_time = datetime.fromisoformat(
                '{:04d}-{:02d}-{:02d}T{}:00'.format(year, month, k + 1, e['time']))
            data.append(e['height'])
            data_t.append(tide_time)
            moon = ephem.Moon(tide_time)
            data_m.append(moon.phase)

    # convert to numpy arrays for plotting and argmax/argmin
    data = np.array(data)
    data_t = np.array(data_t, dtype="datetime64[s]")
    data_m = np.array(data_m)
    data_c = np.diff(data.copy())/np.mean(data)*100
    data_c = np.append(data_c,data_c[-1])
    return data, data_t, data_m, data_c


# --- Sidebar: API key + month ---------------------------------------------
default_key = st.secrets.get("API_MAREE_KEY", "") if hasattr(st, "secrets") else ""
key = st.sidebar.text_input(
    "api-maree.fr API key",
    value=default_key or os.environ.get("API_MAREE_KEY", API_MAREE_KEY),
    type="password",
    help="Free key at https://api-maree.fr",
)

today = date.today()
month = st.sidebar.selectbox(
    "Mois",
    options=range(1, 13),
    index=today.month - 1,
    format_func=lambda m: MOIS[m - 1],
)
year = st.sidebar.number_input("Année", min_value=2020, max_value=2100, value=today.year, step=1)
run = st.sidebar.button("Afficher les marées", type="primary")


# --- Main panel -----------------------------------------------------------
st.title("🌊 Marées — Saint-Malo")
st.caption("Prévisions d'après les données SHOM, via api-maree.fr")

if run or st.session_state.get("ran"):
    st.session_state["ran"] = True

    if not key:
        st.error("Entrez votre clé api-maree.fr dans la barre latérale.")
        st.stop()

    # number of days in the requested month (handles leap years)
    day_max = calendar.monthrange(year, month)[1]
    day1 = date(year, month, 1)
    day2 = date(year, month, day_max)

    try:
        extrema = tide_extrema(day1, day2, key)
    except requests.HTTPError as e:
        st.error(f"Erreur API : {e} — vérifiez la clé et la plage de dates "
                 "(les prévisions couvrent environ ±1 an).")
        st.stop()

    data, data_t, data_m, data_c = collect_month(extrema, month, year)

    # --- tide table --------------------------------------------------------
    # st.subheader("Marées — {} {}".format(MOIS[month - 1], year))
    # rows = []
    # for k in range(day_max):
    #    for e in extrema["data"][k]["extrema"]:
    #        typ = LABEL.get(e["type"], e["type"])
    #        coeff = e.get("coefficient", "")
    #        rows.append({
    #            "Jour": "{:04d}-{:02d}-{:02d}".format(year, month, k + 1),
    #            "Heure": e["time"],
    #            "Type": typ,
    #            "Hauteur (m)": round(e["height"], 2),
    #            "Coefficient": coeff,
    #        })
    # st.dataframe(rows, use_container_width=True, height=400)

    # --- monthly curve with moon markers ------------------------------------
    
    fig, ax = plt.subplots(figsize=(16, 4))
    ax.plot(data_t, data, "k-")
    ax.scatter(data_t, data, c="red", zorder=3)

    # moon markers: white circle at fullest moon, black circle at darkest
    circle = Ellipse((data_t[np.argmax(data_m)], 16), width=1, height=2.5,
                     edgecolor='black', facecolor='white', linewidth=2)
    ax.add_patch(circle)
    circle = Ellipse((data_t[np.argmin(data_m)], 16), width=1, height=2.5,
                     edgecolor='black', facecolor='black')
    ax.add_patch(circle)

    ax.set_ylabel('Marnage (m)')
    ax.set_xaxis('off')
    ax.set_title('Marées - Saint-Malo - {} {}'.format(MOIS[month - 1], year))
    ax.set_ylim([-2,18])

    # --- monthly curve with moon markers ------------------------------------

    for k in range(len(data)):
        #dt = datetime.fromisoformat(data_t[k])
        dt = data_t[k].astype(datetime)
        hour_approximation = dt.hour+int(np.round(dt.minute/60))
        if data[k] > np.mean(data):
            offset = 1.2
        else:
            offset = -1.2
        ax.text(data_t[k], data[k]+offset, '{}\n{}h'.format(dt.day,hour_approximation), fontsize=7, color="navy",horizontalalignment='center',verticalalignment='center')
        
    st.pyplot(fig)
else:
    st.info("Entrez votre clé API dans la barre latérale, choisissez un mois, "
            "puis cliquez sur **Afficher les marées**.")

# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Created on Fri Oct 30 12:40:42 2026

# @author: carlotal
# """


# #!/usr/bin/env python3
# """ low and high tide times (with heights and coefficients) at
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
#         # (f"Tides at Saint-Malo on {day.strftime('%d %B %Y')} ({TIMEZONE}):")
#         # print("Tides at Saint-Malo on {}-{}-{}".format(k+1,month,year))
#         dataframe = extrema["data"][k]["extrema"]
#         for e in dataframe:
#             typ = label.get(e["type"], e["type"])
#             coeff = f", coefficient {e['coefficient']}" if e.get("coefficient") else ""
#             # print(f"  {e['time']}  {typ:8s}  {e['height']:.2f} m{coeff}")
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
