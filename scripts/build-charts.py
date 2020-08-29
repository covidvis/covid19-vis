#!/usr/bin/env python
import sys
sys.path.append('.')
from datetime import datetime

import pandas as pd
import yaml

from chartlib import CovidChart, DaysSinceNumReached, days_between


STAGING = True  # os.environ.get('STAGING', os.environ.get('STAGE', False))

EXTRA_DAYS_TO_INCLUDE = days_between('2020-04-28', datetime.now())


def first_alphabetic_group(df, groupcol):
    return sorted(df[groupcol].unique())[0]


def chart_configs():
    mobile_override_props = {
        'width': 200,
        'ytitle': '',
        'emoji_legend': False,
    }
    configs = [
        {
            'name': 'jhu_us_cases',
            'gen': make_jhu_state_cases_chart,
            'make_text_area': True,
        },
        {
            'name': 'jhu_us_deaths',
            'gen': make_jhu_state_deaths_chart,
            'make_text_area': True,
        },
        {
            'name': 'jhu_world_cases',
            'gen': make_jhu_country_cases_chart,
        },
        {
            'name': 'jhu_world_deaths',
            'gen': make_jhu_country_deaths_chart,
        },
    ]

    def _make_mobile_config(config):
        return {
            **config,
            'name': config['name'] + '_mobile',
            'override_props': mobile_override_props,
            'make_text_area': False,
        }
    # force evaluation of list to avoid infinite loop
    configs_with_mobile = []
    for config in configs:
        configs_with_mobile.append(config)
        configs_with_mobile.append(_make_mobile_config(config))
    return configs_with_mobile


def _maybe_add_staging_props(chart):
    if STAGING:
        chart.lockdown_icons = True
        chart.lockdown_rules = False
        chart.lockdown_tooltips = True
        chart.only_show_lockdown_tooltip_on_hover = True
        chart.emoji_legend = True
        chart.grid = False
        chart.use_manual_legend = True
        chart.event_select = True
        chart.ydomain = (1, chart.ydomain[1])
    return chart


def make_jhu_country_cases_chart(override_props) -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    jhu_df = jhu_df[(jhu_df.Province_State.isnull()) & (jhu_df.Country_Region != 'China')]

    #qcsv = './data/quarantine-activity-Apr19.csv'
    qcsv = './data/quarantine-activity-world-new-export.csv'
    
    days_since = 50
    groupcol = 'Country_Region'
    chart = CovidChart(
        jhu_df,
        groupcol=groupcol,
        start_criterion=DaysSinceNumReached(days_since, 'Confirmed'),
        ycol='Confirmed',
        level='country',
        xcol='Date',
        top_k_groups=30,
        sample_every=3,
        quarantine_df=qcsv
    )


    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log scale)')
    chart = chart.set_xtitle(['Days since {} Confirmed'.format(days_since), '(Events prior to Day 0 not shown)'])
    chart.set_width(600).set_height(400)
    chart.set_ydomain((days_since, 1000000))
    chart.set_xdomain((0, 72 + EXTRA_DAYS_TO_INCLUDE))
    chart.click_selection_init = first_alphabetic_group(chart._preprocess_df(), groupcol)
    chart = _maybe_add_staging_props(chart)
    chart.spec.update(override_props)
    return chart


def make_jhu_country_deaths_chart(override_props) -> CovidChart:
    jhu_df = pd.read_csv("./data/jhu-data.csv")
    jhu_df = jhu_df.loc[(jhu_df.Country_Region != 'China') & jhu_df.Province_State.isnull()]

    qcsv = './data/quarantine-activity-Apr19.csv'

    days_since = 10
    groupcol = 'Country_Region'
    chart = CovidChart(
        jhu_df,
        groupcol=groupcol,
        start_criterion=DaysSinceNumReached(days_since, 'Deaths'),
        ycol='Deaths',
        xcol='Date',
        level='country',
        top_k_groups=30,
        sample_every=3,
        quarantine_df=qcsv
    )

    chart = chart.set_ytitle('Number of Deaths (log scale)')
    chart = chart.set_xtitle(['Days since {} Deaths'.format(days_since),'(Events prior to Day 0 not shown)'])
    chart.set_width(600).set_height(400)
    chart.set_ydomain((days_since, 100000))
    chart.set_xdomain((0, 62 + EXTRA_DAYS_TO_INCLUDE))
    chart.click_selection_init = first_alphabetic_group(chart._preprocess_df(), groupcol)
    chart = _maybe_add_staging_props(chart)
    chart.spec.update(override_props)
    return chart


def make_jhu_state_cases_chart(override_props) -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    # grab us-specific
    jhu_df = jhu_df[(jhu_df.Country_Region == 'United States') & jhu_df.Province_State.notnull()]

    if STAGING:
        level = 'usa'
        #qcsv = './data/quarantine-activity-US-Apr16.csv'
        qcsv = './data/combined-activity-US-Jun9.csv'
    else:
        level = 'usa_old'
        qcsv = './data/quarantine-activity-US.csv'

    days_since = 20
    groupcol = 'Province_State'
    chart = CovidChart(
        jhu_df,
        groupcol=groupcol,
        start_criterion=DaysSinceNumReached(days_since, 'Confirmed'),
        ycol='Confirmed',
        level=level,
        xcol='Date',
        top_k_groups=30,
        sample_every=3,
        quarantine_df=qcsv  # should have a column with same name as `groupcol`
    )
    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log scale)')
    chart = chart.set_xtitle(['Days since {} Confirmed'.format(days_since), '(Events prior to Day 0 not shown)'])
    chart.set_width(600).set_height(400)
    chart.set_xdomain((0, 47 + EXTRA_DAYS_TO_INCLUDE)).set_ydomain((days_since, 1000000))
    chart.click_selection_init = first_alphabetic_group(chart._preprocess_df(), groupcol)
    chart = _maybe_add_staging_props(chart)
    chart.spec.update(override_props)
    return chart


def make_jhu_state_deaths_chart(override_props) -> CovidChart:
    jhu_df = pd.read_csv('./data/jhu-data.csv')
    jhu_df = jhu_df.loc[(jhu_df.Country_Region == 'United States') & jhu_df.Province_State.notnull()]

    if STAGING:
        level = 'usa'
        #qcsv = './data/quarantine-activity-US-Apr16.csv'
        qcsv = './data/combined-activity-US-Jun9.csv'
    else:
        level = 'usa_old'
        qcsv = './data/quarantine-activity-US.csv'

    days_since = 10
    groupcol = 'Province_State'
    chart = CovidChart(
        jhu_df,
        groupcol=groupcol,
        start_criterion=DaysSinceNumReached(days_since, 'Deaths'),
        ycol='Deaths',
        xcol='Date',
        level=level,
        top_k_groups=30,
        sample_every=3,
        quarantine_df=qcsv  # should have a column with same name as `groupcol`
    )

    chart = chart.set_ytitle('Number of Deaths (log scale)')
    chart = chart.set_xtitle(['Days since {} Deaths'.format(days_since), '(Events prior to Day 0 not shown)'])
    chart.set_width(600).set_height(400)
    chart.set_ydomain((days_since, 100000))
    chart.set_xdomain((0, 47 + EXTRA_DAYS_TO_INCLUDE))
    chart.click_selection_init = first_alphabetic_group(chart._preprocess_df(), groupcol)
    chart = _maybe_add_staging_props(chart)
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
        level='USA',
        xcol='Date',
        top_k_groups=20,
        quarantine_df = './data/combined-activity-US-Jun9.csv'
        #quarantine_df='./data/quarantine-activity-US.csv'  # should have a column with same name as `groupcol`
    )
    # chart.set_colormap()
    chart.set_unfocused_opacity(0.05)
    chart = chart.set_ytitle('Number of Confirmed Cases (log scale)')
    chart = chart.set_xtitle(['Days since {} Confirmed'.format(days_since), '(Events prior to Day 0 not shown)'])
    chart.set_width(250).set_height(400)
    chart.set_xdomain((0, 35)).set_ydomain((days_since, 100000))
    chart.set_title("States With Significant Rate Decreases")
    chart = _maybe_add_staging_props(chart)
    chart.spec.update(override_props)
    return chart


def export_charts(configs):
    for config in configs:
        name = config['name']
        chart = config['gen'](config.get('override_props', {}))
        chart.export(f'./website/js/autogen/{name}.js', f'{name}')


def make_vega_embed_script(configs):
    load_script_function = """
function loadScript(scriptUrl) {
  const script = document.createElement('script');
  script.src = scriptUrl;
  document.body.appendChild(script);
  
  return new Promise((res, rej) => {
    script.onload = function() {
      res();
    }
    script.onerror = function () {
      rej();
    }
  });
}
    """
    script = """
var COVIDVIS_CHARTS = {{}};
{load_script_function}
function startVegaEmbedding() {{
  var embedOpt = {{"mode": "vega-lite"}};
  $(document).ready(function() {{
{embed_calls}
  }});
}}
    """
    embed_calls = None
    for config in reversed(configs):
        then_add_listener = ''
        if STAGING and config.get('make_text_area', False):
            then_add_listener = f'''
    var handler = makePopulateInfoPageSpaceHandler('{config["name"]}');
    chart.view.addSignalListener('click', handler);
    handler('click', chart.view.signal('click'));
'''
        then = f'''.then(function(chart) {{
    COVIDVIS_CHARTS['{config["name"]}'] = chart;
    {then_add_listener}
}})'''
        embed_call = f'vegaEmbed("#{config.get("embed_id", config["name"])}", {config["name"]}, embedOpt){then};'
        embed_call = f'loadScript("js/autogen/{config["name"]}.js").then(function() {{{ embed_call }}})'
        if embed_calls is None:
            embed_calls = embed_call
        else:
            embed_calls = f"""
{embed_call}.then(function() {{
    {embed_calls}
}})
        """.strip()
    script = script.format(load_script_function=load_script_function, embed_calls=embed_calls)
    with open('./website/js/autogen/vega_embed.js', 'w') as f:
        f.write(script)


def make_chart_detail():
    #.str.strip(to_strip='"')
    quarantine_df = pd.read_csv(qcsv = './data/combined-activity-US-Jun9.csv')
    quarantine_df["detail_html"] = '<li>'+quarantine_df["Effective Date"].str.replace("-","/")+": "+quarantine_df["Details (if any) "]+" [<a href='"+quarantine_df["Reference links"]+"'>source</a>]"+'</li>'

    quarantine_df["detail_html"] = quarantine_df["detail_html"].fillna("")

    result_html = quarantine_df[["State", "detail_html"]].groupby("State").aggregate(sum).reset_index()
    result_series = pd.Series(data=result_html["detail_html"])
    result_series.index = result_html['State']
    # f.to_json("./website/js/us_state_details.js",orient='columns')
    import json
    with open("./website/js/autogen/us_state_details.js",'w') as f:
        f.write("var stateDetails = ")
        json.dump(result_series.to_dict(),f)
        f.close()


def make_jekyll_config():
    with open('./website/_config.in.yml', 'r') as f:
        jekyll_config = yaml.load(f.read(), yaml.SafeLoader)
    jekyll_config['date_last_modified'] = datetime.now().strftime('%B %d, %Y')
    # for config in configs:
    #     jekyll_config['footer_scripts'].append(f'js/autogen/{config["name"]}.js')
    jekyll_config['staging'] = STAGING
    with open('./website/_config.yml', 'w') as f:
        yaml.dump(jekyll_config, f)


def main():
    configs = chart_configs()
    export_charts(configs)
    make_vega_embed_script(configs)
    make_jekyll_config()
    make_chart_detail()


if __name__ == '__main__':
    sys.exit(main())
