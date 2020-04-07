# covid19-vis

Building the Charts
-------------------
```
pip install -r requirements.txt
./scripts/build-charts.py
```

Now the charts have been added to the website. (Try cd'ing into `website` and doing `git status` after making a change to the charts.)

Building the Website
--------------------

Make sure that you have Ruby version >= 2.4. Building the website requires ruby and bundler. To grab website dependencies, do the following from the `website` directory:

```
gem install bundler
bundle install
```

Now it should be possible to preview changes using jekyll (from `website` subdirectory):

`bundle exec jekyll serve`

To build without previewing execute the following (again, from `website` subdirectory):

`bundle exec jekyll build`

Or simply run the convenience script (from the root directory):

`./scripts/build-web.sh`

Deploying
---------

Deploying to github pages consists of copying the contents of `website/_site` into `covidvis.github.io`, commiting, and pushing. The convenience for this is as follows:

`./scripts/deploy-web.sh`


Makefile for End to End Building and Deploying
----------------------------------------------

To execute all build steps end-to-end, simply type `make`.

To deploy: `make deploy` (just a wrapper around `scripts/deploy-web.sh`)
