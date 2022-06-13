import requests
from googlesearch import search, get_random_user_agent
import people_also_ask

# Extract information from a given url using the Content Extractor API
def get_json_from_url(url):
    url = "https://contentextractor.herokuapp.com/?url=" + url
    return requests.get(url, timeout=10).json()


# Does a Google search and returns the top 10 results.
def google_search(query, results=10):
    urls = []
    user_agent = get_random_user_agent()
    result = search(query,
    tld='com.br', lang='pt-BR', safe='off', num=10, start=0, stop=results, pause=0,
    country='BR', extra_params=None, verify_ssl=False,
    user_agent=user_agent)
    for url in result:
        urls.append(url)
    yield urls


# Returns the people also ask questions for the given keyword.
def also_ask_questions(query, number_of_questions=5):
    result = people_also_ask.get_related_questions(query, number_of_questions)
    questions = []
    for question in result:
        questions.append(question.split("Pesquisar:")[0])
    return questions


# Returns the top 10 results from the Google search and the people also ask questions.
def get_top_10_results(query, results=10):
    urls = []
    result = search(query,
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
            json = get_json_from_url(url)
        except:
            print("Error getting headings from: " + url)
            continue
        else:
            article_headings = json['article_headings']
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

print(get_headings("chá verde para emagrecer"))