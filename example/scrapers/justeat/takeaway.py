from cyborg import Page, Scraper


class TakeawayScraper(Scraper):
    def scrape(self, data, response):
        for place_div in response.find("div.restaurant"):
            if place_div.has_class("offlineRestaurant"):
                continue

            header_link = place_div.get("h2 a")
            header_id = int(header_link.attr["data-restaurant-id"])

            yield {"id": header_id}, header_link.attr["href"]

