import altair as alt

from .dot_dict import DotDict


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

    def _prefer_transient(self, key, default=None):
        transient = self.get(self.TRANSIENT, None)
        if transient is None:
            return self.get(key, default)
        else:
            return transient.get(key, self.get(key, default))

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
        return alt.Color(f'{self._colorby}:N', **extra_color_kwargs)

    @property
    def _yscale(self):
        return self.get('yscale', 'linear')

    def _ensure_parens(self, expr):
        return f'({expr})'

    def _legend_is_active(self):
        conditions = [
            f'{str(self.legend_selection).lower()}',
            f'isDefined({self.legend}.{self._detailby})',
            f'(!isDefined({self.click}) || !isDefined({self.click}_{self._detailby}))',
        ]
        # TODO (smacke): legend_tuple not defined for facet charts;
        # need a more reliable way to detect if we clicked on a blank area
        if self.get('facetby', None) is None:
            conditions.extend([
                f'isValid({self.legend}_tuple)',
                f'!isDefined({self.legend}_tuple.unit)',
            ])
        else:
            conditions.append(f'isValid({self.legend}_{self._detailby}_legend)')
        return self._ensure_parens(' && '.join(conditions))

    def _click_is_active(self):
        return self._ensure_parens(' && '.join([
            f'{str(self.click_selection).lower()}',
            f'isDefined({self.click}.{self._detailby})',
            f'isDefined({self.click}_{self._detailby})',
            f'{self.click}.{self._detailby} != "{self.EMPTY_SELECTION}"'
        ]))

    def _legend_focused(self):
        return self._ensure_parens(' && '.join([
            f'{self._legend_is_active()}',
            f'indexof({self.legend}.{self._detailby}, datum.{self._detailby}) >= 0'
        ]))

    def _click_focused(self):
        return self._ensure_parens(' && '.join([
            self._click_is_active(),
            f'{self.click}.{self._detailby} == datum.{self._detailby}'
        ]))

    def _in_focus(self):
        return self._ensure_parens(f'{self._click_focused()} || {self._legend_focused()}')

    def _someone_has_focus(self):
        return self._ensure_parens(f'{self._click_is_active()} || {self._legend_is_active()}')

    def _in_focus_or_none_selected(self):
        return self._ensure_parens(f'{self._in_focus()} || !{self._someone_has_focus()}')

    def _show_trends(self):
        return '!isValid(trends_tuple) || trends_tuple.values[0]'

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
        return point_layer.mark_text(align='left', dx=5, dy=-5).encode(
            text=alt.condition(cursor, 'tooltip_text:N', alt.value(' ')),
            opacity=alt.value(1),
            color=alt.value('black')
        ).transform_calculate(
            tooltip_text=f'datum.{self._detailby} + ": " + datum.y'
            # tooltip_text='datum.y'
        ).transform_filter(self._in_focus())

    def _make_lockdown_rules_layer(self, base):
        return base.mark_rule(size=3, strokeDash=[7, 3]).encode(
            x='x:Q', detail=self._alt_detail, color=self._alt_color
        ).transform_filter(
            f'datum.x_type == "{self.lockdown_type}"'
        ).transform_filter(self._in_focus())

    def _make_lockdown_tooltips_layer(self, rules, cursor):
        text = 'lockdown_tooltip_text:N'
        if self.get('only_show_lockdown_tooltip_on_hover', False):
            text = alt.condition(cursor, text, alt.value(' ')),
        return rules.mark_text(align='left', dx=15, dy=0).encode(
            y=self._get_y('y:Q'),
            text=text,
            color=alt.value('black')
        ).transform_calculate(
            lockdown_tooltip_text=f'datum.{self._detailby} + " " + datum.lockdown_type+ " " +"("+ datum.lockdown_date + ")"'
        ).transform_filter(self._in_focus())

    def _make_cursor_selection(self, base):
        cursor = alt.selection_single(name=self.cursor, nearest=True, on='mouseover',
                                      fields=['x'], empty='none')
        return cursor, base.mark_point().encode(
            x='x:Q', opacity=alt.value(0),
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
        if self.get('lockdown_rules', False):
            layers['lockdown_rules'] = self._make_lockdown_rules_layer(base)
            layers['lockdown_tooltips'] = self._make_lockdown_tooltips_layer(
                layers['lockdown_rules'], cursor
            )

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
        return extrap.mark_text(align='center', dx=0, dy=-5).encode(
            x=self._get_x(x),
            y=self._get_y(y),
            text=text,
            opacity=alt.value(1),
            color=alt.value('black')
        ).transform_filter(
            self._show_trends()
        ).transform_calculate(
            #extrap_text=f'"Original trend for " + datum.{self._detailby}'
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

    def compile(self, df):
        self.validate(df)
        self[self.TRANSIENT] = DotDict()
        try:
            self._populate_transient_props(df)
            base = alt.Chart(
                df,
                width=self.get('width', self.DEFAULT_WIDTH),
                height=self.get('height', self.DEFAULT_HEIGHT)
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
                bind=dropdown, clear='dblclick', **extra_click_selection_kwargs
            )

            legend_selection = alt.selection_multi(
                fields=[self._colorby], on='click', name=self.legend, empty='all',
                bind='legend', clear='dblclick',
            )

            # put a fake layer in first with no click selection
            # since it has X and Y, it will help chart.interactive() to find x and y fields to bind to,
            # allowing us to pan up and down and zoom over both axes instead of just 1.
            layers['fake_interactive'] = base.mark_line().encode(
                x=self._get_x(), y=self._get_y()
            ).transform_filter('false')

            # next goes the tooltip selector layer (needs to happen before click selection layer)
            cursor, selectors = self._make_cursor_selection(base)
            layers['selectors'] = selectors

            # The first layer with a specified color channel is used to generate the legend.
            # as such, we need to make sure the marks in the first layer w/ specified color channel are not translucent,
            # otherwise we'll get a blank legend.
            # We put a fake layer in here before we add any other layers w/ color channel specified, and we
            # furthermore add the legend selection to it b/c it also seems like a multi-selection bound to the
            # legend needs to be added to the layer that generates the legend.
            layers['legend'] = base.mark_point(size=0).encode(
                x=self._get_x(), y=self._get_y(), color=self._alt_color
            ).add_selection(legend_selection)

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
            layered = layered.configure_legend(symbolType='diamond')
            if self.get('interactive', False):
                layered = layered.interactive(bind_x=True, bind_y=True)
            if self.get('title', False):
                layered.title = self.get('title')
            layered = layered.configure(background=self.get('background', self.DEFAULT_BACKGROUND_COLOR))
            layered = layered.configure_axis(
                titleFontSize=self.get('axes_title_fontsize', self.DEFAULT_AXES_TITLE_FONTSIZE)
            )
            return layered
        finally:
            del self[self.TRANSIENT]
