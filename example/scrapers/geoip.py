from cyborg import Page, BatchProcessor
import urllib.parse


class GeoIPScraper(BatchProcessor):
    BATCH_SIZE = 10

    def process_batch(self, batch):
        subquery_format = "SELECT latitude,longitude FROM geo.placefinder WHERE text='{0}' LIMIT 1"

        subqueries = (subquery_format.format(data[0]["address"].replace("'", "\\\\'")) for data in batch)
        query = "SELECT * FROM yql.query.multi WHERE queries=\"{0}\"".format(";".join(subqueries))

        return "http://query.yahooapis.com/v1/public/yql?q={0}&format=json".format(
            urllib.parse.quote_plus(query)
        )

    def process_response(self, batch, response):
        results = response["query"]["results"]["results"]
        if isinstance(results, dict):
            results = [results]

        for idx, result in enumerate(results):
            try:
                data = batch[idx][0]
                data["latlong"] = (result["Result"]["latitude"], result["Result"]["longitude"])

                yield data, None
            except Exception as e:
                pass

