import os
import re
import json
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_soup(url):
    """Fetches and parses HTML from a URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def detect_page_type(soup):
    """Determines if the page is a table-based list or a category list."""
    if soup.find("table", class_="wikitable"):
        return "table"
    return "category"

def scrape_wikipedia_category_links(url):
    """Extracts painting links from a Wikipedia category page."""
    soup = get_soup(url)
    if not soup:
        return []
    
    painting_links = []
    content = soup.find("div", id="mw-pages")
    if not content:
        return painting_links

    for a in content.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin("https://en.wikipedia.org", href)
        text = a.get_text(" ", strip=True)
        if not text or text.lower() in {"next page", "previous page"}:
            continue
        painting_links.append(full_url)

    return list(dict.fromkeys(painting_links)) # unique links preserving order

def scrape_wikipedia_painting_page(painting_url):
    """Scrapes details from an individual painting's Wikipedia page."""
    soup = get_soup(painting_url)
    if not soup:
        return None

    title = None
    year = None
    image_url = None

    heading = soup.find("h1", id="firstHeading")
    if heading:
        title = heading.get_text(" ", strip=True)

    infobox = soup.find("table", class_="infobox")
    if infobox:
        img = infobox.find("img")
        if img and img.get("src"):
            image_url = urljoin("https:", img["src"])

        rows = infobox.find_all("tr")
        for row in rows:
            header = row.find("th")
            data = row.find("td")
            if not header or not data:
                continue
            htxt = header.get_text(" ", strip=True).lower()
            dtxt = data.get_text(" ", strip=True)
            if "year" in htxt or "date" in htxt:
                year = dtxt
                break

    if not year:
        text = soup.get_text(" ", strip=True)
        match = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", text)
        if match:
            year = match.group(1)

    return {
        "title": title,
        "year": year,
        "image_url": image_url,
        "painting_url": painting_url
    }

def scrape_wikipedia_paintings_table(url):
    """Scrapes paintings from a Wikipedia page that uses a table format."""
    soup = get_soup(url)
    if not soup:
        return []

    paintings = []
    tables = soup.find_all('table', class_='wikitable')
    
    for table in tables:
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 2:
                continue
            
            first_col = cols[0]
            img_tag = first_col.find('img')
            image_url = None
            if img_tag:
                src = img_tag.get('src')
                image_url = urljoin("https:", src)
            
            title_tag = first_col.find('i')
            title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
            
            link_tag = first_col.find('a')
            painting_url = urljoin("https://en.wikipedia.org/", link_tag.get('href')) if link_tag and link_tag.get('href').startswith('/wiki/') else url
            
            year = cols[1].get_text(strip=True) if len(cols) > 1 else "Unknown"
            
            paintings.append({
                'title': title,
                'year': year,
                'image_url': image_url,
                'painting_url': painting_url
            })
            
    return paintings

def download_image(url, folder, filename):
    """Downloads an image from a URL and saves it to the specified folder."""
    if not url:
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        # Determine extension from URL or content-type
        ext = os.path.splitext(urlparse(url).path)[1]
        if not ext:
            content_type = response.headers.get('content-type')
            if content_type:
                ext = '.' + content_type.split('/')[-1].replace('jpeg', 'jpg')
        
        full_path = os.path.join(folder, filename + ext)
        
        # Ensure filename uniqueness
        counter = 1
        base_path = os.path.join(folder, filename)
        while os.path.exists(full_path):
            full_path = f"{base_path}_{counter}{ext}"
            counter += 1

        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return full_path
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def sanitize_filename(name):
    """Sanitizes a string to be used as a filename."""
    return re.sub(r'[^\w\-_\. ]', '_', name).strip()

def main():
    parser = argparse.ArgumentParser(description="Extract paintings from a Wikipedia page and save them to a folder.")
    parser.add_argument("url", help="Wikipedia URL of the artist's page or list of paintings.")
    parser.add_argument("--output", "-o", default="paintings", help="Folder to save the paintings. Defaults to 'paintings'.")
    parser.add_argument("--limit", "-l", type=int, help="Maximum number of paintings to scrape.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        print(f"Created directory: {args.output}")

    print(f"Detecting page type for: {args.url}")
    soup = get_soup(args.url)
    if not soup:
        return
    
    page_type = detect_page_type(soup)
    print(f"Page type detected: {page_type}")

    if page_type == "table":
        paintings = scrape_wikipedia_paintings_table(args.url)
    else:
        links = scrape_wikipedia_category_links(args.url)
        if args.limit:
            links = links[:args.limit]
        
        paintings = []
        for i, link in enumerate(links):
            print(f"Scraping ({i+1}/{len(links)}): {link}")
            p = scrape_wikipedia_painting_page(link)
            if p:
                paintings.append(p)

    if args.limit:
        paintings = paintings[:args.limit]

    print(f"Found {len(paintings)} paintings. Starting download...")

    for i, p in enumerate(paintings):
        title = p.get('title') or "Unknown"
        year = p.get('year') or "Unknown"
        clean_title = sanitize_filename(f"{title}_{year}")
        
        print(f"[{i+1}/{len(paintings)}] Downloading: {title} ({year})")
        if p.get('image_url'):
            local_path = download_image(p['image_url'], args.output, clean_title)
            p['local_path'] = local_path
        else:
            print(f"  No image URL for: {title}")

    # Save metadata
    metadata_path = os.path.join(args.output, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(paintings, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! Extracted {len(paintings)} paintings into '{args.output}'.")
    print(f"Metadata saved to {metadata_path}")

if __name__ == "__main__":
    main()
