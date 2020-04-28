---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: single
---

Visualizing the Impact of SARS-CoV-2 Intervention Strategies
-----

<div class="tabbed-ui overflow-center">
<div class="tab">
<span class="button-group">
  <button class="button-right tablinks default-open" onclick="openTabs(event, '.tab-content-usa');">USA</button>
  <button class="button-left tablinks" onclick="openTabs(event, '.tab-content-world')">World</button>
</span>
<span style="width: 5px; float: left;">&nbsp;</span>
<span class="button-group">
  <button class="button-left tablinks default-open" onclick="openTabs(event, '.tab-content-cases')">Cases</button>
  <button class="button-right tablinks" onclick="openTabs(event, '.tab-content-deaths')">Deaths</button>
</span>
</div>

<div class="tab-content tab-content-usa" id="usa-tab">
<div class="if-desktop">
    <div class="tab-content tab-content-cases" id="jhu_us_cases"></div>
    <div class="tab-content tab-content-deaths" id="jhu_us_deaths"></div>
</div>
<div class="if-mobile">
    <div class="tab-content tab-content-cases" id="jhu_us_cases_mobile"></div>
    <div class="tab-content tab-content-deaths" id="jhu_us_deaths_mobile"></div>
</div>
</div>

<div class="tab-content tab-content-world" id="world-tab">
<div class="if-desktop">
    <div class="tab-content tab-content-cases" id="jhu_world_cases"></div>
    <div class="tab-content tab-content-deaths" id="jhu_world_deaths"></div>
</div>
<div class="if-mobile">
    <div class="tab-content tab-content-cases" id="jhu_world_cases_mobile"></div>
    <div class="tab-content tab-content-deaths" id="jhu_world_deaths_mobile"></div>
</div>
</div>
</div>

<h2 id="about">About</h2>
The rapid spread of <a href="https://en.wikipedia.org/wiki/Coronavirus_disease_2019" target="_blank">SARS-CoV-2</a> has led many countries and regions to enact various <a href="https://en.wikipedia.org/wiki/National_responses_to_the_2019%E2%80%9320_coronavirus_pandemic" target="_blank">interventions</a>, 
such as social distancing, school closures, and border control, 
in order to mitigate the growth of infection. Understanding the effects
of these interventions is particularly important since each strategy comes with its side effects.
We wanted to understand the impact of intervention strategies and their combinations on the disease spread.
After collecting data at the country and state levels for certain types of interventions, we overlaid
them on the disease growth curves, shown above.
{% comment %}
For example, in addition to the economic impact to businesses, there are
<a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30460-8/fulltext">
negative mental health implications
</a> to self-isolation and quarantine.
{% endcomment %}

<h2 id="lockdown_section">Effects of Lockdowns</h2>
<p>
As a first step towards understanding the impact of interventions, the
visualization above shows the number of confirmed cases over time (on a
log scale), for the 30 US States with the most confirmed cases of SARS-CoV-2.
We have overlaid trends with various countermeasures 
taken by the governing entities. 
We use icons (💼, 🏠, 👨‍👩‍👧‍👦, 🎓, 🍔, 🏬) to depict 
these interventions; regional interventions are shown in smaller size than
interventions that are more complete (either at the state level for US States, 
or at the country level for countries).
For example, the icon 🏠 indicates a stay-at-home order or <a href="https://en.wikipedia.org/wiki/Curfews_and_lockdowns_related_to_the_2019%E2%80%9320_coronavirus_pandemic" target="_blank">lockdown</a>. 
We invite the reader to reveal
such measures on a per-region basis
in the chart by clicking the legend (recommended) or the chart itself.
(Select multiple regions by shift-clicking on the legend.)
You can switch between the visualizations for countries
or US states by switching between the
<i>World</i> or <i>USA</i> tabs,
and between the visualizations for
confirmed cases or deaths 
by switching between the <i>Cases</i>
or <i>Deaths</i> tabs.
</p>


<!--<p>
For countries, a <i>full lockdown</i> is 
one where there a nation-wide 
declaration of a <a href="https://en.wikipedia.org/wiki/Curfews_and_lockdowns_related_to_the_2019%E2%80%9320_coronavirus_pandemic" target="_blank">lockdown</a>.
On the other hand, a <i>partial lockdown</i> means that some but not all
regions within the country that have declared a lockdown, such as in the case of the United States. 
When visualizing US states, a <i>full lockdown</i> corresponds to a state-wide 
declaration of a stay at home-type order.
</p>
-->

<p>
To visualize the impact of the interventions,
we also plot a
projection line for the <b>original trajectory</b> 
of the trend prior to the last major intervention enacted. 
The projection extrapolates the
growth based on the slope in the last five days prior to the intervention. 
This projection is based on the simple
assumption that the growth rate stays fixed 
throughout the entire period of time, 
which is not always a valid
assumption for a number of reasons. 
For example, as the number of infected individuals increases, the
<a href="https://www.washingtonpost.com/graphics/2020/world/corona-simulator/" target="_blank">
growth will likely slow down</a>
due to the increasing number of 
recovered people with immunity. 
Nevertheless, this serves as one comparison point that
we can use to understand the effects of 
interventions in slowing the infection rates.
</p>




<h2 id="datasets">Datasets and Procedures</h2>

We draw on data regarding COVID-19 cases and deaths from [JHU Coronavirus Resource Center](https://coronavirus.jhu.edu/data) as well as the [New York Times US dataset](https://github.com/nytimes/covid-19-data).  

We manually constructed a dataset for interventions enacted in each US state, drawing from [Wikipedia](https://en.wikipedia.org/wiki/National_responses_to_the_2019%E2%80%9320_coronavirus_pandemic) as well as the [New York Times](https://github.com/nytimes/covid-19-data). The new dataset we collected  is available [here](https://github.com/covidvis/covid19-vis/blob/master/data/quarantine-activity-US-Apr16.csv) (last updated April 16th). This dataset captures information about:
<ul>
<li>Emergency Declarations</li>
<li>School, Restaurant, Non-Essential Business Closures</li>
<li>Banning of Gatherings</li>
<li>Visitor Quarantines and Border Closures</li>
<li>Stay-at-home Orders</li>
</ul>
After several rounds of manual coding procedures for these interventions, we eventually developed a form to force consistent and error-free coding. This form is available [here](https://github.com/covidvis/covid19-vis/blob/master/data/quarantine-activity-US-form.pdf). 

We have augmented this dataset to produce an enhanced dataset available [here](https://github.com/covidvis/covid19-vis/blob/master/data/quarantine-activity-US-Apr16-long.csv) that may be more useful for computational epidemiologists. In particular,
we list each specified intervention with a new line for each geographic entity (e.g., US city, county, township, school district, etc.). Where possible, each geographic entity was mapped to a unique [Federal Information Processing Standard (FIPS) code](https://en.wikipedia.org/wiki/FIPS_county_code), and then merged with available [population data from the US Census](https://www.census.gov/programs-surveys/popest/data/data-sets.html) to identify the total number of people living in the area where the specified intervention was enacted.

We are aware of complementary efforts to collect intervention data at the county level, such as those from
[Keystone](https://www.keystonestrategy.com/coronavirus-covid19-intervention-dataset-model/) and [Stanford](https://socialdistancing.stanford.edu/); however, these datasets do not cover all counties. 

For countries, we drew on Oxford's [Coronavirus Government Response Tracker](https://www.bsg.ox.ac.uk/research/research-projects/coronavirus-government-response-tracker) (last updated April 19th). We mapped their "Restrictions on movement" label to our "Stay at home" label; the "Workplace closing" label was mapped to "Business closures"; and their "Restrictions on gatherings" label was mapped to our "Gatherings banned" label. 







FAQs
----

- *What are the drawbacks of our visualization dashboards?*

There is danger in
extrapolating too much from limited historical data, especially since many of the case numbers are subject to
other confounding variables, such as the amount and availability of tests. 
We will be keeping the dashboard up-to-date with
the latest data to see how these trends unfold. 

Another drawback is that our extrapolation 
(labeled as original trajectory in the visualization) 
is easy-to-understand but simplistic: other more
sophisticated models exist. 
That said, our intent is not prediction, but rather provide a visual cue
to study the differences before and after the intervention.

Finally, we must mention that aggregate patterns and trends often obscure individual datapoints and outliers. Visualizing data on a logarithmic scale, while making it easier to visualize 
exponential growth, often gives us a false sense of linear behavior. 

- *How was the original trajectory computed?*

The trajectory was computed by drawing a straight line from the last five days prior to the point
of the intervention, and then extending that post the intervention. 

- *Why build yet another COVID-19 visualization?*

While there are many COVID-19 visualization dashboards, including those that employ helpful log-linear extrapolation to understand the trends in various regions, we haven't found any dashboards that try to visualize the overlaid visual impact of various intervention measures, apart from anecdotal reports of the [curve being flattened](https://www.nytimes.com/article/flatten-curve-coronavirus.html) thanks to interventions. If there are any visualization dashboards that we should be aware of and can link to, please share them with us at [covidvis@berkeley.edu](mailto:covidvis@berkeley.edu).

- *What's next for the project?*

The dashboards above simply scratch the surface of what can be and what needs to be done for this project. Apart from keeping our dashboards up-to-date on a regular basis, we're continuing to collect, study, and visualize the impact of fine-grained interventions (specifically, the impact of various combinations of interventions, such as school closures, banning of gatherings, non-essential business closures, and so on). Beyond Wikipedia, we are aware of other data-gathering efforts on this front, such as those from [Keystone](https://www.keystonestrategy.com/coronavirus-covid19-intervention-dataset-model/), [Stanford](https://socialdistancing.stanford.edu/) and [Oxford](https://www.bsg.ox.ac.uk/research/research-projects/coronavirus-government-response-tracker). We hope to leverage these datasets as well as others we manually collect to perform these analyses. 

- *How can we reproduce the charts above?*

Our Jupyter notebooks, processing scripts, and underlying datasets are online on [GitHub](https://github.com/covidvis/covid19-vis).

- *How can I contribute?* 

Please write to us at [covidvis@berkeley.edu](mailto:covidvis@berkeley.edu)

{% comment %}
Sources
-------
1. Data derived from John Hopkins CSSE [[link]](https://github.com/CSSEGISandData/COVID-19)
{% endcomment %}

Other Acknowledgments
----------------


There are many visualizations of COVID-19 growth curves online that we draw on for inspiration. We are fans of visualizations from [John Burn-Murdoch, Financial Times](https://www.ft.com/john-burn-murdoch), such as [this one](https://www.ft.com/coronavirus-latest), as well as the [New York Times](https://www.nytimes.com/news-event/coronavirus), such as [this](https://www.nytimes.com/interactive/2020/04/06/us/coronavirus-deaths-united-states.html), [this](https://www.nytimes.com/interactive/2020/world/coronavirus-maps.html), [this](https://www.nytimes.com/interactive/2020/04/03/upshot/coronavirus-metro-area-tracker.html), and [this](https://www.nytimes.com/interactive/2020/us/coronavirus-stay-at-home-order.html). We drew on data preprocessing scripts from [Wade Fagen](https://waf.cs.illinois.edu/)'s excellent ["Flip the script on COVID-19" dashboard](http://91-divoc.com/). 

Our visualization dashboard employs many popular open-source packages, including
[Altair](https://altair-viz.github.io/) and [Vega-Lite](https://vega.github.io/vega-lite/), for visualization,
[Pandas](https://pandas.pydata.org/) for data processing, and [Jupyter](https://jupyter.org/) for sharing code and visualizations. 

Team
----
Covidvis is a collaborative effort across computational epidemiology, public health, and visualization researchers at UC Berkeley ([EECS](https://eecs.berkeley.edu/),  [Innovate For Health Program](https://bids.berkeley.edu/research/innovate-health), [School of Information](https://www.ischool.berkeley.edu/), and [School of Public Health](https://publichealth.berkeley.edu/)), University of Illinois ([Computer Science](https://www.cs.illinois.edu/)), and Georgia Tech ([Computational Science and Engineering](https://cse.gatech.edu/)). 

From the visualization side, the team includes [Doris Jung-Lin Lee](http://dorisjunglinlee.com/) (UC Berkeley School of Information); [Stephen Macke](https://smacke.net/) (University of Illinois Computer Science and UC Berkeley EECS); [Ti-Chung Cheng](https://tichung.com/), [Tana Wattanawaroon](https://www.linkedin.com/in/tanawattanawaroon/), and Pingjing Yang (University of Illinois Computer Science); and [Aditya Parameswaran](https://people.eecs.berkeley.edu/~adityagp/) (UC Berkeley School of Information and EECS).

From the public health and epidemiology side, the team includes [B Aditya Prakash](http://www.cc.gatech.edu/~badityap) (Georgia Tech Computational Science and Engineering) as well as [Stephanie Eaneff](https://bids.berkeley.edu/people/stephanie-eaneff) (Data Science Health Innovation Fellow at UC Berkeley and UCSF). We've also benefited enormously from ideas and input from [Ziad Obermeyer](https://publichealth.berkeley.edu/people/ziad-obermeyer/) (UC Berkeley School of Public Health). 

