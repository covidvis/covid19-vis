from __future__ import annotations
from typing import Union, Dict

import numpy as np
import pandas as pd

from .chart_spec import ChartSpec
from .start_criterion import StartCriterion
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
    xmax = 'xmax'
    x_type = 'x_type'
    y_type = 'y_type'
    normal_type = 'normal'
    lockdown_type = 'lockdown'
    lockdown_idx = 'lockdown_idx'

    def __init__(
            self,
            df: Union[str, pd.DataFrame],
            groupcol: str,
            start_criterion: StartCriterion,
            ycol: str,
            level: str = 'US',  # one of: [usa_old, US, USA, country]
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
        object.__setattr__(self, 'level', level)
        object.__setattr__(self, 'ycol_is_cumulative', ycol_is_cumulative)
        object.__setattr__(self, 'top_k_groups', top_k_groups)
        object.__setattr__(self, 'spec', ChartSpec())

        if isinstance(df, str):
            df = pd.read_csv(df, parse_dates=[xcol], infer_datetime_format=True)
        self._validate_df(df)

        readable_group_name = level
        if isinstance(quarantine_df, str):
            if level.lower() == 'usa_old':
                quarantine_df = self._ingest_usa_quarantine_df_old(quarantine_df)
                readable_group_name = 'state'
            elif level.lower() in ['us', 'usa', 'united states']:
                quarantine_df = self._ingest_usa_quarantine_df(quarantine_df)
                readable_group_name = 'state'
            elif level.lower() in ('country', 'world'):
                quarantine_df = self._ingest_country_quarantine_df(quarantine_df)
            else:
                raise ValueError('invalid level %s: only "US" and "country" allowed now' % level)
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

    def _ingest_country_quarantine_df(self, quarantine_csv):

        # border screening = b/B; travel restrictions= t/T; border closures = c/C
        # shelter-in-place = l/L; gathering limitations= g/G; k-12 school closures = s/S
        # non-essential business closure = n/N
        def create_lockdown_type_world (x, emo_flag):
            s = r = emo_s = ""
            regional_flag = closure_flag = not_the_first_flag = 0 
            if (x['coverage'] == 'Targeted'):
                r = 'Regional'
                regional_flag = 1
            if (x['Travel Restrictions'] == "Screening"): # assumption: only one travel restriction at a time
                s = s + " Border Screening"
                not_the_first_flag = 1
                emo_s = (emo_s + "b") if (regional_flag == 1) else (emo_s + "B")
            elif (x['Travel Restrictions'] == "Quarantine on high-risk regions"):
                s = s + " Visitor Quarantine"
                not_the_first_flag = 1
                emo_s = (emo_s + "t") if (regional_flag == 1) else (emo_s + "T")
            elif (x['Travel Restrictions'] == "Ban on high risk regions"):
                s = s + " Border Closures"
                not_the_first_flag = 1
                emo_s = (emo_s + "c") if (regional_flag == 1) else (emo_s + "C")
            if (x['Shelter-in-place Order'] == "Restrict movement"):
                # Movement restriction recommended is omitted
                if (not_the_first_flag == 1): s = s + ","
                s = s + " Stay-at-home Order"
                not_the_first_flag = 1
                emo_s = (emo_s + "l") if (regional_flag == 1) else (emo_s + "L")
            if (x['Gathering Limitations'] == "Required Cancelling Public Events"):
                # Recommend Cancelling Public Events is omitted
                if (not_the_first_flag == 1): s = s + ","
                s = s + " Gatherings Banned"
                not_the_first_flag = 1
                emo_s = (emo_s + "g") if (regional_flag == 1) else (emo_s +"G")
            if (x['K-12 School Closure'] == "Required Closing"):
                if (not_the_first_flag == 1):
                    s = s + ","
                s = s + " Closure of Schools"
                closure_flag = 1
                not_the_first_flag = 1
                emo_s = (emo_s + "s") if (regional_flag == 1) else (emo_s + "S")
            if (x['Non-essential Businesses Closure'] == "Required Closing Workspaces"):
                # Recommend Closing Workspaces is omitted
                if (not_the_first_flag == 1):
                    s = s + ","
                if (closure_flag == 0):
                    s = s + " Closure of Non-essential Businesses"
                else:
                    s = s + " Non-essential Businesses"
                closure_flag = 1
                not_the_first_flag = 1
                emo_s = (emo_s + "n") if (regional_flag == 1) else (emo_s + "N")
            if (emo_flag == 1): return emo_s
            if (s == ""): return s # Ensures just "Regional" is not returned
            return (r + s).strip()

        def strip_nans(x):
            # gets rid of nans in a list
            if (type(x) == list):
                x_strip = ""
                for a in x:
                    if (a == a):
                        # not nan
                        x_strip = x_strip + a.strip()
                return x_strip
            else:
                return x.strip()


        quarantine_df = pd.read_csv ('./data/quarantine-activity-Apr19.csv')
        quarantine_df = quarantine_df = quarantine_df.rename(
             columns={'date': 'lockdown_date', 'country_name': 'Country_Region'}
        )

        quarantine_df = quarantine_df.groupby(['lockdown_date', 'Country_Region', 'coverage']).agg({'Travel Restrictions': list, 'Gathering Limitations': list,'Shelter-in-place Order':list, 'K-12 School Closure':list,'Non-essential Businesses Closure':list}).reset_index()
        quarantine_df = quarantine_df.applymap(strip_nans)
        quarantine_df['lockdown_type'] = quarantine_df.apply(lambda x: create_lockdown_type_world(x, 0), axis=1)
        quarantine_df['emoji_string'] = quarantine_df.apply(lambda x: create_lockdown_type_world(x, 1), axis=1)
        quarantine_df['lockdown_type'].replace('', np.nan, inplace=True)
        quarantine_df = quarantine_df.dropna(subset = ['lockdown_type'])
        quarantine_df = quarantine_df.groupby(['lockdown_date', 'Country_Region']).agg({'lockdown_type': lambda col: '; '.join(col), 'emoji_string':lambda col: ''.join(col)}).reset_index()
        quarantine_cols = ['Country_Region', 'lockdown_date', 'lockdown_type', 'emoji_string']
        quarantine_df = quarantine_df[quarantine_cols]


        def str2emo(x):
            emo = ""
            for char in x.lower():
                emo += emoji_dict[char]
            return emo
        emoji_dict = {'e':'🚨','b':'🛃','t':'💼','c':'🛩️','l':'🏠','g': '👨‍👩‍👧‍👦','s':'🎓','r':'🍔','n':'🏬'}
        quarantine_df["emoji"] = quarantine_df["emoji_string"].apply(str2emo)
        return quarantine_df

    def _ingest_country_quarantine_df_old(self, quarantine_csv):
        quarantine_df = pd.read_csv(quarantine_csv)
        # rename SK
        quarantine_df.loc[quarantine_df.Country_Region == 'Korea, South', 'Country_Region'] = 'South Korea'
        quarantine_df = quarantine_df.loc[quarantine_df.Level == 'Enforcement']
        quarantine_df = quarantine_df.loc[quarantine_df.Type != 'Border Control']
        quarantine_df['Lockdown Type'] = quarantine_df.apply(
            lambda x: x['Scope'] + ' ' + x['Type'], axis=1
        )
        quarantine_cols = ['Country_Region', 'Date Enacted', 'Lockdown Type']
        quarantine_df = quarantine_df[quarantine_cols]
        quarantine_df = quarantine_df.rename(
            columns={'Date Enacted': 'lockdown_date', 'Lockdown Type': 'lockdown_type'}
        )
        quarantine_df.loc[
            quarantine_df.lockdown_type == 'Partial Internal Lockdown', 'lockdown_type'
        ] = 'Region-Specific Countermeasures Begin'
        return quarantine_df

    def _ingest_usa_quarantine_df_old(self, quarantine_csv):
        quarantine_df = pd.read_csv(quarantine_csv)
        # only show statewide bars for now
        quarantine_df = quarantine_df.loc[quarantine_df.Regions == 'All']
        quarantine_df_emergency = quarantine_df.copy()
        quarantine_df = quarantine_df.loc[
            (quarantine_df.Type == 'Level 2 Lockdown') | (quarantine_df.Type == 'Level 1 Lockdown')]
        quarantine_df['Lockdown Type'] = 'Full Lockdown'
        quarantine_cols = ['Province_State', 'Date Enacted', 'Lockdown Type']
        quarantine_df = quarantine_df[quarantine_cols]
        quarantine_df_emergency['Lockdown Type'] = 'Emergency Declared'
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

    def _ingest_usa_quarantine_df(self, quarantine_csv):
        quarantine_df = pd.read_csv(quarantine_csv)

        # emergency declaration = e/E; restaurant closure = r/R
        # border screening = b/B; travel restrictions= t/T; border closures = c/C
        # shelter-in-place = l/L; gathering limitations= g/G; k-12 school closures = s/S
        # non-essential business closure = n/N
        def create_lockdown_type(x, emo_flag):
            s = r = emo_s = ""
            regional_flag = closure_flag = not_the_first_flag = 0
            if x['Coverage'] != 'State-wide':
                r = 'Regional'
                regional_flag = 1
            if x['State of Emergency Declaration'] == "State of Emergency declared":
                s = s + " Declaration of Emergency"
                not_the_first_flag = 1
                emo_s = (emo_s + "e") if (regional_flag == 1) else (emo_s + "E")
            if x['Travel Restrictions'] == x['Travel Restrictions']:
                if not_the_first_flag == 1:
                    s = s + ","
                if "Travel restrictions for out of state travelers" in x['Travel Restrictions']:
                    emo_s = (emo_s + "t") if (regional_flag == 1) else (emo_s + "T")
                if "Border closures" in x['Travel Restrictions']:
                    emo_s = (emo_s + "c") if (regional_flag == 1) else (emo_s + "C")
                s = s + " Border Closure/Visitor Quarantine"
                not_the_first_flag = 1
            if x['Shelter-in-place Order'] == x['Shelter-in-place Order']:
                if not_the_first_flag == 1:
                    s = s + ","
                if x['Shelter-in-place Order'] == "Shelter-in-place order":
                    s = s + " Stay-at-home Order"
                if x['Shelter-in-place Order'] == "Night-time curfew":
                    s = s + " Curfew"
                emo_s = (emo_s + "l") if (regional_flag == 1) else (emo_s + "L")
                not_the_first_flag = 1
            if x['Banning Gatherings of a Certain Size'] == x['Banning Gatherings of a Certain Size']:
                if not_the_first_flag == 1:
                    s = s + ","
                s = s + " Gatherings (>" + str(int(x['Banning Gatherings of a Certain Size'])) + ") Banned"
                emo_s = (emo_s + "g") if (regional_flag == 1) else (emo_s + "G")
                not_the_first_flag = 1
            if x['K-12 School Closure'] == x['K-12 School Closure']:
                if not_the_first_flag == 1:
                    s = s + ","
                s = s + " Closure of Schools"
                emo_s = (emo_s + "s") if (regional_flag == 1) else (emo_s + "S")
                closure_flag = not_the_first_flag = 1
            if x['Bar and Dine-in Restaurant Closure'] == x['Bar and Dine-in Restaurant Closure']:
                if not_the_first_flag == 1:
                    s = s + ","
                s = (s + " Closure of Restaurants") if (closure_flag == 0) else (s + " Restaurants")
                emo_s = (emo_s + "r") if (regional_flag == 1) else (emo_s + "R")
                closure_flag = not_the_first_flag = 1
            if x['Non-essential Businesses Closure'] == x['Non-essential Businesses Closure']:
                if not_the_first_flag == 1:
                    s = s + ","
                s = (s + " Closure of Non-essential Businesses") if (closure_flag == 0) else (
                            s + " Non-essential Businesses")
                emo_s = (emo_s + "n") if (regional_flag == 1) else (emo_s + "N")
                closure_flag = not_the_first_flag = 1
            if emo_flag == 1:
                return emo_s;
            if s == "":
                return s
            return (r + s).strip()

        quarantine_df = quarantine_df.rename(columns={'State': 'Province_State', 'Effective Date': 'lockdown_date'})
        quarantine_df['lockdown_type'] = quarantine_df.apply(lambda x: create_lockdown_type(x, 0), axis=1)
        quarantine_df['emoji'] = quarantine_df.apply(lambda x: create_lockdown_type(x, 1), axis=1)
        quarantine_df['lockdown_type'].replace('', np.nan, inplace=True)
        quarantine_df = quarantine_df.dropna(subset=['lockdown_type'])
        quarantine_df = quarantine_df.groupby(['lockdown_date', 'Province_State']).agg(
            {'lockdown_type': lambda col: '; '.join(col), 'emoji': lambda col: ''.join(col)}
        ).reset_index()
        quarantine_df['emoji'] = quarantine_df['emoji'].map(lambda s: ''.join(
            {
                'e':'🚨','b':'🛃','t':'💼','c':'🛩️','l':'🏠','g': '👨‍👩‍👧‍👦','s':'🎓','r':'🍔','n':'🏬'
            }[c] for c in s.lower()
        ))

        # Breaking up emoji into separate rows for vertical stacking
        # def split(word): 
        #     return [char for char in word]  
        # quarantine_df.emoji_string = quarantine_df.emoji_string.apply(split)
        # quarantine_df = quarantine_df.explode(column="emoji_string")
        # quarantine_df["Jurisdiction"]=quarantine_df.emoji_string.apply(lambda x: "Statewide" if str(x).isupper() else "Regional")
        # quarantine_df.emoji_string = quarantine_df.emoji_string.str.lower()
        # quarantine_df['event_index'] = quarantine_df.groupby(['Province_State','lockdown_date']).cumcount()+1

        # quarantine_cols = ['Province_State', 'lockdown_date', 'lockdown_type', 'emoji',"emoji_string",'event_index']
        quarantine_cols = ['Province_State', 'lockdown_date', 'lockdown_type', 'emoji']
        quarantine_df = quarantine_df[quarantine_cols]
        return quarantine_df

    def _preprocess_quarantine_df(self, df) -> pd.DataFrame:
        quarantine_df = self.quarantine_df.copy()
        quarantine_df[self.x_type] = self.lockdown_type
        quarantine_df = quarantine_df.merge(
            df[[self.groupcol, 'date_of_N', self.xmax]].groupby(self.groupcol).first(),
            on=self.groupcol,
            how='inner'
        )
        quarantine_df[self.X] = quarantine_df.apply(
            lambda x: days_between(x['date_of_N'], x['lockdown_date']), axis=1
        )
        del quarantine_df['date_of_N']
        if self.spec.get('filter_lockdown_rules_beyond_xmax', True):
            quarantine_df = quarantine_df.loc[quarantine_df.x <= quarantine_df.xmax]

        # only retain lockdown events that appear in the chart domain
        quarantine_df = quarantine_df.loc[quarantine_df.x.between(*self.spec.xdomain, inclusive=False)]

        # enrich lockdown events with the chronological index of when they occur
        # (might be useful for downstream vega stuff)
        quarantine_df[self.lockdown_idx] = quarantine_df.sort_values(self.X).groupby(self.groupcol).cumcount()
        return quarantine_df

    def _preprocess_lockdown_info(self, df) -> pd.DataFrame:
        quarantine_df = self._preprocess_quarantine_df(df)
        # for trends, use earliest lockdown that appears... eventually we will want to specify this somehow
        trend_df = quarantine_df.loc[quarantine_df.groupby(self.groupcol).x.idxmax()]
        df = df.merge(
            trend_df.rename(columns={self.X: self.lockdown_x})[[self.groupcol, self.lockdown_x]],
            how='left',
            on=self.groupcol
        )

        # NB (smacke): quick hack to avoid using early days to calculate the counterfactual slope
        df_elim_early = df.loc[df.lockdown_x - df.x < 5]
        idx_before_at_lockdown = df_elim_early.loc[df_elim_early.x <= df_elim_early.lockdown_x].groupby(df_elim_early[self.groupcol]).x.idxmax()
        df_lockdown_y = df_elim_early.loc[idx_before_at_lockdown]
        df_intercept = df_elim_early.loc[df_elim_early.groupby(self.groupcol).x.idxmin()]
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

        # make sure the new rows have Y, lockdown_x, and lockdown_y
        quarantine_df = quarantine_df.merge(
            df[[
                self.groupcol, self.X, self.Y, self.lockdown_x, self.lockdown_y
            ]].groupby([self.groupcol, self.X]).first(),
            on=[self.groupcol, self.X],
            how='left'
        )

        # now add lockdown info as new rows in our df
        df = df.append(quarantine_df, ignore_index=True, sort=False)
        return df

    def _preprocess_df(self) -> pd.DataFrame:
        df = self.df.copy()
        df = df.loc[df[self.groupcol] != 'Veteran Hospitals']
        df[self.x_type] = 'normal'
        if self.ycol_is_cumulative:
            df[self.Y] = df[self.ycol]
        else:
            df[self.Y] = np.zeros_like(df[self.ycol])
            for group in df[self.groupcol].unique():
                pred = df[self.groupcol] == group
                df.loc[pred, self.Y] = df.loc[pred, self.ycol].cumsum()

        if self.top_k_groups is not None:
            # force showing India, Greece, SK, Denmark
            top_k_groups = list(
                set(
                    df.groupby(self.groupcol)[self.Y].max().nlargest(self.top_k_groups).index
                ) | {'India', 'Greece', 'South Korea', 'Denmark'}
            )
            df = df.loc[df[self.groupcol].isin(top_k_groups)]

        df = self.start_criterion.transform(self, df)

        if 'xdomain' in self.spec:
            xmin, xmax = self.spec.xdomain[0], self.spec.xdomain[1]
            df = df.loc[(df.x >= xmin) & (df.x <= xmax)]
        if 'ydomain' in self.spec:
            ymin, ymax = self.spec.ydomain[0], self.spec.ydomain[1]
            df = df.loc[(df.y >= ymin) & (df.y <= ymax)]

        # populate each group with max x value appearing in domain
        xmax = df.loc[df.groupby(self.groupcol).x.idxmax()]
        df = df.merge(
            xmax.rename(columns={self.X: self.xmax})[[self.groupcol, self.xmax]],
            how='left',
            on=self.groupcol
        )

        if self.quarantine_df is not None:
            df = self._preprocess_lockdown_info(df)

        groups = df.groupby(self.groupcol).first().reset_index().sort_values(self.groupcol)
        groups['group_idx'] = np.arange(len(groups[self.groupcol]))
        df = df.merge(
            groups[[self.groupcol, 'group_idx']],
            how='left',
            on=self.groupcol
        )

        readable_group_name = self.spec.get('readable_group_name', None)
        if readable_group_name is not None:
            readable_group_name = self.spec._get_legend_title()
            df[readable_group_name] = df[self.spec.colorby]

        # needed to get alphabetic legend
        df = df.sort_values(by=[self.groupcol, self.X])
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

    def set_font(self, font: str):
        self.spec.font = font
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

    def set_axes_title_fontsize(self, fontsize):
        self.spec.axes_title_fontsize = fontsize
        return self

    def set_background(self, color):
        self.spec.background = color
        return self

    def set_extrap_clip_to_ydomain(self, clip=True):
        self.spec.extrap_clip_to_ydomain = clip
        return self

    def set_grid(self, grid):
        self.spec.grid = grid
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
        ).set_extrap_clip_to_ydomain(
        ).set_interactive(False).set_width(
            self.spec.DEFAULT_WIDTH
        ).set_height(
            self.spec.DEFAULT_HEIGHT
        ).set_grid(
            True
        ).set_colormap()
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
