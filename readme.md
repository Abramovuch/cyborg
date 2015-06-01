# Cyborg

Cyborg is an asyncio Python web scraping framework that helps you write programs to extract information from websites by reading and inspecting their HTML.

## What?

Scraping websites for data can be fairly complex when you are dealing with data across multiple pages, request limits and error handling. Cyborg aims to handle all of this for you transparently, so that you can focus on the actual extraction of data rather than all the stuff around it. It does this by helping you break the process down into smaller chunks, which can be combined into a *Pipeline*, for example below is a Pipeline that scrapes takeaway menus from Just-Eat:

    from cyborg import Pipeline
    from example.scrapers.justeat import *
    import json
    
    with open("output", "w") as fd:
      just_eat_pipeline = Pipeline()\
        .set_host("http://just-eat.co.uk")\
        .feed(("chicken", "pizza", "kebab", "american", "italian"))\
        .pipe(AreaScraper)\
        .pipe(TakeawayScraper)\
        .unique("id")\
        .pipe(MenuScraper)\
        .output(lambda o: fd.write(json.dumps(o) + "\n"))
      
      
This Pipeline has several stages:

  1. `feed(("chicken", "pizza", "kebab", "american", "italian"))`
      - This feeds five cuisines into the pipeline. `feed()` accepts other arguments like a file descriptor or a generator
  2. `pipe(AreaScraper)`
      - This is the first scraper to run. It takes a cuisine as input and produces a list of URL's to scrape next, like "https://www.just-eat.co.uk/italian-takeaways/hull"
  3. `pipe(TakeawayScraper)`
      - These URL's are piped into the TakeawayScraper, this produces a list of takeaways with an ID and a URL
  4. `unique("id")`
      - This section of the pipeline only outputs data that has a unique "id" key, so if a takeaway is scraped twice it is filtered out here
  5. `pipe(MenuScraper)`
      - These unique takeaways are piped into the MenuScraper which extracts data like the food offered with prices and the address
  6. `output(lambda o: fd.write(json.dumps(o) + "\n"))`
      - This function writes a JSON representation of the data to the output file
      
      
Running a pipeline is as simple as `asyncio.get_event_loop().run_until_complete(pipe.run())`. This then handles things like retrying failed requests, tracking exceptions/errors and parallel connections.

Currently any exceptions are logged and totalled for each process within a pipeline, however in the future the library will persist more data upon exceptions like the current pages HTML and offer the ability to reply these failed tasks during development.

## Writing a scraper
Writing a scraper is really simple. Here is the entire implementation for the `AreaScraper`:

    from cyborg import Page, Scraper

    class AreaScraper(Scraper):
      page_format = Page("/{input}-takeaways")

      def scrape(self, data, response):
          for link_list in response.find(".links"):
              for link in link_list.find("a"):
                  yield {}, link.attr["href"]
                  

Every scraper must have a `scrape(data, response)` function. This should then yield (data, url), the data is passed to the next scraper in the pipeline along with the URL response. This can be queried using CSS selectors.

## Running the example
You can run the example by just executing `python3 run.py` inside the example/ directory. Every second you will see output like this:

    AreaScraper         :      5: {}
    TakeawayScraper     :      6: {}
    _UniqueProcessor    :     26: {}
    MenuScraper         :     16: {}
    GeoIPScraper        :      7: {}
    
This is the status of the pipeline, the number is the number of tasks that have been processed. The dictionary to the right will display error totals, for examle `{"notfound":4, "exception":2}`.

## What works?
This is just an alpha at the moment, the example works but there is still a lot to be done:

   - Rate limiting
   - Configurable number of workers
   - Testing
   - Parallel pipelines:
      - `Pipeline.parallel(pipeline1, pipeline2).pipe(pipeline3)` - run two pipelines in parallel and pipe it to a third
   - Documentation
