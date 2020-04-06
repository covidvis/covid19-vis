.PHONY: all

all: charts web deploy

charts:
	./scripts/build-charts.py

web:
	./scripts/build-web.sh

deploy:
	./scripts/deploy-web.sh
