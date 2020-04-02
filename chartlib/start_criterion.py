from __future__ import annotations
from typing import TYPE_CHECKING

import pandas as pd

from .utils import days_between
if TYPE_CHECKING:  # ref: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from .covid_chart import CovidChart


class StartCriterion(object):
    def transform(self, chart: CovidChart, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame()


class DaysSinceNumReached(StartCriterion):
    def __init__(self, N, col=None):
        self.N = N
        self.col = col

    def transform(self, chart: CovidChart, df: pd.DataFrame) -> pd.DataFrame:
        if chart.xcol not in df.columns:
            df = df.reset_index()
        col = self.col
        if col is None:
            col = chart.Y
        days_since_N = df[df[col] > self.N].groupby(chart.groupcol)[chart.xcol].min().to_dict()
        date_of_N = 'date_of_N'
        df[date_of_N] = df.apply(lambda x: days_since_N.get(x[chart.groupcol]), axis=1)
        df = df.dropna(subset=[date_of_N])
        df[chart.X] = df.apply(lambda x: days_between(x[date_of_N], x[chart.xcol]), axis=1)
        return df
