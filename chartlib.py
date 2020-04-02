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
    click = 'click'
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

    def _get_x(self, shorthand='x:Q'):
        xaxis_kwargs = {}
        if 'xdomain' in self:
            xaxis_kwargs['scale'] = alt.Scale(domain=self.xdomain)
        if 'xtitle' in self:
            xaxis_kwargs['title'] = self.xtitle
        return alt.X(shorthand, **xaxis_kwargs)

    def _get_y(self, shorthand='y:Q'):
        yaxis_kwargs = {}
        yscale = self.get('yscale', 'linear')
        if 'ydomain' in self:
            yaxis_kwargs['scale'] = alt.Scale(type=yscale, domain=self.ydomain)
        else:
            yaxis_kwargs['scale'] = alt.Scale(type=yscale)
        if 'ytitle' in self:
            yaxis_kwargs['title'] = self.ytitle
        return alt.Y(shorthand, **yaxis_kwargs)

    @property
    def _alt_color(self):
        return alt.Color(self.colorby)

    @property
    def _yscale(self):
        return self.get('yscale', 'linear')

    def _only_visible_when_in_focus(self, base, click_selection):
        if click_selection is not None:
            base = base.transform_filter(
                self._clicked_with_focus()
            )
        return base

    def _clicked_or_empty(self):
        return f'!isDefined({self.click}.{self.colorby}) || !isDefined({self.click}_{self.colorby}) || {self.click}.{self.colorby} == datum.{self.colorby}'

    def _clicked_with_focus(self):
        return f'isDefined({self.click}.{self.colorby}) && {self.click}.{self.colorby} == datum.{self.colorby}'

    def _someone_has_focus(self):
        return f'isDefined({self.click}.{self.colorby}) && isDefined({self.click}_{self.colorby})'

    def _make_line_layer(self, base, click_selection):
        kwargs = dict(x=self._get_x(), y=self._get_y(), color=self._alt_color)
        if not self.get('lines', False):
            kwargs['opacity'] = alt.value(0)
        elif click_selection is not None:
            kwargs['opacity'] = alt.condition(self._clicked_or_empty(), alt.value(1), alt.value(.1))
        line_layer = base.mark_line(size=3).encode(**kwargs)
        line_layer = line_layer.transform_filter('datum.y !== null')
        if self._yscale == 'log':
            line_layer = line_layer.transform_filter('datum.y > 0')
        return line_layer

    def _make_point_layer(self, base, click_selection, is_fake=False):
        kwargs = dict(x=self._get_x(), y=self._get_y(), color=alt.Color(self.colorby))
        if not self.get('points', False) and not is_fake:
            kwargs['opacity'] = alt.value(0)
        elif is_fake and click_selection is None:
            kwargs['opacity'] = alt.value(0)
        elif click_selection is not None:
            not_fake = not is_fake
            kwargs['opacity'] = alt.condition(
                self._clicked_or_empty(), alt.value(.4 * not_fake), alt.value(.1 * not_fake)
            )
        # nice big clickable points if is_fake
        point_layer = base.mark_point(size=400 if is_fake else 90, filled=True).encode(**kwargs)
        point_layer = point_layer.transform_filter('datum.y !== null')
        if self._yscale == 'log':
            point_layer = point_layer.transform_filter('datum.y > 0')
        if is_fake and click_selection is not None:
            # the first one makes it easier for tooltips to follow since otherwise these guys will stick
            point_layer = point_layer.transform_filter(self._clicked_or_empty())
            point_layer = point_layer.add_selection(click_selection)
        return point_layer

    def _make_tooltip_text_layer(self, point_layer, nearest, click_selection):
        ret = point_layer.mark_text(align='left', dx=5, dy=-5).encode(
            text=alt.condition(nearest, 'tooltip_text:N', alt.value(' ')),
            opacity=alt.value(1)
        ).transform_calculate(
            tooltip_text='datum.{} + ": " + datum.y'.format(self.colorby)
        )
        return self._only_visible_when_in_focus(ret, click_selection)

    def _make_lockdown_rules_layer(self, base, click_selection):
        ret = base.mark_rule(strokeDash=[7, 3]).encode(
            x='x:Q', color=self._alt_color
        ).transform_filter('datum.x == datum.lockdown_x')
        return self._only_visible_when_in_focus(ret, click_selection)

    def _make_lockdown_tooltips_layer(self, rules, nearest, click_selection):
        ret = rules.mark_text(align='left', dx=5, dy=-200).encode(
            text=alt.condition(nearest, 'lockdown_tooltip_text:N', alt.value(' '))
        ).transform_calculate(
            lockdown_tooltip_text='datum.{} + " " + datum.lockdown_type'.format(self.colorby)
        )
        return self._only_visible_when_in_focus(ret, click_selection)

    def _make_nearest_selectors(self, base):
        nearest = alt.selection_single(nearest=True, on='mouseover',
                                       fields=['x'], empty='none')
        return nearest, base.mark_point().encode(
            x='x:Q', opacity=alt.value(0),
        ).add_selection(nearest)

    def _collect_tooltip_layers(self, layers, base, nearest, click_selection):
        if not self.get('has_tooltips', False):
            return
        if self.get('tooltip_points', False):
            layers['tooltip_points'] = layers['points'].mark_point(filled=True).encode(
                opacity=alt.condition(nearest, alt.value(1), alt.value(0))
            ).transform_filter(self._clicked_with_focus())
        if self.get('tooltip_text', False):
            layers['tooltip_text'] = self._make_tooltip_text_layer(layers['points'], nearest, click_selection)
        if self.get('tooltip_rules'):
            layers['tooltip_rules'] = base.mark_rule(
                color='gray'
            ).encode(
                x='x:Q'
            ).transform_filter(
                nearest
            ).transform_filter(self._someone_has_focus())
        if self.get('lockdown_rules', False):
            layers['lockdown_rules'] = self._make_lockdown_rules_layer(base, click_selection)
            layers['lockdown_tooltips'] = self._make_lockdown_tooltips_layer(
                layers['lockdown_rules'], nearest, click_selection
            )

    def _make_lockdown_extrapolation_layer(self, base, click_selection):
        def _add_model_transformation_fields(base_chart):
            ret = base_chart.transform_filter(
                'datum.lockdown_x != null'
            ).transform_filter(
                'datum.x >= datum.lockdown_x'
            ).transform_filter(
                'datum.y !== null'
            ).transform_calculate(
                model_y='datum.lockdown_y * pow(datum.lockdown_slope, datum.x - datum.lockdown_x)'
            )
            if 'ydomain' in self:
                ret = ret.transform_filter('datum.model_y <= {}'.format(self.ydomain[1]))
            return ret

        ret = _add_model_transformation_fields(
            base.mark_line(size=3, strokeDash=[1, 1]).encode(
                x=self._get_x('x:Q'),
                y=self._get_y('model_y:Q'),
                color=self._alt_color,
            )
        )
        return self._only_visible_when_in_focus(ret, click_selection)

    def compile(self, df):
        self.validate(df)
        df = self._proprocess_df(df)
        base = alt.Chart(df, width=self.get('width', 1000), height=self.get('height', 500))
        layers = {}
        click_selection = None
        if self.get('click_selection', False):
            dropdown_options = [None] + list(df[self.colorby].unique())
            dropdown = alt.binding_select(options=dropdown_options, name=f'Filter on {self.colorby}: ')
            click_selection = alt.selection_single(
                fields=[self.colorby], on='click', name=self.click, empty='all',
                bind=dropdown
            )
        nearest, selectors = self._make_nearest_selectors(base)
        layers['selectors'] = selectors

        # put a fake layer in first to attach the click selection to
        layers['fake_points'] = self._make_point_layer(base, click_selection, is_fake=True)

        layers['lines'] = self._make_line_layer(base, click_selection)
        layers['points'] = self._make_point_layer(base, click_selection)

        self._collect_tooltip_layers(layers, base, nearest, click_selection)

        if self.get('lockdown_extrapolation', False):
            layers['model_lines'] = self._make_lockdown_extrapolation_layer(base, click_selection)
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
            quarantine_df = self.quarantine_df.copy()
            quarantine_df = quarantine_df.dropna()
            quarantine_df = quarantine_df.merge(
                df[[self.groupcol, 'date_of_N']], on=self.groupcol, how='inner'
            )
            quarantine_df[self.lockdown_X] = quarantine_df.apply(lambda x: _days_between(x['date_of_N'], x['lockdown_date']), axis=1)

            # only retain latest lockdown that appears... eventually we will want to allow for multiple
            quarantine_df = quarantine_df.loc[quarantine_df.lockdown_x > 0]
            quarantine_df = quarantine_df.loc[quarantine_df.groupby(self.groupcol).lockdown_x.idxmin()]
            del quarantine_df['date_of_N']
            df = df.merge(quarantine_df, how='left', on=self.groupcol)

            idx_before_at_lockdown = df.loc[df.x <= df.lockdown_x].groupby(df[self.groupcol]).x.idxmax()
            df_lockdown_y = df.loc[idx_before_at_lockdown]
            df_intercept = df.loc[df.x == 0].groupby(self.groupcol).first().reset_index()
            df = df.merge(
                df_intercept.rename(columns={'y': 'intercept'})[[self.groupcol, 'intercept']],
                how='left',
                on=self.groupcol
            )
            df = df.merge(
                df_lockdown_y.rename(columns={'y': 'lockdown_y'})[[self.groupcol, 'lockdown_y']],
                how='left',
                on=self.groupcol
            )
            df['lockdown_slope'] = np.exp(np.log(df.lockdown_y / df.intercept) / df.lockdown_x)

            new_rows = df.groupby(self.groupcol).max().reset_index()[[self.groupcol, self.lockdown_X, 'lockdown_type']]
            new_rows['x'] = new_rows.lockdown_x
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

    def set_click_selection(self):
        self.spec.click_selection = True
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

    def set_defaults(self):
        self.spec.colorby = self.groupcol
        ret = self.add_lines(
        ).add_points(
        ).set_logscale(
        ).set_click_selection(
        ).add_all_tooltips(
        ).add_lockdown_extrapolation(
        ).set_width(1000).set_height(500)
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
