.PHONY: all

all: charts web

charts:
	./scripts/build-charts.py

web:
	./scripts/build-web.sh

serve:
	./scripts/serve-web.sh

deploy:
	./scripts/deploy-web.sh

stage:
	./scripts/transform-config.py ./website/_config.yml ./website/_config-staging.yml ./website/_config.yml
	./scripts/build-web.sh
	./scripts/deploy-web.sh ../covidvis-staging gh-pages
