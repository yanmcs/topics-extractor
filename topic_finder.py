from contextlib import ContextDecorator
import requests
import googlesearch
import people_also_ask
from bs4 import BeautifulSoup
from people_also_ask.exceptions import (
    GoogleSearchRequestFailedError,
    RelatedQuestionParserError,
    FeaturedSnippetParserError
)
from typing import List, Dict, Any, Optional, Generator
from operator import attrgetter
import time
import os


class CallingSemaphore(ContextDecorator):

    def __init__(self, nb_call_times_limit, expired_time):
        self.nb_call_times_limit = nb_call_times_limit
        self.expired_time = expired_time
        self.called_timestamps = list()

    def __enter__(self):
        while len(self.called_timestamps) > self.nb_call_times_limit:
            now = time.time()
            self.called_timestamps = list(filter(
                lambda x: now - x < self.expired_time,
                self.called_timestamps
            ))
            time.sleep(0.5)
        self.called_timestamps.append(time.time())

    def __exit__(self, *exc):
        pass

URL = "https://www.google.com.br/search"
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/84.0.4147.135 Safari/537.36"
}
SESSION = requests.Session()
NB_TIMES_RETRY = 3
NB_REQUESTS_LIMIT = os.environ.get(
    "RELATED_QUESTION_NBREQUESTS_LIMIT", 25
)
NB_REQUESTS_DURATION_LIMIT = os.environ.get(
    "RELATED_QUESTION_DURATION_LIMIT", 60  # seconds
)


# Extract information from a given url using the Content Extractor API
def get_json_from_url(url):
    url = "https://contentextractor.herokuapp.com/?url=" + url
    response = requests.get(url, timeout=10)
    print(response.text)
    json = response.json()
    return json


# Does a Google search and returns the top 10 results.
def google_search(query, results=10):
    urls = []
    user_agent = googlesearch.get_random_user_agent()
    result = googlesearch.search(query,
    tld='com.br', lang='pt-BR', safe='off', num=10, start=0, stop=results, pause=0,
    country='BR', extra_params=None, verify_ssl=False,
    user_agent=user_agent)
    for url in result:
        urls.append(url)
    yield urls

semaphore = CallingSemaphore(
    NB_REQUESTS_LIMIT, NB_REQUESTS_DURATION_LIMIT
)

def search(keyword: str) -> Optional[BeautifulSoup]:
    """return html parser of google search result"""
    params = {"q": keyword,
              "cr": "BR",
              "hl": "pt-BR",
              "btnG": "Pesquisa+Google"}
    try:
        with semaphore:
            time.sleep(0.5)  # be nice with google :)
            response = SESSION.get(URL, params=params, headers=HEADERS)
    except Exception:
        raise GoogleSearchRequestFailedError(URL, keyword)
    if response.status_code != 200:
        raise GoogleSearchRequestFailedError(URL, keyword)
    return BeautifulSoup(response.text, "html.parser")


def _get_related_questions(text: str) -> List[str]:
    """
    return a list of questions related to text.
    These questions are from search result of text

    :param str text: text to search
    """
    document = search(text)
    if not document:
        return []
    try:
        return extract_related_questions(document)
    except Exception:
        raise RelatedQuestionParserError(text)


def extract_related_questions(document: BeautifulSoup) -> List[str]:
    div_questions = document.find_all("div", class_="related-question-pair")
    get_text = attrgetter("text")
    if not div_questions:
        return []
    questions = list(map(get_text, div_questions))
    return questions


def generate_related_questions(text: str) -> Generator[str, None, None]:
    """
    generate the questions related to text,
    these quetions are found recursively

    :param str text: text to search
    """
    questions = set(_get_related_questions(text))
    searched_text = set(text)
    while questions:
        text = questions.pop()
        yield text
        searched_text.add(text)
        questions |= set(_get_related_questions(text))
        questions -= searched_text


def get_related_questions(text: str, max_nb_questions: Optional[int] = None):
    """
    return a number of questions related to text.
    These questions are found recursively.

    :param str text: text to search
    """
    if max_nb_questions is None:
        return _get_related_questions(text)
    nb_question_regenerated = 0
    questions = set()
    for question in generate_related_questions(text):
        if nb_question_regenerated > max_nb_questions:
            break
        questions.add(question)
        nb_question_regenerated += 1
    return list(questions)


# Returns the people also ask questions for the given keyword.
def also_ask_questions(query, number_of_questions=10):
    result = get_related_questions(query, number_of_questions)
    questions = []
    for question in result:
        questions.append(question.split("Pesquisar:")[0])
    return questions


# Returns the top 10 results from the Google search and the people also ask questions.
def get_top_10_results(query, results=10):
    urls = []
    result = googlesearch.search(query,
    tld='com.br', lang='pt-BR', safe='off', num=10, start=0, stop=results, pause=2,
    country='BR', extra_params=None, user_agent=None, verify_ssl=True)
    for url in result:
        url = url.split("#")[0]
        if url not in urls:
            urls.append(url)
    return urls

def get_headings(keyword):
    headings = []

    # get urls first
    print("Getting top 10 results from Google to keyword: " + keyword)
    urls = get_top_10_results(keyword)
    if len(urls) == 0:
        print("No results found for keyword: " + keyword)
        return None
    else:
        print("Got top 10 results from Google.")
        print('\n'.join(urls))
        print("\nNow let's get the headings from the urls.\n")
    for url in urls:
        print('Getting headings from: ' + url)
        try:
            info = get_json_from_url(url)
        except Exception as e:
            print(e)
            print("Error getting headings from: " + url)
            continue
        else:
            article_headings = info['article_headings']
            print("Headings: " + " , ".join(headings))
            for heading in article_headings:
                print(heading)
                # Remove unicode from headings
                heading = heading.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                # Remove extra spaces
                heading = ' '.join(heading.split())
                headings.append(heading.strip())

    # now get also ask
    also_ask = also_ask_questions(keyword)
    for question in also_ask:
        headings.append(question)
    
    return headings
