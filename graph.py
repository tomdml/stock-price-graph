import io
import pickle

from filecache import filecache
import matplotlib.pyplot as plt
import pandas as pd
import requests

API_KEY = '#########'
ONE_DAY = 24 * 60 * 60

@filecache(ONE_DAY)
def get_intraday(api_key, symbol):

    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol.removeprefix('$'),
        'interval': '1min',
        'outputsize': 'full',
        'apikey': api_key,
    }

    res = requests.get(
        'https://www.alphavantage.co/query', 
        params=params
    )

    metadata, data = res.json().values()

    df = pd.DataFrame(data)


    df = df.astype(float)
    df = df.T

    df.index.name = 'time'
    df.columns = ['open', 'high', 'low', 'close', 'volume']

    return df


@filecache(ONE_DAY)
def get_ext_intraday(api_key, symbol):

    params = {
        'function': 'TIME_SERIES_INTRADAY_EXTENDED',
        'symbol': symbol.removeprefix('$'),
        'interval': '1min',
        'outputsize': 'full',
        'slice': None,
        'apikey': api_key,
    }

    csvs = (
        requests.get(
            'https://www.alphavantage.co/query', 
            params=params | {'slice': slice_}
        ).text
        for slice_ 
        in ('year1month1', 'year1month2', 'year1month3')
    )

    df = pd.concat(
        pd.read_csv(
            io.StringIO(csv),
            index_col='time'
        ) 
        for csv 
        in csvs
    )

    df = df.astype(float)

    return df


def import_data(source_func, symbol):

    df = source_func(API_KEY, symbol)

    index = df.index
    index = [item.split() for item in index]
    df.index = pd.MultiIndex.from_tuples(index, names=['date', 'time'])

    df = df['close'].unstack(level=-1)
    df = df.T
    df = df.interpolate()

    return df


if __name__ == '__main__':

    df = import_data(get_ext_intraday, 'GME')
    df = df / df.loc['09:30:00']
    mean = df.mean(axis=1)

    ax = df.plot(legend=False, linewidth=0.4, color='white')
    mean.plot(ax=ax, linewidth=0.5, color='red')

    ax.axvspan(
        0, df.index.get_loc('09:30:00'),
        alpha=0.1, color='grey'
    )

    ax.axvspan(
        df.index.get_loc('16:00:00'), len(df),
        alpha=0.1, color='grey'
    )

    plt.ylim(0.8, 1.2)
    plt.margins(0)

    plt.show()
