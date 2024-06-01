import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.async_api import async_playwright
import re
import os
from urllib.parse import urlparse
import markdown
from bs4 import BeautifulSoup

# Scraping function
async def scrape_page(page, start_url):
    """
    Scrape the content of a webpage and follow its links to scrape more pages.

    Parameters:
    page (playwright.async_api.Page): The Playwright page object to interact with the web page.
    start_url (str): The starting URL to scrape.

    Returns:
    None
    """
    visited = set()
    queue = [start_url]
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp')

    while queue:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        print(f"Scraping URL: {url}")

        try:
            await page.goto(url)
            content = await page.content()

            # Generate filename from URL
            parsed_url = urlparse(url)
            filename = os.path.join('markdown', parsed_url.path.lstrip('/').replace('/', '_').replace('.html', '') + '.md')

            # Create directory if not exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Write the URL and content to the markdown file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f'## URL: {url}\n\n')
                f.write(f'### Content:\n\n')
                f.write(f'{content}\n\n')

            # Find all links on the page
            links = await page.eval_on_selector_all('a', 'elements => elements.map(el => el.href)')

            for link in links:
                # Ensure we only visit links within the same domain and skip image links
                if re.match(r'https://www\.thalesdocs\.com/ctp/cm/latest/.*', link) and not link.endswith(image_extensions):
                    if link not in visited:
                        queue.append(link)

        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

async def scrape_all(urls):
    """
    Scrape multiple webpages concurrently.

    Parameters:
    urls (list): A list of URLs to scrape.

    Returns:
    None
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        tasks = []
        for url in urls:
            page = await browser.new_page()
            tasks.append(scrape_page(page, url))

        await asyncio.gather(*tasks)
        await browser.close()

# Markdown cleanup function
def clean_markdown_file(file_path, is_file=True):
    """
    Clean up a markdown file by removing unwanted elements and properly formatting the content.

    Parameters:
    file_path (str): The path to the markdown file to clean.
    is_file (bool): A flag indicating whether the input is a file path or a markdown string. Default is True.

    Returns:
    tuple: A tuple containing the file path, a list of updated lines, and an error message (if any).
    """
    updated_lines = []
    
    try:
        # Parse markdown string directly if passed
        if is_file:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = file_path

        # Convert the markdown content to HTML
        html_content = markdown.markdown(content)
        
        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style tags
        for script_or_style in soup(['script', 'style', 'noscript']):
            script_or_style.decompose()
        
        # Remove link redirections
        for a_tag in soup.find_all('a', href=True):
            if 'redirect' in a_tag['href']:
                a_tag.decompose()
        
        # Remove unwanted elements (e.g., iframes)
        for tag in soup(['iframe', 'object', 'embed']):
            tag.decompose()
        
        # Properly format text inside paragraph tags
        for p_tag in soup.find_all('p'):
            p_tag.string = p_tag.get_text()
        
        # Properly format lists
        for ul_tag in soup.find_all('ul'):
            for li_tag in ul_tag.find_all('li'):
                li_tag.string = li_tag.get_text()
        
        # Convert the cleaned HTML content back to markdown
        cleaned_content = soup.get_text()
        
        # Compare the original and cleaned content line by line
        original_lines = content.splitlines()
        cleaned_lines = cleaned_content.splitlines()
        for i, (original_line, cleaned_line) in enumerate(zip(original_lines, cleaned_lines)):
            if original_line != cleaned_line:
                updated_lines.append(f"Line {i + 1}: {cleaned_line}")
        
        # Write the cleaned content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        return file_path, updated_lines, None
    except Exception as e:
        return file_path, updated_lines, str(e)

def clean_markdown_directory(directory, max_workers=(os.cpu_count()-4)):

    """
    Clean all markdown files in a directory using multiple threads.

    Parameters:
    directory (str): The directory containing markdown files to clean.
    max_workers (int): The maximum number of threads to use. Default is 4.

    Returns:
    None
    """
    files_to_clean = [
        os.path.join(root, file)
        for root, _, files in os.walk(directory)
        for file in files if file.endswith('.md')
    ]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(clean_markdown_file, file): file for file in files_to_clean}

        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                file, updated_lines, error = future.result()
                if file.endswith('.json.md'):
                    print(f"Processing JSON: {file}")
                if error:
                    print(f"Error processing {file}: {error}")
                else:
                    print(f"Successfully processed {file}")
                    #if updated_lines:
                        #print("Updated lines:")
                        #for line in updated_lines:
                            #print(line)
            except Exception as e:
                print(f"Exception occurred while processing {file}: {e}")

async def main(urls):
    """
    The main function to scrape multiple URLs and clean up the resulting markdown files.

    Parameters:
    urls (list): A list of URLs to scrape.

    Returns:
    None
    """
    # Run the scraping first
    await scrape_all(urls)
    # Run the markdown cleanup
    await asyncio.to_thread(clean_markdown_directory, 'markdown', max_workers=(os.cpu_count()-2))

if __name__ == '__main__':
    urls = [
        'https://www.thalesdocs.com/ctp/cm/latest/',
        # Add more URLs as needed
    ]
    asyncio.run(main(urls))