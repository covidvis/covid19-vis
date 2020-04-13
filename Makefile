.PHONY: all charts web serve deploy stage

all: web

.empty-targets/charts: scripts/build-charts.py Makefile
	./scripts/build-charts.py
	touch ./.empty-targets/charts

charts: .empty-targets/charts

.empty-targets/web: .empty-targets/charts Makefile
	./scripts/build-web.sh
	touch ./.empty-targets/web

web: .empty-targets/web

serve: charts
	./scripts/serve-web.sh

deploy: web
	./scripts/deploy-web.sh

stage: charts
	./scripts/transform-config.py ./website/_config.yml ./website/_config-staging.yml ./website/_config.yml
	./scripts/build-web.sh
	./scripts/deploy-web.sh ../covidvis-staging gh-pages
