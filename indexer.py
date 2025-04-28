from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import re
import json
import time

BASE_URL = "https://quotes.toscrape.com"
INDEX_FILE = "index.json"
URLS_FILE = "urls.json"
POLITENESS_DELAY = 6


class Indexer: 
    def __init__(self):
        self.index = {}
        self.urls = {}
        self.url_to_index = {}
        self.visited_urls = set()
        self.current_page_id = 0

    def build_index(self, url=BASE_URL):
        if url in self.visited_urls:
            return
        print(f"Indexing page: {url}")
        self.visited_urls.add(url)

        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ")
        # Regex that removes punctuation but allows: 
        # Apostrophes (e.g. it's)
        # Hyphens (e.g. well-being)
        # Commas (e.g. for numbers like 10,000) but doesnt allow commas at the end of words 
        # Periods (e.g. for abbreviations and initials like J.M.)
        words = re.findall(r"\b\w+(?:[-',.\w]*\w+)?\b", text.lower())

        page_id = self.index_url(url)

        for position, word in enumerate(words):
            if word not in self.index:
                self.index[word] = {}
            if page_id not in self.index[word]:
                self.index[word][page_id] = []
            self.index[word][page_id].append(position)

        pages = self.get_pages(soup, url)

        # Recursively index every page found on the current page (eventually indexing all pages)
        for page in pages:
            # Before indexing next page, apply politeness delay
            time.sleep(POLITENESS_DELAY)
            self.build_index(page)

    def get_pages(self, soup, current_url):
        pages = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href")
            full_url = urljoin(current_url, href)

            if full_url.startswith(BASE_URL) and full_url not in self.visited_urls:
                pages.add(full_url)
        return pages


    def index_url(self, url):
        if url in self.url_to_index:
            return self.url_to_index[url]
        
        page_id = self.current_page_id
        self.url_to_index[url] = page_id
        self.urls[page_id] = url
        self.current_page_id += 1
        return page_id
    
    def save_index(self):
        with open(INDEX_FILE, "w") as index_file:
            json.dump(self.index, index_file)
        with open(URLS_FILE, "w") as urls_file:
            json.dump(self.urls, urls_file)


def main():
    indexer = Indexer()
    start_time = time.time()
    indexer.build_index()
    end_time = time.time()
    print(f"Indexing took {end_time - start_time:.2f} seconds")
    indexer.save_index()
    print("Indexing complete.")


if __name__ == "__main__":
    main()  