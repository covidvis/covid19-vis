#!/usr/bin/env python
import sys
sys.path.append('.')
from datetime import datetime

import pandas as pd
import yaml

from chartlib import CovidChart, DaysSinceNumReached


def chart_configs():
    mobile_override_props = {
        'width': 200,
        'ytitle': '',
    }
    return [
        {
            'name': 'jhu_world_cases',
            'gen': make_jhu_country_cases_chart,
        },
        {
            'name': 'jhu_world_deaths',
            'gen': make_jhu_country_deaths_chart,
        },
        {
            'name': 'jhu_us_cases',
            'gen': make_jhu_state_cases_chart,
        },
        {
            'name': 'jhu_us_deaths',
            'gen': make_jhu_state_deaths_chart,
        },

        # mobile-friendly versions below
        {
            'name': 'jhu_world_cases_mobile',
            'gen': make_jhu_country_cases_chart,
            'override_props': mobile_override_props,
        },
        {
            'name': 'jhu_world_deaths_mobile',
            'gen': make_jhu_country_deaths_chart,
            'override_props': mobile_override_props,
        },
        {
            'name': 'jhu_us_cases_mobile',
            'gen': make_jhu_state_cases_chart,
            'override_props': mobile_override_props,
        },
        {
            'name': 'jhu_us_deaths_mobile',
            'gen': make_jhu_state_deaths_chart,
            'override_props': mobile_override_props,
        },
    ]


def make_jhu_country_cases_chart(override_props) -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    jhu_df = jhu_df[(jhu_df.Province_State.isnull()) & (jhu_df.Country_Region != 'China')]

    days_since = 50
    chart = CovidChart(
        jhu_df,
        groupcol='Country_Region',
        start_criterion=DaysSinceNumReached(days_since, 'Confirmed'),
        ycol='Confirmed',
        chart_type='country',
        xcol='Date',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity.csv'  # should have a column with same name as `groupcol`
    )

    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log scale)')
    chart = chart.set_xtitle('Days since {} Confirmed'.format(days_since))
    chart.set_width(600).set_height(400)
    chart.set_ydomain((days_since, 200000))
    chart.set_xdomain((0, 40))
    chart.spec.update(override_props)
    return chart


def make_jhu_country_deaths_chart(override_props) -> CovidChart:
    jhu_df = pd.read_csv("./data/jhu-data.csv")
    jhu_df = jhu_df.loc[(jhu_df.Country_Region != 'China') & jhu_df.Province_State.isnull()]

    chart = CovidChart(
        jhu_df,
        groupcol='Country_Region',
        start_criterion=DaysSinceNumReached(10, 'Deaths'),
        ycol='Deaths',
        xcol='Date',
        chart_type='country',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity.csv'  # should have a column with same name as `groupcol`
    )

    chart = chart.set_ytitle('Number of Deaths (log scale)')
    chart = chart.set_xtitle('Days since 10 Deaths')
    chart.set_width(600).set_height(400)
    chart.set_ydomain((10, 10000))
    chart.set_xdomain((0, 35)).compile()
    chart.spec.update(override_props)
    return chart


def make_jhu_state_cases_chart(override_props) -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    # grab us-specific
    jhu_df = jhu_df[(jhu_df.Country_Region == 'United States') & jhu_df.Province_State.notnull()]

    days_since = 20
    chart = CovidChart(
        jhu_df,
        groupcol='Province_State',
        start_criterion=DaysSinceNumReached(days_since, 'Confirmed'),
        ycol='Confirmed',
        chart_type='USA',
        xcol='Date',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity-US.csv'  # should have a column with same name as `groupcol`
    )
    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log scale)')
    chart = chart.set_xtitle('Days since {} Confirmed'.format(days_since))
    chart.set_width(600).set_height(400)
    chart.set_xdomain((0, 30)).set_ydomain((days_since, 100000))
    chart.spec.update(override_props)
    return chart


def make_jhu_state_deaths_chart(override_props) -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    jhu_df = jhu_df.loc[(jhu_df.Country_Region == 'United States') & jhu_df.Province_State.notnull()]

    chart = CovidChart(
        jhu_df,
        groupcol='Province_State',
        start_criterion=DaysSinceNumReached(10, 'Deaths'),
        ycol='Deaths',
        xcol='Date',
        chart_type='usa',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity-US.csv' # should have a column with same name as `groupcol`
    )

    chart = chart.set_ytitle('Number of Deaths (log scale)')
    chart = chart.set_xtitle('Days since 10 Deaths')
    chart.set_width(600).set_height(400)
    chart.set_ydomain((10, 10000))
    chart.set_xdomain((0, 25)).compile()
    chart.spec.update(override_props)
    return chart


def make_jhu_selected_state_chart(override_props) -> CovidChart:
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
        chart_type='USA',
        xcol='Date',
        top_k_groups=20,
        quarantine_df='./data/quarantine-activity-US.csv'  # should have a column with same name as `groupcol`
    )
    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log scale)')
    chart = chart.set_xtitle('Days since {} Confirmed'.format(days_since))
    chart.set_width(250).set_height(400)
    chart.set_xdomain((0, 35)).set_ydomain((days_since, 100000))
    chart.set_title("States With Significant Rate Decreases")
    chart.spec.update(override_props)
    return chart


def export_charts(configs):
    for config in configs:
        name = config['name']
        chart = config['gen'](config.get('override_props', {}))
        chart.export(f'./website/js/autogen/{name}.js', f'{name}')


def make_vega_embed_script(configs):
    script = """
function startVegaEmbedding() {{
  var embedOpt = {{"mode": "vega-lite"}};
  $(document).ready(function() {{
{embed_calls}
  }});
}};
    """
    embed_calls = []
    for config in configs:
        embed_calls.append(
            f'    vegaEmbed("#{config.get("embed_id", config["name"])}", {config["name"]}, embedOpt);'
        )
    embed_calls = '\n'.join(embed_calls)
    script = script.format(embed_calls=embed_calls)
    with open('./website/js/autogen/vega_embed.js', 'w') as f:
        f.write(script)


def make_jekyll_config(configs):
    with open('./website/_config.in.yml', 'r') as f:
        jekyll_config = yaml.load(f.read(), yaml.SafeLoader)
    jekyll_config['date_last_modified'] = datetime.now().strftime('%B %d, %Y')
    for config in configs:
        jekyll_config['footer_scripts'].append(f'js/autogen/{config["name"]}.js')
    with open('./website/_config.yml', 'w') as f:
        yaml.dump(jekyll_config, f)


def main():
    configs = chart_configs()
    export_charts(configs)
    make_vega_embed_script(configs)
    make_jekyll_config(configs)


if __name__ == '__main__':
    sys.exit(main())
