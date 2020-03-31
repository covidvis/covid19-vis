from __future__ import annotations

from datetime import datetime
from typing import Union

import altair as alt
import numpy as np
import pandas as pd


class StartCriterion(object):
    def transform(self, chart: CovidChart, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame()


def _days_between(d1: Union[str, datetime], d2: Union[str, datetime]):
    if pd.isna(d1) or pd.isna(d2):
        return None
    if isinstance(d1, str):
        try:
            d1 = datetime.strptime(d1, "%m-%d-%Y")
        except ValueError:
            d1 = datetime.strptime(d1, "%Y-%m-%d")
    if isinstance(d2, str):
        try:
            d2 = datetime.strptime(d2, "%m-%d-%Y")
        except ValueError:
            d2 = datetime.strptime(d2, "%Y-%m-%d")
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


# ref: https://gist.github.com/golobor/397b5099d42da476a4e6
class DotDict(dict):
    """A dict with dot access and autocompletion.

    The idea and most of the code was taken from
    http://stackoverflow.com/a/23689767,
    http://code.activestate.com/recipes/52308-the-simple-but-handy-collector-of-a-bunch-of-named/
    http://stackoverflow.com/questions/2390827/how-to-properly-subclass-dict-and-override-get-set
    """

    def __init__(self, *a, **kw):
        dict.__init__(self)
        self.update(*a, **kw)
        self.__dict__ = self

    def __setattr__(self, key, value):
        if key in dict.__dict__:
            raise AttributeError('This key is reserved for the dict methods.')
        dict.__setattr__(self, key, value)

    def __setitem__(self, key, value):
        if key in dict.__dict__:
            raise AttributeError('This key is reserved for the dict methods.')
        dict.__setitem__(self, key, value)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)
        self.__dict__ = self


class ChartSpec(DotDict):
    lockdown_X = 'lockdown_x'
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
        chart_df['zeros'] = np.zeros_like(chart_df[self.X])
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
        # put a fake layer in first to get an always-opaque legend
        layers = {'fake': base.mark_point(size=0, filled=True).encode(color=self.colorby)}
        if legend_selection is not None:
            layers['fake'] = layers['fake'].add_selection(legend_selection)
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
        alt_x = alt.X('x:Q', **xaxis_kwargs)
        alt_y = alt.Y('y:Q', **yaxis_kwargs)
        kwargs = dict(x=alt_x, y=alt_y, color=alt.Color(self.colorby))
        if not self.get('lines', False):
            kwargs['opacity'] = alt.value(0)
        elif legend_selection is not None:
            kwargs['opacity'] = alt.condition(legend_selection, alt.value(1), alt.value(.1))
        line_layer = base.mark_line(size=3).encode(**kwargs)
        line_layer = line_layer.transform_filter('datum.y !== null')
        if yscale == 'log':
            line_layer = line_layer.transform_filter('datum.y > 0')
        layers['lines'] = line_layer
        kwargs = dict(x=alt_x, y=alt_y, color=alt.Color(self.colorby))
        if not self.get('points', False):
            kwargs['opacity'] = alt.value(0)
        elif legend_selection is not None:
            kwargs['opacity'] = alt.condition(legend_selection, alt.value(.4), alt.value(.1))
        point_layer = base.mark_point(size=90, filled=True).encode(**kwargs)
        point_layer = point_layer.transform_filter('datum.y !== null')
        if self.get('yscale', 'linear') == 'log':
            point_layer = point_layer.transform_filter('datum.y > 0')
        layers['points'] = point_layer
        if self.get('has_tooltips', False):
            nearest = alt.selection(type='single', nearest=True, on='mouseover',
                                    fields=['x'], empty='none')
            layers['selectors'] = base.mark_point().encode(
                    x='x:Q',
                    opacity=alt.value(0),
            ).add_selection(nearest)
            if self.get('tooltip_points', False):
                layers['tooltip_points'] = layers['points'].mark_point(filled=True).encode(
                        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
                )
            if self.get('tooltip_text', False):
                extra_kwargs = {}
                if legend_selection is not None:
                    extra_kwargs['opacity'] = alt.condition(legend_selection, alt.value(1), alt.value(0.1))
                layers['tooltip_text'] = layers['points'].mark_text(align='left', dx=5, dy=-5).encode(
                    text=alt.condition(nearest, 'tooltip_text:N', alt.value(' ')),
                    **extra_kwargs
                ).transform_calculate(
                    tooltip_text='datum.{} + ": " + datum.y'.format(self.colorby)
                )
            if self.get('tooltip_rules'):
                layers['tooltip_rules'] = base.mark_rule(color='gray').encode(x='x:Q',).transform_filter(nearest)
            if self.get('lockdown_rules', False):
                layers['lockdown_rules'] = base.mark_rule(strokeDash=[7, 3]).encode(
                    x='x:Q',
                    color=alt.Color(self.colorby),
                    opacity=alt.condition(legend_selection, alt.value(1), alt.value(0.1)) if legend_selection is not None else alt.value(1),
                ).transform_filter(
                    'datum.x == datum.lockdown_x'
                )
                layers['lockdown_tooltips'] = layers['lockdown_rules'].mark_text(align='left', dx=5, dy=-220).encode(
                    text=alt.condition(nearest, 'lockdown_tooltip_text:N', alt.value(' '))
                ).transform_calculate(
                    lockdown_tooltip_text='datum.{} + " " + datum.lockdown_type'.format(self.colorby)
                )
        layered = alt.layer(*layers.values())
        return layered


class CovidChart(object):
    lockdown_X = 'lockdown_x'
    X = 'x'
    Y = 'y'

    def __init__(
            self,
            df: Union[str, pd.DataFrame],
            groupcol: str,
            start_criterion: StartCriterion,
            ycol: str,
            use_defaults: bool = True,
            ycol_is_cumulative: bool = True,
            top_k_groups: int = None,
            xcol: str = 'date',
            quarantine_df: pd.DataFrame = None
    ):
        if isinstance(df, str):
            df = pd.read_csv(df, parse_dates=[xcol], infer_datetime_format=True)
        if groupcol not in df.columns:
            raise ValueError('grouping col should be in dataframe cols')
        if ycol not in df.columns:
            raise ValueError('measure col should be in dataframe cols')

        if quarantine_df is not None:
            if groupcol not in quarantine_df.columns:
                raise ValueError('grouping col should be in dataframe cols')
            if 'lockdown_date' not in quarantine_df.columns:
                raise ValueError('lockdown_date should be in quarantine_df columns')
            if 'lockdown_type' not in quarantine_df.columns:
                raise ValueError('lockdown_type should be in quarantine_df columns')

        self.df = df
        self.quarantine_df = quarantine_df
        self.groupcol = groupcol
        self.start_criterion = start_criterion
        self.xcol = xcol
        self.ycol = ycol
        self.ycol_is_cumulative = ycol_is_cumulative
        self.top_k_groups = top_k_groups
        self.spec = ChartSpec()
        if use_defaults:
            self.set_defaults()

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

        df = self.start_criterion.transform(self, df)
        if self.quarantine_df is not None:
            df = df.merge(self.quarantine_df, how='left', on=self.groupcol)
            df[self.lockdown_X] = df.apply(lambda x: _days_between(x['date_of_N'], x['lockdown_date']), axis=1)

            for group in self.quarantine_df[self.groupcol].unique():
                lockdown_Xs = df.loc[df[self.groupcol] == group, self.lockdown_X].unique()
                lockdown_types = df.loc[df[self.groupcol] == group, 'lockdown_type'].unique()
                # insert some dummy rows w/ X == lockdown_X to get tooltip_rules w/ mouseover to work properly
                new_rows = pd.DataFrame({
                    self.groupcol: [group] * len(lockdown_Xs),
                    self.X: lockdown_Xs,
                    self.lockdown_X: lockdown_Xs,
                    'lockdown_type': lockdown_types
                })
                df = df.append(new_rows, ignore_index=True, sort=False)
        return df

    def set_logscale(self):
        self.spec.yscale = 'log'
        return self

    def set_xdomain(self, limits):
        self.spec.xdomain = limits
        return self

    def set_ydomain(self, limits):
        self.spec.ydomain = limits
        return self

    def set_xtitle(self, xtitle):
        self.spec.xtitle = xtitle
        return self

    def set_ytitle(self, ytitle):
        self.spec.ytitle = ytitle
        return self

    def add_lines(self):
        self.spec.lines = True
        return self

    def add_points(self):
        self.spec.points = True
        return self

    def set_interactive_legend(self):
        self.spec.interactive_legend = True
        return self

    def add_tooltip_text(self):
        self.spec.has_tooltips = True
        self.spec.tooltip_text = True
        return self

    def add_tooltip_points(self):
        self.spec.has_tooltips = True
        self.spec.tooltip_points = True
        return self

    def add_tooltip_rules(self):
        self.spec.has_tooltips = True
        self.spec.tooltip_rules = True
        return self

    def add_lockdown_rules(self):
        self.spec.has_tooltips = True
        self.spec.lockdown_rules = True
        return self

    def set_height(self, height):
        self.spec.height = height

    def set_width(self, width):
        self.spec.width = width

    def add_all_tooltips(self):
        return self.add_tooltip_points().add_tooltip_text().add_tooltip_rules()

    def set_defaults(self):
        self.spec.colorby = self.groupcol
        ret = self.add_lines().add_points().set_logscale().set_interactive_legend().add_all_tooltips()
        if self.quarantine_df is not None:
            ret = ret.add_lockdown_rules()
        return ret

    def compile(self):
        chart_df = self._preprocess_df()
        return self.spec.compile(chart_df)
