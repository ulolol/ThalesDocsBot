import requests
import os
import html2text
from bs4 import BeautifulSoup
from googlesearch import search

def get_search_results(query):
    """
    Fetch search results for the given query.

    Parameters:
    query (str): The query string to search.

    Returns:
    list: A list of dictionaries containing title, link, and description of search results.
    """
    search_results = search(query, advanced=True)
    results = []
    for result in search_results:
        results.append({'title': result.title, 'link': result.url, 'description': result.description})
    return results

def extract_content(url):
    """
    Extract the content of a webpage from a given URL.

    Parameters:
    url (str): The URL of the webpage to extract content from.

    Returns:
    str: The raw HTML content of the webpage, or None if a request error occurs.
    """
    try:
        response = requests.get(url, timeout=10)  # Adding a timeout for better control
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        return str(soup)  # Return the raw HTML as a string
    except requests.exceptions.RequestException as e:
        print(f"Failed to extract content from {url}: {e}")
        return None

def convert_html_to_markdown(html_content):
    """
    Convert HTML content to Markdown format.

    Parameters:
    html_content (str): The HTML content to convert.

    Returns:
    str: The converted Markdown content.
    """
    h = html2text.HTML2Text()
    h.ignore_links = False  # Keep links in the converted text
    return h.handle(html_content)

def save_to_markdown(search_results, query):
    """
    Save search results to a Markdown file.

    Parameters:
    search_results (list): A list of dictionaries containing title, link, and description of search results.
    query (str): The search query string.

    Returns:
    list: A list of Markdown content entries.
    """
    if not os.path.exists('markdown'):
        os.makedirs('markdown')
    filename = f"markdown/{query.replace(' ', '_')}.md"
    markdown_contents = []

    with open(filename, 'w', encoding='utf-8') as f:
        for i, result in enumerate(search_results[:2]):
            title = result['title']
            description = result['description']
            link = result['link']
            html_content = extract_content(link)
            if html_content:
                markdown_content = convert_html_to_markdown(html_content)
                entry = f"## {i+1}. {title}\n*{description}*\n[Source]({link})\n\n```\n{markdown_content}\n```\n\n"
                f.write(entry)
                markdown_contents.append(entry)
    
    print(f"Content saved to {filename}")
    return markdown_contents

def fetch_and_save_articles(query):
    """
    Fetch search results for a given query, convert the content to Markdown format, and save it to a file.

    Parameters:
    query (str): The search query string.

    Returns:
    tuple: A tuple containing a message and a list of Markdown content entries.
    """
    search_results = get_search_results(f"site:thalesdocs.com {query}")
    if search_results:
        print(f"Search Results found: \n{search_results}")
        markdown_contents = save_to_markdown(search_results, query)
        print("Collected Markdown Content:\n")
        for content in markdown_contents:
            print(content)
        return markdown_contents
    else:
        return "No relevant web search results found.", []

