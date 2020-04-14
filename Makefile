.PHONY: all charts web serve deploy stage

all: web

.empty-targets/charts: scripts/build-charts.py $(wildcard chartlib/*.py) Makefile
	./scripts/build-charts.py
	touch ./.empty-targets/charts

charts: .empty-targets/charts

web: .empty-targets/charts
	./scripts/build-web.sh

serve: charts
	./scripts/serve-web.sh

deploy: web
	./scripts/deploy-web.sh

stage: .empty-targets/charts
	./scripts/transform-config.py ./website/_config.yml ./website/_config-staging.yml ./website/_config.yml
	./scripts/build-web.sh
	./scripts/deploy-web.sh ../covidvis-staging gh-pages
