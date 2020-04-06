#!/usr/bin/env python
import sys

import pandas as pd
import yaml

from chartlib import CovidChart, DaysSinceNumReached


def make_jhu_country_chart() -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    jhu_df = jhu_df[jhu_df['Province_State'].isnull()]

    chart = CovidChart(
        jhu_df,
        groupcol='Country_Region',
        start_criterion=DaysSinceNumReached(50, 'Confirmed'),
        ycol='Confirmed',
        level='country',
        xcol='Date',
        top_k_groups=10,
        quarantine_df='./data/quarantine-activity.csv'  # should have a column with same name as `groupcol`
    )

    chart = chart.set_ytitle('Num Confirmed Cases (log)')
    chart = chart.set_xtitle('Days since 50 Confirmed')
    chart.set_width(600).set_height(400)
    chart.set_ydomain((100, 200000))
    chart.set_xdomain((0, 40))
    return chart


def make_jhu_state_chart() -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    # grab us-specific
    jhu_df = jhu_df[(jhu_df['Country_Region'] == 'United States') & (jhu_df['Province_State'].notnull())]

    chart = CovidChart(
        jhu_df,
        groupcol='Province_State',
        start_criterion=DaysSinceNumReached(20, 'Confirmed'),
        ycol='Confirmed',
        level='USA',
        xcol='Date',
        top_k_groups=10,
        quarantine_df='./data/quarantine-activity-US.csv'  # should have a column with same name as `groupcol`
    )
    chart.set_colormap()
    chart.set_axes_title_fontsize(16)
    chart.set_unfocused_opacity(0.05)
    chart.set_width(600).set_height(400)
    chart = chart.set_ytitle('Num Confirmed Cases (log)')
    chart = chart.set_xtitle('Days since 20 Confirmed')
    chart.set_xdomain((0, 30)).set_ydomain((20, 100000))
    return chart


def export_charts():
    jhu_country = make_jhu_country_chart()
    jhu_country.export('./website/scripts/jhu_country.js', 'jhu_country')
    jhu_state = make_jhu_state_chart()
    jhu_state.export('./website/scripts/jhu_state.js', 'jhu_state')


def make_vega_embed_script():
    script = """
(function(vegaEmbed) {
  var embedOpt = {"mode": "vega-lite"};
  vegaEmbed("#country_vis", jhu_country, embedOpt)
  vegaEmbed("#state_vis", jhu_state, embedOpt)
})(vegaEmbed);
    """
    with open('./website/scripts/vega_embed.js', 'w') as f:
        f.write(script)


def make_jekyll_config(chart_scripts):
    with open('./website/_config.in.yml', 'r') as f:
        config = yaml.load(f.read(), yaml.SafeLoader)
    for script in chart_scripts:
        config['head_scripts'].append(f'scripts/{script}')
    config['footer_scripts'] = ['scripts/vega_embed.js']
    with open('./website/_config.yml', 'w') as f:
        yaml.dump(config, f)


def main():
    export_charts()
    make_vega_embed_script()
    make_jekyll_config(['jhu_country.js', 'jhu_state.js'])


if __name__ == '__main__':
    sys.exit(main())
