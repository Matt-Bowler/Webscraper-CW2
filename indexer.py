from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import re
import json
import time
from collections import deque

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
        self.index_loaded = False

    def build_index(self, url=BASE_URL):
        queue = deque([url])

        while queue:
            current_url = queue.popleft()

            if current_url in self.visited_urls:
                continue

            self.visited_urls.add(current_url)
            print("Indexing: ", current_url)

            response = requests.get(current_url)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            words = []
            for word in text.lower().split():
                # Removes punctuation from the start and end of the word
                removed_punctuation = re.sub(r"^[^\w\d]+|[^\w\d]+$", "", word)
                # If result is not empty
                if removed_punctuation:
                    words.append(removed_punctuation)

            page_id = self.index_url(current_url)

            for position, word in enumerate(words):
                if word not in self.index:
                    self.index[word] = {}
                if page_id not in self.index[word]:
                    self.index[word][page_id] = []
                self.index[word][page_id].append(position)

            pages = self.get_pages(soup, current_url)
            for page in pages:
                if page not in self.visited_urls:
                    queue.append(page)
            
            time.sleep(POLITENESS_DELAY)

    def get_pages(self, soup, current_url):
        pages = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href")
            full_url = urljoin(current_url, href).rstrip("/")
            if full_url.startswith(BASE_URL):
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

    def load_index(self):
        try:
            with open(INDEX_FILE, "r") as index_file:
                self.index = json.load(index_file)
            with open(URLS_FILE, "r") as urls_file:
                self.urls = json.load(urls_file)
            self.index_loaded = True
        except FileNotFoundError:
            print("Index file not found run build to build the index first.")
    
    def get_link_by_id(self, page_id):
        if page_id not in self.urls:
            print("Page ID not found.")
            return
        return self.urls[page_id]

    def get_word_index(self, word):
        if word not in self.index:
            print("Word not found in index.")
            return
        return self.index[word]

    def get_if_index_loaded(self):
        return self.index_loaded 

    def find(self, query):
        words = query.split()
        page_ranks = {}

        for word in words:
            if word not in self.index:
                print(f"{word} not found in index, skipping")
                continue

            for page_id, positions in self.index[word].items():
                if page_id not in page_ranks:
                    page_ranks[page_id] = 0
                page_ranks[page_id] += len(positions)

        if len(words) > 1:
            page_ranks = self.multiword_query_ranking(words, page_ranks)
            
        return page_ranks

    def multiword_query_ranking(self, words, page_ranks):
        for page_id in list(page_ranks):
                word_positions = []
                for word in words:
                    if word in self.index and page_id in self.index[word]:
                        word_positions.append(self.index[word][page_id])
                
                match_count_bonus = len(word_positions) if len(word_positions) > 1 else 0
                page_ranks[page_id] += match_count_bonus * 5

                complete_phrase_bonus = 0
                if len(word_positions) == len(words):
                    for start_pos in word_positions[0]:
                        matched = 1
                        for i in range(1, len(word_positions)):
                            if (start_pos + i) in word_positions[i]:
                                matched += 1
                            else:
                                break
                        if matched == len(word_positions):
                            complete_phrase_bonus += 100
                page_ranks[page_id] += complete_phrase_bonus
        return page_ranks