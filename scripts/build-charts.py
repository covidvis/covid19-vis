#!/usr/bin/env python
import sys
sys.path.append('.')

import pandas as pd
import yaml

from chartlib import CovidChart, DaysSinceNumReached


def chart_configs():
    return [
        {
            'name': 'jhu_country',
            'embed_id': 'country_vis',
            'gen': make_jhu_country_chart,
        },
        {
            'name': 'jhu_country_death',
            'embed_id': 'country_death_vis',
            'gen': make_jhu_country_death_chart,
        },
        {
            'name': 'jhu_state',
            'embed_id': 'state_vis',
            'gen': make_jhu_state_chart,
        },
        {
            'name': 'jhu_state_death',
            'embed_id': 'state_death_vis',
            'gen': make_jhu_state_death_chart,
        },
    ]


def make_jhu_country_chart() -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    jhu_df = jhu_df[(jhu_df.Province_State.isnull()) & (jhu_df.Country_Region != 'China')]

    days_since = 50
    chart = CovidChart(
        jhu_df,
        groupcol='Country_Region',
        start_criterion=DaysSinceNumReached(days_since, 'Confirmed'),
        ycol='Confirmed',
        level='country',
        xcol='Date',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity.csv'  # should have a column with same name as `groupcol`
    )

    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log)')
    chart = chart.set_xtitle('Days since {} Confirmed'.format(days_since))
    chart.set_width(600).set_height(400)
    chart.set_ydomain((days_since, 200000))
    chart.set_xdomain((0, 40))
    return chart


def make_jhu_country_death_chart() -> CovidChart:
    jhu_df = pd.read_csv("./data/jhu-data.csv")
    jhu_df = jhu_df.loc[(jhu_df.Country_Region != 'China') & jhu_df.Province_State.isnull()]

    chart = CovidChart(
        jhu_df,
        groupcol='Country_Region',
        start_criterion=DaysSinceNumReached(10, 'Deaths'),
        ycol='Deaths',
        xcol='Date',
        level='country',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity.csv'  # should have a column with same name as `groupcol`
    )

    chart = chart.set_ytitle('Number of Deaths (log)')
    chart = chart.set_xtitle('Days since 10 Deaths')
    chart.set_width(600).set_height(400)
    chart.set_ydomain((10, 10000))
    chart.set_xdomain((0, 35)).compile()
    return chart


def make_jhu_state_death_chart() -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    jhu_df = jhu_df.loc[(jhu_df.Country_Region == 'United States') & jhu_df.Province_State.notnull()]

    chart = CovidChart(
        jhu_df,
        groupcol='Province_State',
        start_criterion=DaysSinceNumReached(10, 'Deaths'),
        ycol='Deaths',
        xcol='Date',
        level='usa',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity-us.csv' # should have a column with same name as `groupcol`
    )

    chart = chart.set_ytitle('Number of Deaths (log)')
    chart = chart.set_xtitle('Days since 10 Deaths')
    chart.set_width(600).set_height(400)
    chart.set_ydomain((10, 10000))
    chart.set_xdomain((0, 25)).compile()
    return chart


def make_jhu_state_chart() -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    # grab us-specific
    jhu_df = jhu_df[(jhu_df.Country_Region == 'United States') & jhu_df.Province_State.notnull()]

    days_since = 20
    chart = CovidChart(
        jhu_df,
        groupcol='Province_State',
        start_criterion=DaysSinceNumReached(days_since, 'Confirmed'),
        ycol='Confirmed',
        level='USA',
        xcol='Date',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity-US.csv'  # should have a column with same name as `groupcol`
    )
    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log)')
    chart = chart.set_xtitle('Days since {} Confirmed'.format(days_since))
    chart.set_width(600).set_height(400)
    chart.set_xdomain((0, 30)).set_ydomain((days_since, 100000))
    return chart


def make_jhu_selected_state_chart() -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    # grab us-specific
    jhu_df = jhu_df[(jhu_df.Country_Region == 'United States') & jhu_df.Province_State.notnull()]
    # jhu_df[(nyt_df["state"]=="Illinois")|(nyt_df["state"]=="New York")| (nyt_df["state"]=="New Jersey")| (nyt_df["state"]=="Washington")| (nyt_df["state"]=="Michigan")]
    days_since = 20
    chart = CovidChart(
        jhu_df,
        groupcol='Province_State',
        start_criterion=DaysSinceNumReached(days_since, 'Confirmed'),
        ycol='Confirmed',
        level='USA',
        xcol='Date',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity-US.csv'  # should have a column with same name as `groupcol`
    )
    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log)')
    chart = chart.set_xtitle('Days since {} Confirmed'.format(days_since))
    chart.set_width(250).set_height(400)
    chart.set_xdomain((0, 35)).set_ydomain((days_since, 100000))
    chart.set_title("States With Significant Rate Decreases")
    return chart


def export_charts(configs):
    for config in configs:
        name = config['name']
        chart = config['gen']()
        chart.export(f'./website/scripts/{name}.js', f'{name}')


def make_vega_embed_script(configs):
    script = """
(function(vegaEmbed) {{
  var embedOpt = {{"mode": "vega-lite"}};
{embed_calls}
}})(vegaEmbed);
    """
    embed_calls = []
    for config in configs:
        embed_calls.append(
            f'  vegaEmbed("#{config.get("embed_id", config["name"])}", {config["name"]}, embedOpt);'
        )
    embed_calls = '\n'.join(embed_calls)
    script = script.format(embed_calls=embed_calls)
    with open('./website/scripts/vega_embed.js', 'w') as f:
        f.write(script)


def make_jekyll_config(configs):
    with open('./website/_config.in.yml', 'r') as f:
        jekyll_config = yaml.load(f.read(), yaml.SafeLoader)
    for config in configs:
        jekyll_config['head_scripts'].append(f'scripts/{config["name"]}.js')
    with open('./website/_config.yml', 'w') as f:
        yaml.dump(jekyll_config, f)


def main():
    configs = chart_configs()
    export_charts(configs)
    make_vega_embed_script(configs)
    make_jekyll_config(configs)


if __name__ == '__main__':
    sys.exit(main())
