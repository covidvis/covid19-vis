import altair as alt
import numpy as np
import pandas as pd

from .dot_dict import DotDict


def _fontSettings(font):
    return lambda: {
        "config": {
            "title": {'font': font},
            "axis": {
                "labelFont": font,
                "titleFont": font
            },
            "header": {
                "labelFont": font,
                "titleFont": font
            },
            "legend": {
                "labelFont": font,
                "titleFont": font
            }
        }
    }


def _ensure_parens(expr):
    return f'({expr})'


class ChartSpec(DotDict):
    """
    A wrapper around a dictionary capturing all the state that determines how
    to generate a Vega-Lite spec, given a pandas dataframe as input.
    Anything that calls into altair happens here.
    """
    click = 'click'
    cursor = 'cursor'
    legend = 'legend'
    lockdown_x = 'lockdown_x'
    X = 'x'
    Y = 'y'
    xmax = 'xmax'
    x_type = 'x_type'
    y_type = 'y_type'
    normal_type = 'normal'
    lockdown_type = 'lockdown'

    TRANSIENT = 'transient'
    DEFAULT_HEIGHT = 400
    DEFAULT_WIDTH = 600
    DEFAULT_POINT_SIZE = 45
    DEFAULT_UNFOCUSED_OPACITY = 0.08
    DEFAULT_AXES_TITLE_FONTSIZE = 16
    #DEFAULT_BACKGROUND_COLOR = '#F2F6F6'
    DEFAULT_BACKGROUND_COLOR = 'white'
    DEFAULT_MIN_TREND_LINE_DAYS = 5
    DEFAULT_FONT = 'Khula'
    MAX_LEGEND_MARKS = 32
    MAX_EMOJI_LEGEND_MARKS = 20
    EMPTY_SELECTION = ''
    COLOR_SCHEME = list(
        map(
            lambda y: '#' + y,
            filter(
                lambda x: x != '',
                [(
                    "4e79a7f28e2ce1575976b7b259a14fedc949af7aa1ff9da79c755fbab0ab"
                    "1f77b4ff7f0e2ca02cd627289467bd8c564be377c27f7f7fbcbd2217becf"
                    "a6cee31f78b4b2df8a33a02cfb9a99e31a1cfdbf6fff7f00cab2d66a3d9affff99b15928"
                    "7fc97fbeaed4fdc086ffff99386cb0f0027fbf5b17666666"
                    "1b9e77d95f027570b3e7298a66a61ee6ab02a6761d666666"
                )[i:i+6] for i in range(0, 1000, 6)]
            )
        )
    ) + [
        'red', 'blue', 'green', 'purple', 'orange',
    ]

    def validate(self, df):
        if 'lines' not in self and 'points' not in self:
            raise ValueError('should have at least one of lines or points')
        if self.X not in df.columns:
            raise ValueError('dataframe should have an x column')
        if self.Y not in df.columns:
            raise ValueError('dataframe should have a y column')
        if not self.get('click_selection', False) and not self.get('legend_selection', False):
            raise ValueError('one of click or legend selection should be specified')
        colormap = self.get('colormap', None)
        if colormap is not None:
            if self.detailby != self.colorby:
                raise ValueError('when colormap specified, detailby and colorby should be identical')
            if not isinstance(colormap, dict):
                raise ValueError('expected dictionary for colormap')
        if self.get('legend_selection', False):
            if self.detailby != self.colorby:
                raise ValueError('when legend selection enabled, detailby and colorby should be identical')

    def _get_x(self, shorthand='x:Q'):
        xaxis_kwargs = {}
        if 'xdomain' in self:
            xaxis_kwargs['scale'] = alt.Scale(domain=self.xdomain)
        xtitle = self.get('xtitle', None)
        if xtitle is not None:
            xaxis_kwargs['title'] = xtitle
        if 'grid' in self:
            xaxis_kwargs['axis'] = alt.Axis(grid=self['grid'])
        return alt.X(shorthand, **xaxis_kwargs)

    def _get_y(self, shorthand='y:Q'):
        yaxis_kwargs = {}
        yscale = self.get('yscale', 'linear')
        if 'ydomain' in self:
            yaxis_kwargs['scale'] = alt.Scale(type=yscale, domain=self.ydomain)
        else:
            yaxis_kwargs['scale'] = alt.Scale(type=yscale)
        ytitle = self.get('ytitle', None)
        if ytitle is not None:
            yaxis_kwargs['title'] = ytitle
        if 'grid' in self:
            yaxis_kwargs['axis'] = alt.Axis(grid=self['grid'])
        return alt.Y(shorthand, **yaxis_kwargs)

    def _prefer_transient(self, key, default=None):
        transient = self.get(self.TRANSIENT, None)
        if transient is None:
            return self.get(key, default)
        else:
            return transient.get(key, self.get(key, default))

    @property
    def _font(self):
        return self.get('font', self.DEFAULT_FONT)

    @property
    def _colorby(self):
        return self._prefer_transient('colorby')

    @property
    def _detailby(self):
        return self._prefer_transient('detailby')

    @property
    def _colormap(self):
        return self._prefer_transient('colormap')

    @property
    def _alt_detail(self):
        return alt.Detail(f'{self._detailby}:N')

    @property
    def _alt_color(self):
        extra_color_kwargs = {}
        colormap = self._colormap
        if colormap is not None:
            domain = list(colormap.keys())
            rng = list(colormap.values())
            extra_color_kwargs['scale'] = dict(
                domain=domain, range=rng,
            )
        return alt.Color(f'{self._colorby}:N', legend=None, **extra_color_kwargs)

    @property
    def _yscale(self):
        return self.get('yscale', 'linear')

    @property
    def _height(self):
        return self.get('height', self.DEFAULT_HEIGHT)

    @property
    def _width(self):
        return self.get('width', self.DEFAULT_WIDTH)

    def _click_is_active(self):
        return _ensure_parens(' && '.join([
            f'{str(self.click_selection).lower()}',
            f'isDefined({self.click}.{self._detailby})',
            f'isDefined({self.click}_{self._detailby})',
            f'{self.click}.{self._detailby} != "{self.EMPTY_SELECTION}"'
        ]))

    def _legend_is_active(self):
        return _ensure_parens(' && '.join([
            'isValid(legend_hover)',
            'isValid(legend_hover.group_idx)',
            'legend_hover.group_idx > -1'
        ]))

    def _click_focused(self):
        return _ensure_parens(' && '.join([
            self._click_is_active(),
            f'{self.click}.{self._detailby} == datum.{self._detailby}'
        ]))

    def _legend_hover_focused(self):
        return _ensure_parens(' && '.join([
            self._legend_is_active(),
            f'!{self._click_is_active()}',
            'datum.group_idx == legend_hover.group_idx'
        ]))

    def _in_focus(self):
        return _ensure_parens(f'{self._click_focused()} || {self._legend_hover_focused()}')

    def _someone_has_focus(self):
        return _ensure_parens(f'{self._click_is_active()} || {self._legend_is_active()}')

    def _in_focus_or_none_selected(self):
        return _ensure_parens(f'{self._in_focus()} || !{self._someone_has_focus()}')

    def _click_focused_or_none_selected(self):
        return _ensure_parens(f'{self._click_focused()} || !{self._someone_has_focus()}')

    def _legend_focused_or_none_selected(self):
        return _ensure_parens(f'{self._legend_hover_focused()} || !{self._someone_has_focus()}')

    def _show_trends(self):
        return 'trends.values[0]'

    def _maybe_add_facet(self, base):
        facetby = self.get('facetby', None)
        if facetby is not None:
            base = base.facet(column=f'{facetby}:N')
        return base

    def _make_line_layer(self, base):
        kwargs = dict(x=self._get_x(), y=self._get_y(), detail=self._alt_detail, color=self._alt_color)
        if not self.get('lines', False):
            kwargs['opacity'] = alt.value(0)
        else:
            kwargs['opacity'] = alt.condition(
                self._in_focus_or_none_selected(),
                alt.value(1),
                alt.value(self.get('unfocused_opacity', self.DEFAULT_UNFOCUSED_OPACITY))
            )
        line_layer = base.mark_line(size=3).encode(**kwargs)
        line_layer = line_layer.transform_filter('datum.y !== null')
        line_layer = line_layer.transform_filter(f'datum.x_type == "{self.normal_type}"')
        if self._yscale == 'log':
            line_layer = line_layer.transform_filter('datum.y > 0')
        return line_layer

    def _make_point_layer(self, base, point_size, is_fake):
        kwargs = dict(x=self._get_x(), y=self._get_y(), detail=self._alt_detail, color=self._alt_color)
        if not self.get('points', False) or is_fake:
            kwargs['opacity'] = alt.value(0)
        else:
            kwargs['opacity'] = alt.condition(
                self._in_focus_or_none_selected(),
                alt.value(.4),
                alt.value(self.get('unfocused_opacity', self.DEFAULT_UNFOCUSED_OPACITY))
            )

        point_layer = base.mark_point(size=point_size, filled=True).encode(**kwargs)
        point_layer = point_layer.transform_filter('datum.y !== null')
        point_layer = point_layer.transform_filter(f'datum.x_type == "{self.normal_type}"')
        if self._yscale == 'log':
            point_layer = point_layer.transform_filter('datum.y > 0')
        if is_fake:
            # the first one makes it easier for tooltips to follow since otherwise these guys will stick
            point_layer = point_layer.transform_filter(self._in_focus_or_none_selected())
        return point_layer

    def _make_tooltip_text_layer(self, point_layer, cursor):
        return point_layer.mark_text(
            align='left', dx=5, dy=45, font=self._font
        ).encode(
            text=alt.condition(cursor, 'tooltip_text:N', alt.value(' ')),
            opacity=alt.value(1),
            color=alt.value('black')
        ).transform_calculate(
            tooltip_text=f'datum.{self._detailby} + ": " + datum.y',
            # tooltip_text='datum.y'
        ).transform_filter(self._in_focus())

    def _make_lockdown_icons_layer(self, rules, cursor):
        # return rules.mark_point(size=5,color="red").encode(
        #     x=self._get_x(), y=self._get_y()
        # ).transform_filter(self._in_focus())
        
        # return rules.mark_image(size=5).encode(
        #     x=self._get_x(), y=self._get_y(), 
        #     url='img'
        # ).transform_filter(self._in_focus())
        return rules.mark_text(size=20, dx=-15).encode(
            x=self._get_x(), y=self._get_y(),
            opacity=alt.value(1),
            # opacity=alt.condition(cursor, alt.value(1), alt.value(.5)),
            text=alt.Text('emoji:N')
        )
    
    def _make_lockdown_rules_layer(self, base, do_mark=True):
        if do_mark:
            base = base.mark_rule(size=3, strokeDash=[7, 3])
        return base.encode(
            self._get_x(), detail=self._alt_detail, color=self._alt_color,
        )

    def _make_lockdown_tooltips_layer(self, base, cursor):
        text = 'lockdown_tooltip_text:N'
        if self.get('only_show_lockdown_tooltip_on_hover', False):
            text = alt.condition(cursor, text, alt.value(' '))
        return base.mark_text(align='left', dx=15, dy=0, font=self._font).encode(
            x=self._get_x(),
            y=self._get_y(),
            text=text,
            color=alt.value('black')
        ).transform_calculate(
# AGP        lockdown_tooltip_text=f'datum.{self._detailby} + " " + datum.lockdown_type+ " " +"("+ datum.lockdown_date + ")"'
             # lockdown_tooltip_text=f'datum.lockdown_type+ " " +"("+ datum.lockdown_date + ")"'
             lockdown_tooltip_text=f'datum.lockdown_type+ " " +"("+ datum.lockdown_date + ")"'
        )

    def _make_cursor_selection(self, base, x_bind_col):
        cursor = alt.selection_single(name=self.cursor, nearest=True, on='mouseover',
                                      fields=[x_bind_col], empty='none')
        return cursor, base.mark_point().encode(
            x=f'{x_bind_col}:Q', opacity=alt.value(0),
        ).add_selection(cursor)

    def _collect_tooltip_layers(self, layers, base, cursor):
        if not self.get('has_tooltips', False):
            return
        if self.get('tooltip_points', False):
            layers['tooltip_points'] = layers['points'].mark_point(filled=True).encode(
                opacity=alt.condition(cursor, alt.value(1), alt.value(0))
            ).transform_filter(self._in_focus())
        if self.get('tooltip_text', False):
            layers['tooltip_text'] = self._make_tooltip_text_layer(layers['points'], cursor)
        if self.get('tooltip_rules'):
            layers['tooltip_rules'] = base.mark_rule(
                color='gray'
            ).encode(
                x='x:Q'
            ).transform_filter(
                cursor
            ).transform_filter(self._someone_has_focus())
        lockdown_base = base.transform_filter(
            f'datum.x_type == "{self.lockdown_type}"'
        ).transform_filter(self._in_focus())
        has_lockdown_rules = self.get('lockdown_rules', False)
        if has_lockdown_rules:
            layers['lockdown_rules'] = self._make_lockdown_rules_layer(lockdown_base)
        if has_lockdown_rules or self.get('lockdown_tooltips', False):
            layers['lockdown_tooltips'] = self._make_lockdown_tooltips_layer(lockdown_base, cursor)
        if self.get('lockdown_icons', False):
            layers['lockdown_icons'] = self._make_lockdown_icons_layer(lockdown_base, cursor)


    def _make_lockdown_extrapolation_layer(self, base, trend_select):
        def _add_model_transformation_fields(base_chart):
            ret = base_chart.transform_filter(
                self._show_trends()
            ).transform_filter(
                'datum.lockdown_x != null'
            ).transform_filter(
                'datum.y !== null'
            ).transform_filter(
                'datum.x >= datum.lockdown_x'
            ).transform_filter(
                # only show the trend lines if the main lockdown rule appears after the start of the line
                'datum.lockdown_x > datum.x_start'
            ).transform_filter(
                'datum.xmax - datum.lockdown_x >= {}'.format(
                    self.get('min_trend_line_days', self.DEFAULT_MIN_TREND_LINE_DAYS)
                )
            ).transform_calculate(
                model_y='datum.lockdown_y * pow(datum.lockdown_slope, datum.x - datum.lockdown_x)'
            )
            if 'ydomain' in self and self.get('extrap_clip_to_ydomain', False):
                ret = ret.transform_filter(f'datum.model_y <= {self.ydomain[1]}')
            return ret

        ret = _add_model_transformation_fields(
            base.mark_line(size=5, strokeDash=[1, 1]).encode(
                x=self._get_x('x:Q'),
                y=self._get_y('model_y:Q'),
                detail=self._alt_detail,
                color=self._alt_color,
            )
        )
        ret = ret.transform_filter(self._in_focus())
        return ret

    def _make_extrapolation_tooltip_layer(self, extrap, cursor, trend_select):
        text = 'extrap_text:N'
        x, y = 'x', 'model_y'
        no_max_template = '{}:Q'
        max_template = 'max({}):Q'
        if self.get('only_show_extrapolation_tooltip_on_hover', False):
            text = alt.condition(cursor, text, alt.value(' '))
            x, y = no_max_template.format(x), no_max_template.format(y)
        else:
            x, y = max_template.format(x), max_template.format(y)
        return extrap.mark_text(
            align='center', dx=0, dy=-5, font=self._font
        ).encode(
            x=self._get_x(x),
            y=self._get_y(y),
            text=text,
            opacity=alt.value(1),
            color=alt.value('black')
        ).transform_filter(
            self._show_trends()
        ).transform_calculate(
            extrap_text='"Original trend"'
        ).add_selection(trend_select)

    def _populate_transient_colormap(self, df):
        colormap = self.get('colormap', None)
        if colormap is None:
            return
        colormap = dict(colormap)
        color_scheme_idx = 0
        default_color = self.get('default_color', None)
        for group in df[self._colorby].unique():
            if group in colormap:
                continue
            elif default_color is not None:
                colormap[group] = default_color
                continue
            while self.COLOR_SCHEME[color_scheme_idx] in colormap.values():
                color_scheme_idx += 1
            colormap[group] = self.COLOR_SCHEME[color_scheme_idx]
            color_scheme_idx += 1
        self[self.TRANSIENT]['colormap'] = colormap

    def _get_legend_title(self):
        readable_group_name = self.get('readable_group_name', None)
        if readable_group_name is not None and self.get('legend_selection', False):
            return f'Select_{readable_group_name}'
        elif readable_group_name is not None:
            return readable_group_name
        else:
            return self.colorby

    def _populate_transient_props(self, df):
        self._populate_transient_colormap(df)
        readable_group_name = self.get('readable_group_name', None)
        if readable_group_name is not None and self.get('legend_selection', False):
            self[self.TRANSIENT]['colorby'] = self._get_legend_title()
            self[self.TRANSIENT]['detailby'] = self._get_legend_title()

    def _make_manual_legend(self, df, click_selection):
        groups = df.groupby(self.colorby).first().reset_index().sort_values(self.colorby, ascending=True)
        group_names = list(groups[self.colorby].values)
        if len(group_names) > self.MAX_LEGEND_MARKS:
            raise ValueError(f'max {self.MAX_LEGEND_MARKS} supported for now')
        idx = list(self.MAX_LEGEND_MARKS + 1 - np.arange(len(group_names)))
        row_type = ['normal'] * len(idx)
        idx.append(self.MAX_LEGEND_MARKS + 2)
        row_type.append('title')
        group_names.append(f'Select {self.get("readable_group_name", "line")}')
        xs = np.zeros_like(idx)
        leg_df = pd.DataFrame({
            'idx': idx * 3,
            'group_idx': list(groups['group_idx']) + (2 * len(idx) + 1) * [-1],
            self._colorby: group_names * 3,
            'x': list(xs) + list(xs-1) + list(xs+20),
            'row_type': row_type + ['fake'] * 2 * len(idx)
        })

        axis = alt.Axis(domain=False, ticks=False, orient='right', grid=False, labels=False)
        base = alt.Chart(
            leg_df, height=self._height, width=100,
        )

        def _make_base(base, **extra_kwargs):
            return base.encode(
                x=alt.X('x:Q', title='', axis=axis, scale=alt.Scale(domain=(-1, 20))),
                y=alt.Y('idx:Q', title='', axis=axis, scale=alt.Scale(domain=(0, self.MAX_LEGEND_MARKS))),
                color=self._alt_color,
                detail=self._alt_detail,
                **extra_kwargs
            )

        legend_points = _make_base(
            base, opacity=alt.condition(
                self._click_focused_or_none_selected(),
                alt.value(1),
                alt.value(0.4),
            )
        ).mark_point(shape='diamond', filled=True, size=160)
        legend_points = legend_points.transform_filter('datum.row_type == "normal"')
        cursor = alt.selection_single(name='legend_hover', nearest=True, on='mouseover',
                                      fields=['group_idx'], empty='none')
        points_layer = legend_points
        if self.get('legend_selection', False):
            points_layer = points_layer.add_selection(click_selection)
        layers = [
            _make_base(base).mark_point(size=0).add_selection(cursor),
            legend_points.mark_text(
                align='left', dx=10, font=self._font,
            ).encode(
                text=f'{self._colorby}:N',
                color=alt.value('black'),
                opacity=alt.condition(
                    self._in_focus_or_none_selected(),
                    alt.value(1),
                    alt.value(0.4),
                ),
            ),
            points_layer,
            _make_base(base).mark_text(
                align='left', dx=-10, dy=-5, font=self._font, fontSize=16,
            ).encode(
                text=f'{self._colorby}:N',
                color=alt.value('black'),
            ).transform_filter('datum.row_type == "title"')
        ]
        return alt.layer(*layers, view=alt.ViewConfig(strokeOpacity=0))

    def _make_emoji_legend(self, df):
        emojis = list(df['emoji'].dropna().unique())
        emojis_flattened = []
        for s in emojis:
            emojis_flattened.extend([c for c in s])

        def _emoji_gen():
            cur_emoji = emojis_flattened[0]
            saw_sep = False
            for c in emojis_flattened[1:]:
                if not saw_sep and c != u'\u200d':
                    yield cur_emoji
                    cur_emoji = c
                else:
                    cur_emoji += c
                saw_sep = (c == u'\u200d')
        # TODO (smacke): not sure what this weird unicode emoji modifier is
        emojis = sorted(set(_emoji_gen()) - {'️'})
        if len(emojis) > self.MAX_EMOJI_LEGEND_MARKS:
            raise ValueError(f'max {self.MAX_EMOJI_LEGEND_MARKS} supported for now')
        idx = list(self.MAX_EMOJI_LEGEND_MARKS + 1 - np.arange(len(emojis)))
        row_type = ['normal'] * len(idx)
        idx.append(self.MAX_EMOJI_LEGEND_MARKS + 2)
        idx = list(np.array(idx) - 2.25)
        row_type.append('title')
        emojis.append('Intervention type')
        leg_df = pd.DataFrame({'idx': idx, 'emoji': emojis, 'zero': np.zeros_like(idx), 'row_type': row_type})
        axis = alt.Axis(domain=False, ticks=False, orient='right', grid=False, labels=False)
        base = alt.Chart(
            leg_df, height=self._height, width=10,
        ).encode(
            x=alt.X('zero:Q', title='', axis=axis),
            y=alt.Y('idx:Q', title='', axis=axis, scale=alt.Scale(domain=(0, self.MAX_EMOJI_LEGEND_MARKS))),
            color=self._alt_color,
            detail=self._alt_detail,
        )
        layers = [
            base.mark_text(
                align='left', font=self._font, fontSize=12,
            ).encode(
                text='emoji_and_description:N',
                color=alt.value('black'),
            ).transform_calculate(
                emoji_and_description='datum.emoji + " " + {'
                                      '"👨‍👩‍👧‍👦": "Gatherings banned", '
                                      '"🏠": "Stay at home order", '
                                      '"🍽": "Restaurant closures", '
                                      '"🏬": "Non-ess. businesses closed", '
                                      '"🚨": "State of emergency declared", '
                                      '"🎓": "School closures", '
                                      '"🛩️": "Travel restrictions", '
                                      '"💼": "Border cont. or quarantine", '
                                      '"🛃": "Forgot what this meant", '
                                      '}[datum.emoji]'
            ).transform_filter('datum.row_type == "normal"'),
            base.mark_text(
                align='left', dy=-5, font=self._font, fontSize=16,
            ).encode(
                text='emoji:N',
                color=alt.value('black'),
            ).transform_filter('datum.row_type == "title"')
        ]
        return alt.layer(*layers, view=alt.ViewConfig(strokeOpacity=0))

    def compile(self, df):
        self.validate(df)
        self[self.TRANSIENT] = DotDict()
        try:
            self._populate_transient_props(df)
            base = alt.Chart(
                df,
                width=self._width,
                height=self._height
            )
            layers = {}

            dropdown_options = [self.EMPTY_SELECTION]
            dropdown_name = " "
            if self.get('click_selection', False):
                dropdown_options.extend(list(df[self._detailby].unique()))
                dropdown_name = f'Select {self.get("readable_group_name", self.detailby)}: '
            dropdown = alt.binding_select(options=dropdown_options, name=dropdown_name)
            extra_click_selection_kwargs = {}
            click_init = self.get('click_selection_init', None)
            if click_init is not None:
                extra_click_selection_kwargs['init'] = {self._detailby: click_init}
            click_selection = alt.selection_single(
                fields=[self._detailby], on='click', name=self.click, empty='all',
                bind=dropdown,
                clear='dblclick', **extra_click_selection_kwargs
            )

            # put a fake layer in first with no click selection
            # since it has X and Y, it will help chart.interactive() to find x and y fields to bind to,
            # allowing us to pan up and down and zoom over both axes instead of just 1.
            layers['fake_interactive'] = base.mark_line().encode(
                x=self._get_x(), y=self._get_y()
            ).transform_filter('false')

            # Next goes the mouseover interaction layer (needs to happen before click selection layer).
            # We are binding the hover interaction to the 'x' column in the dataframe, so any other layers
            # that make use of the hover interaction need to use this column for their x encoding in Altair.
            # This means that things like lockdown tooltips need to use 'x' and then apply a filter to filter
            # out non-lockdown days if they want work with the mouseover interaction.
            cursor, selectors = self._make_cursor_selection(base, x_bind_col=self.X)
            layers['selectors'] = selectors

            # The first layer with a specified color channel is used to generate the legend.
            # as such, we need to make sure the marks in the first layer w/ specified color channel are not translucent,
            # otherwise we'll get a blank legend.
            # We put a fake layer in here before we add any other layers w/ color channel specified, and we
            # furthermore add the legend selection to it b/c it also seems like a multi-selection bound to the
            # legend needs to be added to the layer that generates the legend.
            # layers['legend'] = base.mark_point(size=0).encode(
            #     x=self._get_x(), y=self._get_y(), color=self._alt_color
            # )  # .add_selection(legend_selection)

            # Put a fake layer in first to attach the click selection to. We use a fake layer for this for a few reasons.
            # 1. It's not used as a base layer, so we won't get errors
            #    about the spec having the selection added multiple times.
            # 2. We need a layer that has nice fat points that are easy to click for adding the click_selection to.
            #    Since the layer has fat points, however, the points need to be translucent, and since they
            #    need to be translucent, this layer cannot be the first layer that specifies color channel
            #    and similarly cannot be the layer with the legend_selection added on.
            layers['fake_points'] = self._make_point_layer(
                base, point_size=400, is_fake=True
            ).add_selection(click_selection)

            # now the meaty layers with actual content
            layers['lines'] = self._make_line_layer(base)
            layers['points'] = self._make_point_layer(
                base,
                point_size=self.get('point_size', self.DEFAULT_POINT_SIZE),
                is_fake=False
            )

            self._collect_tooltip_layers(layers, base, cursor)

            if self.get('lockdown_extrapolation', False):
                trend_checkbox = alt.binding_checkbox(name='Show trend lines for selected ')
                trend_select = alt.selection_single(bind=trend_checkbox, name='trends', init={'values': True})
                layers['model_lines'] = self._make_lockdown_extrapolation_layer(base, trend_select)
                layers['model_tooltip'] = self._make_extrapolation_tooltip_layer(
                    layers['model_lines'], cursor, trend_select
                )

            layered = alt.layer(*layers.values())
            layered = self._maybe_add_facet(layered)
            if self.get('interactive', False):
                layered = layered.interactive(bind_x=True, bind_y=True)
            if self.get('title', False):
                layered.title = self.get('title')
            if self.get('emoji_legend', False):
                final_chart = alt.hconcat(self._make_emoji_legend(df), layered)
            else:
                final_chart = layered
            final_chart = alt.hconcat(final_chart, self._make_manual_legend(df, click_selection))
            final_chart = final_chart.configure(background=self.get('background', self.DEFAULT_BACKGROUND_COLOR))
            final_chart = final_chart.configure_axis(
                titleFontSize=self.get('axes_title_fontsize', self.DEFAULT_AXES_TITLE_FONTSIZE),
            )
            final_chart = final_chart.configure_title(font=self._font)
            alt.themes.register('customFont', _fontSettings(self._font))
            alt.themes.enable('customFont')
            return final_chart
        finally:
            del self[self.TRANSIENT]
