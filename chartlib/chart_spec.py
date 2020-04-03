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
    lockdown_X = 'lockdown_x'
    X = 'x'
    Y = 'y'
    DEFAULT_HEIGHT = 400
    DEFAULT_WIDTH = 600
    EMPTY_SELECTION = ''

    def validate(self, df):
        if 'lines' not in self and 'points' not in self:
            raise ValueError('should have at least one of lines or points')
        if self.X not in df.columns:
            raise ValueError('dataframe should have an x column')
        if self.Y not in df.columns:
            raise ValueError('dataframe should have a y column')
        if not self.get('click_selection', False) and not self.get('legend_selection', False):
            raise ValueError('one of click or legend selection should be specified')

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
    def _alt_detail(self):
        return alt.Detail(f'{self.detailby}:N')

    @property
    def _alt_color(self):
        return alt.Color(f'{self.colorby}:N')

    @property
    def _yscale(self):
        return self.get('yscale', 'linear')

    def _ensure_parens(self, expr):
        return f'({expr})'

    def _legend_is_active(self):
        return self._ensure_parens(' && '.join([
            f'{str(self.legend_selection).lower()}',
            f'isDefined({self.legend}.{self.detailby})',
            # TODO (smacke): legend_tuple not defined for facet charts; need a more reliable way to detect if we clicked on a blank area
            f'!isDefined({self.legend}_tuple.unit)' if self.get('facetby', None) is None else f'isValid({self.legend}_{self.detailby}_legend)',
            f'(!isDefined({self.click}) || !isDefined({self.click}_{self.detailby}))',
        ]))

    def _click_is_active(self):
        return self._ensure_parens(' && '.join([
            f'{str(self.click_selection).lower()}',
            f'isDefined({self.click}.{self.detailby})',
            f'isDefined({self.click}_{self.detailby})',
            f'{self.click}.{self.detailby} != "{self.EMPTY_SELECTION}"'
        ]))

    def _legend_focused(self):
        return self._ensure_parens(' && '.join([
            f'{self._legend_is_active()}',
            f'indexof({self.legend}.{self.detailby}, datum.{self.detailby}) >= 0'
        ]))

    def _click_focused(self):
        return self._ensure_parens(' && '.join([
            self._click_is_active(),
            f'{self.click}.{self.detailby} == datum.{self.detailby}'
        ]))

    def _in_focus(self):
        return self._ensure_parens(f'{self._click_focused()} || {self._legend_focused()}')

    def _someone_has_focus(self):
        return self._ensure_parens(f'{self._click_is_active()} || {self._legend_is_active()}')

    def _in_focus_or_none_selected(self):
        return self._ensure_parens(f'{self._in_focus()} || !{self._someone_has_focus()}')

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
            kwargs['opacity'] = alt.condition(self._in_focus_or_none_selected(), alt.value(1), alt.value(.1))
        line_layer = base.mark_line(size=3).encode(**kwargs)
        line_layer = line_layer.transform_filter('datum.y !== null')
        if self._yscale == 'log':
            line_layer = line_layer.transform_filter('datum.y > 0')
        return line_layer

    def _make_point_layer(self, base, point_size, is_fake):
        kwargs = dict(x=self._get_x(), y=self._get_y(), detail=self._alt_detail, color=self._alt_color)
        if not self.get('points', False) or is_fake:
            kwargs['opacity'] = alt.value(0)
        else:
            kwargs['opacity'] = alt.condition(
                self._in_focus_or_none_selected(), alt.value(.4), alt.value(.1)
            )

        point_layer = base.mark_point(size=point_size, filled=True).encode(**kwargs)
        point_layer = point_layer.transform_filter('datum.y !== null')
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
            tooltip_text=f'datum.{self.detailby} + ": " + datum.y'
        ).transform_filter(self._in_focus())

    def _make_lockdown_rules_layer(self, base):
        return base.mark_rule(size=3, strokeDash=[7, 3]).encode(
            x='x:Q', detail=self._alt_detail, color=self._alt_color
        ).transform_filter(
            'datum.x == datum.lockdown_x'
        ).transform_filter(self._in_focus())

    def _make_lockdown_tooltips_layer(self, rules, cursor):
        return rules.mark_text(align='left', dx=5, dy=-200).encode(
            text=alt.condition(cursor, 'lockdown_tooltip_text:N', alt.value(' ')),
            color=alt.value('black')
        ).transform_calculate(
            lockdown_tooltip_text=f'datum.{self.detailby} + " " + datum.lockdown_type'
        ).transform_filter(self._in_focus())

    def _make_cursor_selection(self, base):
        cursor = alt.selection_single(name=self.cursor, nearest=True, on='mouseover',
                                      fields=['x'], empty='none')
        return cursor, base.mark_point().encode(
            x='x:Q', opacity=alt.value(0),
        ).add_selection(cursor)

    def _collect_tooltip_layers(self, layers, base, nearest):
        if not self.get('has_tooltips', False):
            return
        if self.get('tooltip_points', False):
            layers['tooltip_points'] = layers['points'].mark_point(filled=True).encode(
                opacity=alt.condition(nearest, alt.value(1), alt.value(0))
            ).transform_filter(self._in_focus())
        if self.get('tooltip_text', False):
            layers['tooltip_text'] = self._make_tooltip_text_layer(layers['points'], nearest)
        if self.get('tooltip_rules'):
            layers['tooltip_rules'] = base.mark_rule(
                color='gray'
            ).encode(
                x='x:Q'
            ).transform_filter(
                nearest
            ).transform_filter(self._someone_has_focus())
        if self.get('lockdown_rules', False):
            layers['lockdown_rules'] = self._make_lockdown_rules_layer(base)
            layers['lockdown_tooltips'] = self._make_lockdown_tooltips_layer(
                layers['lockdown_rules'], nearest
            )

    def _make_lockdown_extrapolation_layer(self, base):
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

    def _make_extrapolation_tooltip_layer(self, extrap, nearest):
        return extrap.mark_text(align='left', dx=5, dy=-20).encode(
            text=alt.condition(nearest, 'extrap_text:N', alt.value(' ')),
            opacity=alt.value(1),
            color=alt.value('black')
        ).transform_calculate(
            extrap_text=f'"trend at lockdown for " + datum.{self.detailby}'
        )

    def compile(self, df):
        self.validate(df)
        base = alt.Chart(
            df,
            width=self.get('width', self.DEFAULT_WIDTH),
            height=self.get('height', self.DEFAULT_HEIGHT)
        )
        layers = {}

        dropdown_options = [self.EMPTY_SELECTION]
        dropdown_name = " "
        if self.get('click_selection', False):
            dropdown_options.extend(list(df[self.detailby].unique()))
            dropdown_name = f'Select {self.detailby}: '
        dropdown = alt.binding_select(options=dropdown_options, name=dropdown_name)
        click_selection = alt.selection_single(
            fields=[self.detailby], on='click', name=self.click, empty='all',
            bind=dropdown, clear='dblclick',
        )

        legend_selection = alt.selection_multi(
            fields=[self.detailby], on='click', name=self.legend, empty='all',
            bind='legend', clear='dblclick'
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
        layers['points'] = self._make_point_layer(base, point_size=45, is_fake=False)

        self._collect_tooltip_layers(layers, base, cursor)

        if self.get('lockdown_extrapolation', False):
            layers['model_lines'] = self._make_lockdown_extrapolation_layer(base)
            layers['model_tooltip'] = self._make_extrapolation_tooltip_layer(layers['model_lines'], cursor)

        layered = alt.layer(*layers.values())
        layered = self._maybe_add_facet(layered)
        layered = layered.configure_legend(symbolType='diamond')
        if self.get('interactive', False):
            layered = layered.interactive(bind_x=True, bind_y=True)
        if self.get('title', False):
            layered.title = self.get('title')
        return layered
