import altair as alt

from .dot_dict import DotDict


class ChartSpec(DotDict):
    """
    A wrapper around a dictionary capturing all the state that determines how
    to generate a Vega-Lite spec, given a pandas dataframe as input.
    Anything that calls into altair happens here.
    """
    click = 'click'
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

    def _only_visible_when_in_focus(self, base, click_selection):
        if click_selection is not None:
            base = base.transform_filter(
                self._clicked_with_focus()
            )
        return base

    def _clicked_or_empty(self):
        return ' || '.join([
            f'!isDefined({self.click}.{self.detailby})',
            f'!isDefined({self.click}_{self.detailby})',
            f'{self.click}.{self.detailby} == datum.{self.detailby}',
            f'{self.click}.{self.detailby} == "{self.EMPTY_SELECTION}"'
        ])

    def _clicked_with_focus(self):
        return f'isDefined({self.click}.{self.detailby}) && {self.click}.{self.detailby} == datum.{self.detailby}'

    def _someone_has_focus(self):
        return ' && '.join([
            f'isDefined({self.click}.{self.detailby})',
            f'isDefined({self.click}_{self.detailby})',
            f'{self.click}.{self.detailby} != "{self.EMPTY_SELECTION}"'
        ])

    def _maybe_add_facet(self, base):
        facetby = self.get('facetby', None)
        if facetby is not None:
            base = base.facet(column=f'{facetby}:N')
        return base

    def _make_line_layer(self, base, click_selection):
        kwargs = dict(x=self._get_x(), y=self._get_y(), detail=self._alt_detail, color=self._alt_color)
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
        kwargs = dict(x=self._get_x(), y=self._get_y(), detail=self._alt_detail, color=self._alt_color)
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
        point_layer = base.mark_point(size=400 if is_fake else 45, filled=True).encode(**kwargs)
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
            tooltip_text=f'datum.{self.detailby} + ": " + datum.y'
        )
        return self._only_visible_when_in_focus(ret, click_selection)

    def _make_lockdown_rules_layer(self, base, click_selection):
        ret = base.mark_rule(strokeDash=[7, 3]).encode(
            x='x:Q', detail=self._alt_detail, color=self._alt_color
        ).transform_filter('datum.x == datum.lockdown_x')
        return self._only_visible_when_in_focus(ret, click_selection)

    def _make_lockdown_tooltips_layer(self, rules, nearest, click_selection):
        ret = rules.mark_text(align='left', dx=5, dy=-200).encode(
            text=alt.condition(nearest, 'lockdown_tooltip_text:N', alt.value(' '))
        ).transform_calculate(
            lockdown_tooltip_text=f'datum.{self.detailby} + " " + datum.lockdown_type'
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

    def _make_lockdown_extrapolation_layer(self, base, click_selection, nearest):
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
            base.mark_line(size=3, strokeDash=[1, 1]).encode(
                x=self._get_x('x:Q'),
                y=self._get_y('model_y:Q'),
                detail=self._alt_detail,
                color=self._alt_color,
            )
        )
        ret = self._only_visible_when_in_focus(ret, click_selection)
        return ret

    def _make_extrapolation_tooltip_layer(self, extrap, nearest):
        return extrap.mark_text(align='left', dx=5, dy=-20).encode(
            text=alt.condition(nearest, 'extrap_text:N', alt.value(' ')),
            opacity=alt.value(1)
        ).transform_calculate(
            extrap_text=f'"trend at lockdown for " + datum.{self.detailby}'
        )

    def _collect_facet_layers(self, layers):
        keys = list(layers.keys())
        for key in keys:
            layers[key] = self._maybe_add_facet(layers[key])

    def compile(self, df):
        self.validate(df)
        base = alt.Chart(
            df,
            width=self.get('width', self.DEFAULT_WIDTH),
            height=self.get('height', self.DEFAULT_HEIGHT)
        )
        layers = {}
        click_selection = None
        if self.get('click_selection', False):
            dropdown_options = [self.EMPTY_SELECTION] + list(df[self.detailby].unique())
            dropdown = alt.binding_select(options=dropdown_options, name=f'Filter on {self.detailby}: ')
            click_selection = alt.selection_single(
                fields=[self.detailby], on='click', name=self.click, empty='all',
                bind=dropdown
            )
        # put a fake layer in first with no click selection
        # since it has X and Y, it will help with chart.interactive()
        layers['fake_points_for_interactive'] = self._make_point_layer(base, None, is_fake=True)

        # next goes the tooltip selector layer (needs to happen before click selection layer)
        nearest, selectors = self._make_nearest_selectors(base)
        layers['selectors'] = selectors

        # put a fake layer in first to attach the click selection to
        layers['fake_points'] = self._make_point_layer(base, click_selection, is_fake=True)

        layers['lines'] = self._make_line_layer(base, click_selection)
        layers['points'] = self._make_point_layer(base, click_selection)

        self._collect_tooltip_layers(layers, base, nearest, click_selection)

        if self.get('lockdown_extrapolation', False):
            layers['model_lines'] = self._make_lockdown_extrapolation_layer(base, click_selection, nearest)
            layers['model_tooltip'] = self._make_extrapolation_tooltip_layer(layers['model_lines'], nearest)

        # self._collect_facet_layers(layers)

        layered = alt.layer(*layers.values())
        layered = self._maybe_add_facet(layered)
        if self.get('interactive', False):
            layered = layered.interactive()
        return layered
