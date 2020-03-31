from __future__ import annotations

from datetime import datetime
from typing import Union

from bunch import Bunch
import altair as alt
import numpy as np
import pandas as pd


class StartCriterion(object):
    def transform(self, chart: CovidChart, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame()


def _days_between(d1: Union[str, datetime], d2: Union[str, datetime]):
    if isinstance(d1, str):
        d1 = datetime.strptime(d1, "%m-%d-%Y")
    if isinstance(d2, str):
        d2 = datetime.strptime(d2, "%m-%d-%Y")
    return int((d2 - d1).days)


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
        df[chart.X] = df.apply(lambda x: _days_between(x[date_of_N], x[chart.xcol]), axis=1)
        return df


class ChartSpec(Bunch):
    X = 'x'
    Y = 'y'
    def validate(self, df):
        if 'lines' not in self and 'points' not in self:
            raise ValueError('should have at least one of lines or points')
        if self.X not in df.columns:
            raise ValueError('dataframe should have an x column')
        if self.Y not in df.columns:
            raise ValueError('dataframe should have a y column')

    def _proprocess_df(self, df):
        chart_df = df.copy()
        if 'xdomain' in self:
            xmin, xmax = self.xdomain[0], self.xdomain[1]
            chart_df = chart_df.loc[(chart_df[self.X] >= xmin) & (chart_df[self.X] <= xmax)]
        if 'ydomain' in self:
            ymin, ymax = self.ydomain[0], self.ydomain[1]
            chart_df = chart_df.loc[(chart_df[self.Y] >= ymin) & (chart_df[self.Y] <= ymax)]
        return chart_df

    def compile(self, df):
        self.validate(df)
        df = self._proprocess_df(df)
        base = alt.Chart(df, width=self.get('width', 1000), height=self.get('height', 500))
        legend_selection = None
        if self.get('interactive_legend', False):
            legend_selection = alt.selection_multi(fields=[self.colorby], bind='legend')
        layers = []
        xaxis_kwargs = {}
        if 'xdomain' in self:
            xaxis_kwargs['scale'] = alt.Scale(domain=self.xdomain)
        if 'xtitle' in self:
            xaxis_kwargs['title'] = self.xtitle
        yaxis_kwargs = {}
        yscale = self.get('yscale', 'linear')
        if 'ydomain' in self:
            yaxis_kwargs['scale'] = alt.Scale(type=yscale, domain=self.ydomain)
        else:
            yaxis_kwargs['scale'] = alt.Scale(type=yscale)
        if 'ytitle' in self:
            yaxis_kwargs['title'] = self.ytitle
        alt_x = alt.X("x:Q", **xaxis_kwargs)
        alt_y = alt.Y("y:Q", **yaxis_kwargs)
        if 'lines' in self:
            kwargs = dict(x=alt_x, y=alt_y, color=alt.Color(self.colorby))
            if legend_selection is not None:
                kwargs['opacity'] = alt.condition(legend_selection, alt.value(1), alt.value(.1))
            line_layer = base.mark_line(size=3).encode(**kwargs)
            line_layer = line_layer.transform_filter('datum.y !== null')
            if yscale == 'log':
                line_layer = line_layer.transform_filter('datum.y > 0')
            if legend_selection is not None:
                line_layer = line_layer.add_selection(legend_selection)
            layers.append(line_layer)
        if 'points' in self:
            kwargs = dict(x=alt_x, y=alt_y, color=alt.Color(self.colorby))
            if legend_selection is not None:
                kwargs['opacity'] = alt.condition(legend_selection, alt.value(.4), alt.value(.1))
            point_layer = base.mark_point(size=90, filled=True).encode(**kwargs)
            point_layer = point_layer.transform_filter('datum.y !== null')
            if self.get('yscale', 'linear') == 'log':
                point_layer = point_layer.transform_filter('datum.y > 0')
            layers.append(point_layer)
        if self.get('has_tooltips', False):
            nearest = alt.selection(type='single', nearest=True, on='mouseover',
                                    fields=['x'], empty='none')
            layers.append(
                base.mark_point().encode(
                    x='x:Q',
                    opacity=alt.value(0),
                ).add_selection(nearest)
            )
            if self.get('tooltip_points', False):
                layers.append(
                    layers[1].mark_point(filled=True).encode(
                        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
                    )
                )
            if self.get('tooltip_text', False):
                extra_kwargs = {}
                if legend_selection is not None:
                    extra_kwargs['opacity'] = alt.condition(legend_selection, alt.value(1), alt.value(0.1))
                layers.append(
                    layers[1].mark_text(align='left', dx=5, dy=-5).encode(
                        text=alt.condition(nearest, 'tooltip_text:N', alt.value(' ')),
                        **extra_kwargs
                    ).transform_calculate(
                        tooltip_text='datum.{} + ": " + datum.y'.format(self.colorby)
                    )
                )
            if self.get('tooltip_rules'):
                layers.append(
                    base.mark_rule(color='gray').encode(x='x:Q',).transform_filter(nearest)
                )
        return alt.layer(*layers)


class CovidChart(object):
    X = 'x'
    Y = 'y'

    def __init__(
            self,
            df: Union[str, pd.DataFrame],
            groupcol: str,
            start_criterion: StartCriterion,
            ycol: str,
            ycol_is_cumulative: bool,
            top_k_groups: int = None,
            xcol: str = 'date'
    ):
        if isinstance(df, str):
            df = pd.read_csv(df, index_col=0, parse_dates=True)
        if groupcol not in df.columns:
            raise ValueError('grouping col should be in dataframe cols')
        if ycol not in df.columns:
            raise ValueError('measure col should be in dataframe cols')

        self.df = df
        self.groupcol = groupcol
        self.start_criterion = start_criterion
        self.xcol = xcol
        self.ycol = ycol
        self.ycol_is_cumulative = ycol_is_cumulative
        self.top_k_groups = top_k_groups
        self.chart_spec = ChartSpec()
        self.chart_spec.colorby = self.groupcol

    def _preprocess_df(self) -> pd.DataFrame:
        df = self.df.copy()
        if self.ycol_is_cumulative:
            df[self.Y] = df[self.ycol]
        else:
            df[self.Y] = np.zeros_like(df[self.ycol])
            for group in df[self.groupcol].unique():
                pred = df[self.groupcol] == group
                df.loc[pred, self.Y] = df.loc[pred, self.ycol].cumsum()

        if self.top_k_groups is not None:
            top_k_groups = list(df.groupby(self.groupcol)[self.Y].max().nlargest(self.top_k_groups).index)
            df = df.loc[df[self.groupcol].isin(top_k_groups)]

        return self.start_criterion.transform(self, df)

    def set_logscale(self):
        self.chart_spec.yscale = 'log'
        return self

    def set_xdomain(self, limits):
        self.chart_spec.xdomain = limits
        return self

    def set_ydomain(self, limits):
        self.chart_spec.ydomain = limits
        return self

    def set_xtitle(self, xtitle):
        self.chart_spec.xtitle = xtitle
        return self

    def set_ytitle(self, ytitle):
        self.chart_spec.ytitle = ytitle
        return self

    def add_lines(self):
        self.chart_spec.lines = True
        return self

    def add_points(self):
        self.chart_spec.points = True
        return self

    def set_interactive_legend(self):
        self.chart_spec.interactive_legend = True
        return self

    def add_tooltip_text(self):
        self.chart_spec.has_tooltips = True
        self.chart_spec.tooltip_text = True
        return self

    def add_tooltip_points(self):
        self.chart_spec.has_tooltips = True
        self.chart_spec.tooltip_points = True
        return self

    def add_tooltip_rules(self):
        self.chart_spec.has_tooltips = True
        self.chart_spec.tooltip_rules = True
        return self

    def set_height(self, height):
        self.chart_spec.height = height

    def set_width(self, width):
        self.chart_spec.width = width

    def add_all_tooltips(self):
        return self.add_tooltip_points().add_tooltip_text().add_tooltip_rules()

    def set_default(self):
        return self.add_lines().add_points().set_logscale().set_interactive_legend().add_all_tooltips()

    def compile(self):
        chart_df = self._preprocess_df()
        return self.chart_spec.compile(chart_df)
