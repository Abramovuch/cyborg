import asyncio
import logging

# Change this to logging.INFO to see more information. Setting it to logging.DEBUG is a bit too much.
logging.basicConfig(level=logging.WARN)

from example.scrapers.geoip import GeoIPScraper
import json

from cyborg import Pipeline
from example.scrapers.justeat.area import AreaScraper
from example.scrapers.justeat.takeaway import TakeawayScraper
from example.scrapers.justeat.menu import MenuScraper


just_eat_pipeline = Pipeline()\
    .set_host("http://just-eat.co.uk")\
    .feed(("chicken", "pizza", "kebab", "american", "italian"))\
    .pipe(AreaScraper)\
    .pipe(TakeawayScraper)\
    .unique("id")\
    .pipe(MenuScraper)


def main():
    with open("results", "w") as fd:
        # Create our pipeline, pipe all the data through the GeoIPScraper
        # Use the "display" plugin to give us a live overview of the status of the pipeline
        # Output all the results in JSON to our "results" file, opened above.
        pipe = just_eat_pipeline\
            .pipe(GeoIPScraper)\
            .use("display")\
            .output(lambda o: fd.write(json.dumps(o) + "\n"))

        # Run the pipeline
        task = pipe.start()
        asyncio.get_event_loop().run_until_complete(task)


if __name__ ==  "__main__":
    main()