from __future__ import annotations
from typing import Union, Dict

import numpy as np
import pandas as pd

from .chart_spec import ChartSpec
from .start_criterion import StartCriterion, DaysSinceNumReached
from .utils import days_between


class CovidChart(object):
    """
    A class that composes a ChartSpec and uses the state therein to compute a dataframe
    that will be used as input to altair to generate a Vega-Lite spec. None of the altair
    stuff happens here (that's in ChartSpec), but *all* of the dataframe processing happens here.

    Also provides various convenience methods for setting ChartSpec state.
    """
    X = 'x'
    Y = 'y'
    lockdown_x = 'lockdown_x'
    lockdown_y = 'lockdown_y'
    x_type = 'x_type'
    y_type = 'y_type'
    normal_type = 'normal'
    lockdown_type = 'lockdown'

    def __init__(
        self,
        df: Union[str, pd.DataFrame],
        groupcol: str,
        start_criterion: StartCriterion,
        ycol: str,
        level: str = 'US',  # one of: [US, USA, country]
        use_defaults: bool = True,
        ycol_is_cumulative: bool = True,
        top_k_groups: int = None,
        xcol: str = 'date',
        quarantine_df: Union[str, pd.DataFrame] = None,
    ):
        object.__setattr__(self, 'groupcol', groupcol)
        object.__setattr__(self, 'start_criterion', start_criterion)
        object.__setattr__(self, 'xcol', xcol)
        object.__setattr__(self, 'ycol', ycol)
        object.__setattr__(self, 'ycol_is_cumulative', ycol_is_cumulative)
        object.__setattr__(self, 'top_k_groups', top_k_groups)
        object.__setattr__(self, 'spec', ChartSpec())

        if isinstance(df, str):
            df = pd.read_csv(df, parse_dates=[xcol], infer_datetime_format=True)
        self._validate_df(df)

        readable_group_name = level
        if isinstance(quarantine_df, str):
            if level.lower() in ['us', 'usa', 'united states']:
                quarantine_df = self._injest_usa_quarantine_df(quarantine_df)
                readable_group_name = 'state'
            elif level == 'country':
                quarantine_df = self._injest_country_quarantine_df(quarantine_df)
            else:
                raise ValueError('invalid level %s: only "US" and "country" allowed now')
        quarantine_df = quarantine_df.dropna(subset=[groupcol, 'lockdown_date', 'lockdown_type'])
        self._validate_quarantine_df(quarantine_df)

        object.__setattr__(self, 'df', df)
        object.__setattr__(self, 'quarantine_df', quarantine_df)

        self.spec.detailby = groupcol
        self.spec.colorby = groupcol
        self.spec.facetby = None
        self.spec.readable_group_name = readable_group_name
        if use_defaults:
            self.set_defaults()

    def _validate_df(self, df):
        if self.groupcol not in df.columns:
            raise ValueError('grouping col should be in dataframe cols')
        if self.ycol not in df.columns:
            raise ValueError('measure col should be in dataframe cols')

    def _validate_quarantine_df(self, quarantine_df):
        if self.groupcol not in quarantine_df.columns:
            raise ValueError('grouping col should be in dataframe cols')
        if 'lockdown_date' not in quarantine_df.columns:
            raise ValueError('lockdown_date should be in quarantine_df columns')
        if 'lockdown_type' not in quarantine_df.columns:
            raise ValueError('lockdown_type should be in quarantine_df columns')

    def _injest_country_quarantine_df(self, quarantine_csv):
        quarantine_df = pd.read_csv(quarantine_csv)
        quarantine_df = quarantine_df.loc[quarantine_df.Level == 'Enforcement']
        quarantine_df['Lockdown Type'] = quarantine_df.apply(
            lambda x: x['Scope'] + ' ' + x['Type'], axis=1
        )
        quarantine_cols = ['Country_Region', 'Date Enacted', 'Lockdown Type']
        quarantine_df = quarantine_df[quarantine_cols]
        quarantine_df = quarantine_df.rename(
            columns={'Date Enacted': 'lockdown_date', 'Lockdown Type': 'lockdown_type'}
        )
        return quarantine_df

    def _injest_usa_quarantine_df(self, quarantine_csv):
        quarantine_df = pd.read_csv(quarantine_csv)
        quarantine_df_emergency = quarantine_df.copy()
        quarantine_df = quarantine_df.loc[quarantine_df.Type == 'Level 2 Lockdown']
        quarantine_df['Lockdown Type'] = 'Full Lockdown'
        quarantine_cols = ['Province_State', 'Date Enacted', 'Lockdown Type']
        quarantine_df = quarantine_df[quarantine_cols]
        quarantine_df_emergency['Lockdown Type'] = 'Emergency Declared'
        quarantine_df_emergency = quarantine_df_emergency.loc[quarantine_df_emergency.Regions == 'All']
        quarantine_cols_emergency = ['Province_State', 'State of emergency declared', 'Lockdown Type']
        quarantine_df_emergency = quarantine_df_emergency[quarantine_cols_emergency]
        quarantine_df_emergency = quarantine_df_emergency.rename(
            columns={'State of emergency declared': 'Date Enacted'}
        )
        quarantine_df = pd.concat([quarantine_df, quarantine_df_emergency])
        quarantine_df = quarantine_df.rename(
            columns={'Date Enacted': 'lockdown_date', 'Lockdown Type': 'lockdown_type'}
        )
        return quarantine_df

    def _preprocess_lockdown_info(self, df) -> pd.DataFrame:
        quarantine_df = self.quarantine_df.copy()
        quarantine_df[self.x_type] = self.lockdown_type
        quarantine_df = quarantine_df.merge(
            df[[self.groupcol, 'date_of_N']].groupby(self.groupcol).first(),
            on=self.groupcol,
            how='inner'
        )
        quarantine_df[self.X] = quarantine_df.apply(
            lambda x: days_between(x['date_of_N'], x['lockdown_date']), axis=1
        )
        del quarantine_df['date_of_N']

        # only retain lockdown events that appear in the chart domain
        quarantine_df = quarantine_df.loc[quarantine_df.x.between(*self.spec.xdomain, inclusive=False)]

        # for trends, use earliest lockdown that appears... eventually we will want to specify this somehow
        trend_df = quarantine_df.loc[quarantine_df.groupby(self.groupcol).x.idxmin()]
        df = df.merge(
            trend_df.rename(columns={self.X: self.lockdown_x})[[self.groupcol, self.lockdown_x]],
            how='left',
            on=self.groupcol
        )

        idx_before_at_lockdown = df.loc[df.x <= df.lockdown_x].groupby(df[self.groupcol]).x.idxmax()
        df_lockdown_y = df.loc[idx_before_at_lockdown]
        df_intercept = df.loc[df.groupby(self.groupcol).x.idxmin()]
        df = df.merge(
            df_intercept.rename(columns={self.Y: 'y_start', self.X: 'x_start'})[[self.groupcol, 'y_start', 'x_start']],
            how='left',
            on=self.groupcol
        )
        df = df.merge(
            df_lockdown_y.rename(columns={self.Y: self.lockdown_y})[[self.groupcol, self.lockdown_y]],
            how='left',
            on=self.groupcol
        )
        df['lockdown_slope'] = np.exp(np.log(df.lockdown_y / df.y_start) / (df.lockdown_x - df.x_start))

        # these new rows are to ensure we have at least one point where x == lockdown_x since this is the filter
        # used to generate lockdown rules...
        # we need this b/c we can only attach mouseover interactions to one column, and it is already attached to x

        # TODO (smacke): instead of x and lockdown_x, we should have x and x_type, where x_type can be normal,
        # lockdown, etc... This will also generalize better if we want to change x based on e.g. a dropdown
        new_rows = df.groupby(self.groupcol).max().reset_index()[[self.groupcol, self.lockdown_x]]
        new_rows[self.X] = new_rows.lockdown_x
        df = df.append(new_rows, ignore_index=True, sort=False)

        # now add lockdown info as new rows in our df
        df = df.append(quarantine_df, ignore_index=True, sort=False)
        return df

    def _preprocess_df(self) -> pd.DataFrame:
        df = self.df.copy()
        df[self.x_type] = 'normal'
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

        if 'xdomain' in self.spec:
            xmin, xmax = self.spec.xdomain[0], self.spec.xdomain[1]
            df = df.loc[(df.x >= xmin) & (df.x <= xmax)]
        if 'ydomain' in self.spec:
            ymin, ymax = self.spec.ydomain[0], self.spec.ydomain[1]
            df = df.loc[(df.y >= ymin) & (df.y <= ymax)]

        if self.quarantine_df is not None:
            df = self._preprocess_lockdown_info(df)

        readable_group_name = self.spec.get('readable_group_name', None)
        if readable_group_name is not None:
            readable_group_name = self.spec._get_legend_title()
            df[readable_group_name] = df[self.spec.colorby]

        return df

    def _make_info_dict(self, qdf):
        info_dict = {}

        def _make_info_from_row(row):
            info_dict[row[self.groupcol]] = f'{self.groupcol} is implementing a general lockdown '
            f'{"across the territory" if row["Planned end date"] is None else "in specific regions"}. '
            f'The lockdown started on {row["DateEnacted"]}. '
            f'{"No specific end date is announced" if row["Planned end date"] is None else "It will last until {}".format(row["Planned end date"])}.'

        qdf.apply(_make_info_from_row)
        return info_dict

    def __getattr__(self, item):
        if item not in self.__getattribute__('spec'):
            raise AttributeError("Neither this object nor spec the spec contain attribute %s" % item)
        return self.spec[item]

    def __setattr__(self, key, value):
        self.spec[key] = value

    def set_title(self, title):
        self.spec.title = title
        return self
        
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

    def set_click_selection(self):
        self.spec.click_selection = True
        return self

    def set_legend_selection(self):
        self.spec.legend_selection = True
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
        return self

    def set_width(self, width):
        self.spec.width = width
        return self

    def add_all_tooltips(self):
        return self.add_tooltip_points().add_tooltip_text().add_tooltip_rules()

    def add_lockdown_extrapolation(self):
        self.spec.lockdown_extrapolation = True
        return self

    def set_interactive(self, interactive=True):
        self.spec.interactive = interactive
        return self

    def colorby(self, col):
        self.spec.colorby = col
        return self

    def facetby(self, col):
        self.spec.facetby = col
        return self

    def set_point_size(self, point_size: int):
        self.spec.point_size = point_size
        return self

    def set_unfocused_opacity(self, opacity: float):
        self.spec.unfocused_opacity = opacity
        return self

    def set_readable_group_name(self, readable_name: str):
        self.spec.readable_group_name = readable_name
        return self

    def set_colormap(
            self,
            colormap: Union[str, pd.DataFrame, Dict] = None,
            default_color: str = None,
            **kwargs
    ):
        if colormap is None:
            colormap = {}
        if isinstance(colormap, str):
            colormap = pd.read_csv(colormap)
        if isinstance(colormap, pd.DataFrame):
            keycol, valcol = colormap.columns
            colormap = dict(colormap.set_index(keycol)[valcol])
        if not isinstance(colormap, dict):
            raise ValueError('expected to have a dictionary by now; something weird happened')
        colormap = dict(colormap)
        colormap.update(kwargs)
        self.spec.colormap = colormap
        if default_color is not None:
            self.spec.default_color = default_color
        return self

    def set_defaults(self):
        self.spec.detailby = self.groupcol
        self.spec.colorby = self.groupcol
        self.spec.point_size = ChartSpec.DEFAULT_POINT_SIZE
        ret = self.add_lines(
        ).add_points(
        ).set_logscale(
        ).set_click_selection(
        ).set_legend_selection(
        ).add_all_tooltips(
        ).add_lockdown_extrapolation(
        ).set_interactive(False).set_width(
            self.spec.DEFAULT_WIDTH
        ).set_height(
            self.spec.DEFAULT_HEIGHT
        )
        if self.quarantine_df is not None:
            ret = ret.add_lockdown_rules()
        return ret

    def compile(self):
        chart_df = self._preprocess_df()
        return self.spec.compile(chart_df)

    def export(self, fname="vis.json", js_var="vis"):
        import json
        with open(fname, 'w') as f:
            f.write(f"var {js_var} = {json.dumps(self.compile().to_dict())}")
