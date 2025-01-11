import requests

class AliExpressScraper:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_page(self, path):
        url = f"{self.base_url}{path}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            response.raise_for_status()