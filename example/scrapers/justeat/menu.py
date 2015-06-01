from cyborg import Page, Scraper


class MenuScraper(Scraper):
    def scrape(self, data, response):
        takeaway_address = self.trim_whitespace(response.get(".restInfoAddress").text)
        takeaway_name = response.get(".restaurant-name").text

        menu = []

        for header in response.find("a.category-header-link"):
            if "chicken" not in header.text.lower():
                continue

            section = header.parent.parent

            for list_item in section.find("ul.menu-category-products > li"):
                if list_item.has_class("productSynonymListContainer"):
                    name = list_item.get("h4.itemName").text

                    menu_sublist = []

                    for sub_product in list_item.find(".addItemButton"):
                        sub_product_name = sub_product.get("h5.synonymName").text
                        price = sub_product.get("div.item-price").text.replace("\u00a3", "").replace("from", "")
                        menu_sublist.append(
                            (self.trim_whitespace(sub_product_name), self.trim_whitespace(price))
                        )

                    menu.append((name.strip(), menu_sublist))

                elif list_item.has_class("addItemButton"):
                    name = list_item.get("h4").text
                    price = list_item.get("div.item-price").text.replace("\u00a3", "").replace("from", "")
                    menu.append((name.strip(), price.strip()))
                else:
                    self.unknown_markup(list_item)

            yield {"id": data["id"], "name": takeaway_name,
                   "address": takeaway_address, "menu": menu}, None
            break
