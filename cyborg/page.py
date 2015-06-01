

class Page(object):
    def __init__(self, format_string: str, host=""):
        self.host = host
        self.format = format_string

    def get_url(self, data):
        if data.startswith("/") and self.host.endswith("/"):
            data = data[1:]

        return self.host + self.format.format(input=data)

    def set_host(self, host):
        self.host = host

    def copy(self):
        return Page(self.format, self.host)