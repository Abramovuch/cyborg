from cyborg import Page, Scraper


class AreaScraper(Scraper):

    page_format = Page("/{input}-takeaways")

    def scrape(self, data, response):
        for link_list in response.find(".links"):
            for link in link_list.find("a"):
                yield {}, link.attr["href"]