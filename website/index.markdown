---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: single
---

Visualizing the Impact of Intervention Strategies
-----
The rapid spread of <a href="https://en.wikipedia.org/wiki/Coronavirus_disease_2019">SARS-CoV-2</a> has led many countries and regions to enact various <a href="https://en.wikipedia.org/wiki/National_responses_to_the_2019%E2%80%9320_coronavirus_pandemic">interventions</a>, 
such as social distancing, school closures, and border control, 
in order to mitigate the growth of infection. Understanding the effects
of these interventions is particularly important since each strategy comes with its side effects.
We wanted to understand the impact of intervention strategies and their combinations on the disease spread.
After collecting data at the country and state levels for certain types of interventions, we overlaid
them on the disease growth curves, shown below.
{% comment %}
For example, in addition to the economic impact to businesses, there are
<a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30460-8/fulltext">
negative mental health implications
</a> to self-isolation and quarantine.
{% endcomment %}

<div class="tabbed-ui overflow-center">
<div class="tab">
<span class="button-group">
  <button class="button-left tablinks default-open" onclick="openTabs(event, '.tab-content-world')">World</button>
  <button class="button-right tablinks" onclick="openTabs(event, '.tab-content-usa')">USA</button>
</span>
<span style="width: 5px; float: left;">&nbsp;</span>
<span class="button-group">
  <button class="button-left tablinks default-open" onclick="openTabs(event, '.tab-content-cases')">Cases</button>
  <button class="button-right tablinks" onclick="openTabs(event, '.tab-content-deaths')">Deaths</button>
</span>
</div>

<div class="tab-content tab-content-world" id="world-tab">
{% comment %}
    <h2 class="centered">Country Trends</h2>
{% endcomment %}
    <div class="tab-content tab-content-cases" id="country_vis"></div>
    <div class="tab-content tab-content-deaths" id="country_death_vis"></div>
</div>

<div class="tab-content tab-content-usa" id="usa-tab">
{% comment %}
    <h2 class="centered">State Trends</h2>
{% endcomment %}
    <div class="tab-content tab-content-cases" id="state_vis"></div>
    <div class="tab-content tab-content-deaths" id="state_death_vis"></div>
</div>
</div>

<h2 id="lockdown_section">Effects of Lockdowns</h2>
<p>
As a first step towards understanding the impact of interventions, the
visualization above shows the logarithm of the number of confirmed cases 
over time, for the 20 countries with the most confirmed cases of SARS-CoV-2.
We have overlaid our trends with various countermeasures 
taken by the governing entities. 
We invite the reader to reveal
such measures on a per-region basis
in the chart by clicking the legend (recommended), 
the dropdown below the chart, or the chart itself.
You can switch between the visualizations for countries
or US states by switching between the
<i>World</i> or <i>USA</i> tabs,
and between the visualizations for
confirmed cases or deaths 
by switching between the <i>Cases</i>
or <i>Deaths</i> tabs.
</p>


<p>
For countries, a <i>full lockdown</i> is 
one where there a nation-wide 
declaration of a <a href="https://en.wikipedia.org/wiki/Curfews_and_lockdowns_related_to_the_2019%E2%80%9320_coronavirus_pandemic">lockdown</a>.
On the other hand, a <i>partial lockdown</i> means that some but not all
regions within the country that have declared a lockdown, such as in case of the United States. 
Likewise, when visualizing US states, 
a <i>full lockdown</i> is 
one where there is a state-wide 
declaration of a stay at home-type order.
</p>

<p>
To visualize the impact of these lockdowns,
we also plot a
projection line for the <b>original trajectory</b> 
of the trend before the lockdown date. 
The projection extrapolates the
growth based on the slope computed up until the lockdown date. 
This projection is based on the simple
assumption that the growth rate stays fixed 
throughout the entire period of time, 
which is not always a valid
assumption for a number of reasons. 
For example, as the number of infected individuals increases, the
<a href="https://www.washingtonpost.com/graphics/2020/world/corona-simulator/">
growth will likely slow down</a>
due to the increasing number of 
recovered people with immunity. 
Nevertheless, this serves as one comparison point that
we can use to understand the effects of 
interventions in slowing the infection rates.
</p>





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

The trajectory was computed by drawing a straight line from the start of the visualization to the point
of the intervention, and then extending that post the intervention. 

- *Why build yet another COVID-19 visualization?*

While there are many COVID-19 visualization dashboards, including those that employ helpful log-linear extrapolation to understand the trends in various regions, we haven't found any dashboards that try to visualize the overlaid visual impact of various intervention measures, apart from anecdotal reports of the [curve being flattened](https://www.nytimes.com/article/flatten-curve-coronavirus.html) thanks to interventions. If there are any visualization dashboards that we should be aware of and can link to, please share them with us at [covidvis@berkeley.edu](mailto:covidvis@berkeley.edu).

- *What's next for the project?*

The dashboards above simply scratch the surface of what can be and what needs to be done for this project. Apart from keeping our dashboards up-to-date on a regular basis, we're in the process of collecting, studying, and visualizing the impact of fine-grained interventions (specifically, the impact of various combinations of interventions, such as school closures, banning of gatherings, non-essential business closures, and so on). Beyond Wikipedia, we are aware of other data-gathering efforts on this front, such as those from [Keystone](https://www.keystonestrategy.com/coronavirus-covid19-intervention-dataset-model/) and [Stanford](https://socialdistancing.stanford.edu/). We hope to leverage these datasets as well as others we manually collect to perform these analyses. 

- *How can we reproduce the charts above?*

Our Jupyter notebooks and processing scripts are online on [GitHub](https://github.com/covidvis/covid19-vis). We also plan to make our intervention data available soon.

- *How can I contribute?* 

Please write to us at [covidvis@berkeley.edu](mailto:covidvis@berkeley.edu)

{% comment %}
Sources
-------
1. Data derived from John Hopkins CSSE [[link]](https://github.com/CSSEGISandData/COVID-19)
{% endcomment %}

Acknowledgments
----------------
We draw on data regarding COVID-19 cases and deaths from [JHU Coronavirus Resource Center](https://coronavirus.jhu.edu/data) as well as the [New York Times US dataset](https://github.com/nytimes/covid-19-data).  We draw on data regarding national and regional interventions from [Wikipedia](https://en.wikipedia.org/wiki/National_responses_to_the_2019%E2%80%9320_coronavirus_pandemic) as well as the [New York Times](https://github.com/nytimes/covid-19-data). 

There are many visualizations of COVID-19 growth curves online that we draw on for inspiration. We are fans of visualizations from [John Burn-Murdoch, Financial Times](https://www.ft.com/john-burn-murdoch), such as [this one](https://www.ft.com/coronavirus-latest), as well as the [New York Times](https://www.nytimes.com/news-event/coronavirus), such as [this](https://www.nytimes.com/interactive/2020/04/06/us/coronavirus-deaths-united-states.html), [this](https://www.nytimes.com/interactive/2020/world/coronavirus-maps.html), [this](https://www.nytimes.com/interactive/2020/04/03/upshot/coronavirus-metro-area-tracker.html), and [this](https://www.nytimes.com/interactive/2020/us/coronavirus-stay-at-home-order.html). We drew on data preprocessing scripts from [Wade Fagen](https://waf.cs.illinois.edu/)'s excellent ["Flip the script on COVID-19" dashboard](http://91-divoc.com/). 

Our visualization dashboard employs many popular open-source packages, including
[Altair](https://altair-viz.github.io/) and [Vega-Lite](https://vega.github.io/vega-lite/), for visualization,
[Pandas](https://pandas.pydata.org/) for data processing, and [Jupyter](https://jupyter.org/) for sharing code and visualizations. 

Team
----
Covidvis is a collaborative effort across computational epidemiology, public health, and visualization researchers at UC Berkeley ([EECS](https://eecs.berkeley.edu/), [School of Information](https://www.ischool.berkeley.edu/), and [School of Public Health](https://publichealth.berkeley.edu/)), University of Illinois ([Computer Science](https://www.cs.illinois.edu/)), and Georgia Tech ([Computational Science and Engineering](https://cse.gatech.edu/)). 

From the visualization side, the team includes [Doris Jung-Lin Lee](http://dorisjunglinlee.com/) (UC Berkeley School of Information); [Stephen Macke](https://smacke.net/) (University of Illinois Computer Science and UC Berkeley EECS); [Ti-Chung Cheng](https://tichung.com/), [Tana Wattanawaroon](https://www.linkedin.com/in/tanawattanawaroon/), and Pingjing Yang (University of Illinois Computer Science); and [Aditya Parameswaran](https://people.eecs.berkeley.edu/~adityagp/) (UC Berkeley School of Information and EECS).

From the public health and epidemiology side, the team includes [Ziad Obermeyer](https://publichealth.berkeley.edu/people/ziad-obermeyer/) (UC Berkeley School of Public Health) and [B Aditya Prakash](http://www.cc.gatech.edu/~badityap) (Georgia Tech Computational Science and Engineering).

