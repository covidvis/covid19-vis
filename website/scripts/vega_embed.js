
(function(vegaEmbed) {
  var embedOpt = {"mode": "vega-lite"};
  vegaEmbed("#country_vis", jhu_country, embedOpt);
  vegaEmbed("#country_death_vis", jhu_country_death, embedOpt);
  vegaEmbed("#state_vis", jhu_state, embedOpt);
  vegaEmbed("#state_death_vis", jhu_state_death, embedOpt);
})(vegaEmbed);
    