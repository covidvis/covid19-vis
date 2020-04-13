.PHONY: all charts web serve deploy stage

all: web

charts:
	./scripts/build-charts.py

web: charts
	./scripts/build-web.sh

serve: charts
	./scripts/serve-web.sh

deploy: web
	./scripts/deploy-web.sh

stage: charts
	./scripts/transform-config.py ./website/_config.yml ./website/_config-staging.yml ./website/_config.yml
	./scripts/build-web.sh
	./scripts/deploy-web.sh ../covidvis-staging gh-pages
