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
