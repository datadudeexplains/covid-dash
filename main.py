import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import toml

dt_fmt = "%d/%m/%Y"
url = toml.load('dash-covid.toml')['url']
now = datetime.now()
# population = {
#     'Bulgaria': 6948445,
#     'Spain': 46754778,
#     'Israel':  8841083,
#     'Portugal': 10196709
# }
population = toml.load('population.toml')


def get_data():
    _ = pd.read_csv(url)

    cols = {
            'Country/Region': 'Country',
            'Province/State': 'State'
    }

    for d in _.columns[4:]:
        cols[d] = datetime.strptime(d, "%m/%d/%y").strftime(dt_fmt)
    _ = _.rename(columns=cols)

    return _


def by_country(country):

    b = df.query("Country.str.contains('{}')".format(country)).\
        drop(['State', 'Country', 'Lat', 'Long'], axis=1).T
    b.reset_index(inplace=True)
    b = b.rename(columns={
            'index': 'Date',
            b.columns[1]: 'Cumulative'
        })
    b['Date'] = pd.to_datetime(b.Date.astype(str), format='%d/%m/%Y')
    b['Daily'] = b['Cumulative'].diff()

    return b


def gen_graph(which):
    s = by_country('Spain')
    b = by_country('Bulgaria')

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    if which == 'daily':
        fig.add_trace(
            go.Bar(x=s.Date, y=s.Daily, name="Spain"),
            secondary_y=False,
        )

        fig.add_trace(
            go.Bar(x=b.Date, y=b.Daily, name='Bulgaria'),
            secondary_y=True,
        )

        fig.update_layout(
            title=f"Daily cases for Spain and Bulgaria"
        )
    else:
        fig.add_trace(
            go.Bar(x=s.Date, y=s.Cumulative, name="Spain"),
            secondary_y=False,
        )

        fig.add_trace(
            go.Bar(x=b.Date, y=b.Cumulative, name='Bulgaria'),
            secondary_y=True,
        )

        fig.update_layout(
            title=f"Cumulative cases for Spain and Bulgaria"
        )
    return fig


def fmt(d):
    return d.strftime(dt_fmt)


def get_windowed_graph(country, num_weeks=24):
    c = by_country(country)

    # find previous Monday
    d_max = max(c.Date).date()
    mon = (d_max - timedelta(days=d_max.weekday()))
    st_date = mon - timedelta(weeks=num_weeks)
    # print(st_date, mon)
    fil = c.query("Date >= '{}' & Date <= '{}'".format(st_date, d_max))
    fig = go.Figure([
        go.Bar(x=fil.Date, y=fil.Daily)
    ])
    fig.update_layout(
        title=f"{country}: number of new cases in the last {num_weeks} weeks ({fmt(st_date)} to {fmt(d_max)})",
        # xaxis = dict(
        # tickmode = 'array',
        #    tickvals = fil.Date,
        #    ticktext = fil.Date.dt.strftime(fmt)
        # )
    )
    return fig


def get_incidence_statistics(country):
    if country in list(population.keys()):
        _ = by_country(country)
        last = _.Date.iloc[-1]
        d14 = last - timedelta(days=13)
        d7 = last - timedelta(days=6)
        inc7 = _[_['Date'] == last].Cumulative.iloc[0] - _[_['Date'] == d7].Cumulative.iloc[0]
        res = "{} - incidence rates per 100000:\n 7 days: {:.2f}".format(country, inc7 * 100000 / population[country])
        inc14 = _[_['Date'] == last].Cumulative.iloc[0] - _[_['Date'] == d14].Cumulative.iloc[0]
        # .query("Date > '{}'".format(ft)).Daily.sum()
        # print(inc14)
        res += "\n14 days: {:.2f}".format(inc14 * 100000 / population[country])
        if 2*inc7 < inc14:
            res += f"\n7-day incidence is within normal value!"
        else:
            res += f"\n7-day incidence indicates a possible wave!!"
    else:
        res = f"Can't calculate incidence stats for {country}, no population data!"
    return res


df = get_data()
st.set_page_config(layout='wide')
st.title('Evolution of Covid 19 cases')
st.caption(f"source: {url}")
st.caption(f"Data downloaded on {now.strftime('%a, '+dt_fmt+', %H:%M')}")
st.header('Graphs since the beginning')
type_graph = st.sidebar.selectbox("Graph:", ['Daily', 'Cumulative'])
st.plotly_chart(gen_graph(type_graph.lower()))
cnt = st.sidebar.selectbox("Windowed graph for:", df.Country.unique(), )
num_wks = st.sidebar.number_input(label="Limit to this number of weeks:", value=20, max_value=80)
st.header(f'Windowed graphs for the last {int(num_wks)} weeks')
st.plotly_chart(get_windowed_graph(cnt, num_wks))
st.text(get_incidence_statistics(cnt))
