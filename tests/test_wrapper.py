#!/usr/bin/env python

# Replica of overview.ipynb for test-driven-development purposes. This script is intended to be run as a standalone
# Python script, not as a Jupyter notebook.

from __future__ import annotations

import os

import pandas as pd
import seaborn as sns
import yfinance as yf

import alphalens

sns.set_style('white')

sector_names = {
    0: "information_technology",
    1: "financials",
    2: "health_care",
    3: "industrials",
    4: "utilities",
    5: "real_estate",
    6: "materials",
    7: "telecommunication_services",
    8: "consumer_staples",
    9: "consumer_discretionary",
    10: "energy"
}

ticker_sector = {
    "ACN": 0, "ATVI": 0, "ADBE": 0, "AMD": 0, "AKAM": 0, "ADS": 0, "GOOGL": 0, "GOOG": 0,
    "APH": 0, "ADI": 0, "ANSS": 0, "AAPL": 0, "AMAT": 0, "ADSK": 0, "ADP": 0, "AVGO": 0,
    "AMG": 1, "AFL": 1, "ALL": 1, "AXP": 1, "AIG": 1, "AMP": 1, "AON": 1, "AJG": 1, "AIZ": 1, "BAC": 1,
    "BK": 1, "BBT": 1, "BRK.B": 1, "BLK": 1, "HRB": 1, "BHF": 1, "COF": 1, "CBOE": 1, "SCHW": 1, "CB": 1,
    "ABT": 2, "ABBV": 2, "AET": 2, "A": 2, "ALXN": 2, "ALGN": 2, "AGN": 2, "ABC": 2, "AMGN": 2, "ANTM": 2,
    "BCR": 2, "BAX": 2, "BDX": 2, "BIIB": 2, "BSX": 2, "BMY": 2, "CAH": 2, "CELG": 2, "CNC": 2, "CERN": 2,
    "MMM": 3, "AYI": 3, "ALK": 3, "ALLE": 3, "AAL": 3, "AME": 3, "AOS": 3, "ARNC": 3, "BA": 3, "CHRW": 3,
    "CAT": 3, "CTAS": 3, "CSX": 3, "CMI": 3, "DE": 3, "DAL": 3, "DOV": 3, "ETN": 3, "EMR": 3, "EFX": 3,
    "AES": 4, "LNT": 4, "AEE": 4, "AEP": 4, "AWK": 4, "CNP": 4, "CMS": 4, "ED": 4, "D": 4, "DTE": 4,
    "DUK": 4, "EIX": 4, "ETR": 4, "ES": 4, "EXC": 4, "FE": 4, "NEE": 4, "NI": 4, "NRG": 4, "PCG": 4,
    "ARE": 5, "AMT": 5, "AIV": 5, "AVB": 5, "BXP": 5, "CBG": 5, "CCI": 5, "DLR": 5, "DRE": 5,
    "EQIX": 5, "EQR": 5, "ESS": 5, "EXR": 5, "FRT": 5, "GGP": 5, "HCP": 5, "HST": 5, "IRM": 5, "KIM": 5,
    "APD": 6, "ALB": 6, "AVY": 6, "BLL": 6, "CF": 6, "DWDP": 6, "EMN": 6, "ECL": 6, "FMC": 6, "FCX": 6,
    "IP": 6, "IFF": 6, "LYB": 6, "MLM": 6, "MON": 6, "MOS": 6, "NEM": 6, "NUE": 6, "PKG": 6, "PPG": 6,
    "T": 7, "CTL": 7, "VZ": 7,
    "MO": 8, "ADM": 8, "BF.B": 8, "CPB": 8, "CHD": 8, "CLX": 8, "KO": 8, "CL": 8, "CAG": 8,
    "STZ": 8, "COST": 8, "COTY": 8, "CVS": 8, "DPS": 8, "EL": 8, "GIS": 8, "HSY": 8, "HRL": 8,
    "AAP": 9, "AMZN": 9, "APTV": 9, "AZO": 9, "BBY": 9, "BWA": 9, "KMX": 9, "CCL": 9,
    "APC": 10, "ANDV": 10, "APA": 10, "BHGE": 10, "COG": 10, "CHK": 10, "CVX": 10, "XEC": 10, "CXO": 10,
    "COP": 10, "DVN": 10, "EOG": 10, "EQT": 10, "XOM": 10, "HAL": 10, "HP": 10, "HES": 10, "KMI": 10
}


def get_test_data(filepath: str) -> pd.DataFrame:
    """ Copied from src/alphalens/examples/overview.ipynb.

    Args:
        filepath (str): Path to the pickle file containing the data. Defaults to None.
    """
    if filepath is None or not isinstance(filepath, str) or not filepath.strip().endswith('.pkl'):
        raise ValueError(f"The 'filepath' argument must be a valid string representing the path to a pickle file: {filepath}")

    if os.path.exists(filepath) and os.path.isfile(filepath):
        df = pd.read_pickle(filepath)
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"The pickle file at '{filepath}' does not contain a valid DataFrame.")
        if df.empty:
            raise ValueError(f"The pickle file at '{filepath}' is empty.")
        print(f"\nLoaded data from pickle file: {filepath}\n")
        return df

    tickers = list(ticker_sector.keys())
    data = yf.download(tickers, start='2014-12-01', end='2017-01-01')
    if not isinstance(data, pd.DataFrame):
        raise ValueError("The downloaded data is not a valid DataFrame. Please check the ticker symbols and date range.")
    if data.empty:
        raise ValueError("The downloaded data is empty. Please check the ticker symbols and date range.")
    data.index = pd.to_datetime(data.index, utc=True)
    data = data.stack(future_stack=True)
    data.index.names = ['date', 'asset']
    data.to_pickle(filepath)

    print(f"\nData downloaded and saved to pickle file: {filepath}\n")

    return data

def compute_factor(data: pd.DataFrame) -> pd.Series:
    """ Compute a simple factor for demonstration purposes.

    Args:
        data (pd.DataFrame): The input data containing stock prices.
    Returns:
        pd.Series: A simple factor computed from the input data.
    """
    lookahead_bias_days = 5

    factor = data.loc[:, 'Open'].unstack('asset')
    factor = factor.pct_change(lookahead_bias_days)

    # introduce look-ahead bias and make the factor predictive
    factor = factor.shift(-lookahead_bias_days)
    factor = factor.stack()

    return factor

def get_pricing(data: pd.DataFrame) -> pd.DataFrame:
    prices = data.loc[:, 'Open'].iloc[1:].unstack('asset')
    return prices

def get_factor_data() -> pd.DataFrame:
    test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")
    if not os.path.isdir(test_data_dir):
        os.makedirs(test_data_dir)
        print(f"\nCreated directory for test data: {test_data_dir}\n")

    data_filepath = os.path.join(test_data_dir, "test_data_wrapper.pkl")  # Specify the path to your pickle file here
    df = get_test_data(data_filepath)

    predictive_factor = compute_factor(df)

    pricing = get_pricing(df)

    # Format tearsheet input data
    factor_data = alphalens.utils.get_clean_factor_and_forward_returns(predictive_factor,
                                                                       pricing,
                                                                       quantiles=5,
                                                                       bins=None,
                                                                       groupby=ticker_sector,
                                                                       groupby_labels=sector_names)

    return factor_data


if __name__ == "__main__":

    df = get_factor_data()
    print(df.head())

    result = alphalens.wrapper.return_analysis_wrapper(data=df,
                                                       tear_sheet_filepath="wrapper_return_tear_sheet.png")
    print("\n--- Return Analysis Wrapper Results:")
    for key, value in result.items():
        print(f"\n{key}:\n{value}\n")

    result = alphalens.wrapper.information_analysis_wrapper(data=df,
                                                            tear_sheet_filepath="wrapper_information_tear_sheet.png")
    print("\n--- Information Analysis Wrapper Results:")
    for key, value in result.items():
        print(f"\n{key}:\n{value}\n")

    result = alphalens.wrapper.turnover_analysis_wrapper(data=df,
                                                         turnover_period=5,
                                                         period_unit="D",
                                                         tear_sheet_filepath="wrapper_turnover_tear_sheet.png")
    print("\n--- Turnover Analysis Wrapper Results:")
    for key, value in result.items():
        print(f"\n{key}:\n{value}\n")
