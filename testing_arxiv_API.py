import requests
import xml.etree.ElementTree as ET

query = 'all:covid 19'
max_results = 10

url = f'http://export.arxiv.org/api/query?search_query={query}&max_results={max_results}'
resp = requests.get(url)

ns = {'r': 'http://www.w3.org/2005/Atom'}
root = ET.fromstring(resp.text)

all_papers = list()
entries = root.findall('r:entry', namespaces=ns)
for entry in entries:
    paper = {l.tag[l.tag.index('}')+1:]: l.text for l in entry if l.tag[l.tag.index('}')+1:] != 'author'}
    
    # Extracting authors
    authors = entry.findall('r:author/r:name', namespaces=ns)
    author_names = [author.text for author in authors]
    paper['author'] = ', '.join(author_names)

    # Extracting categories (which are essentially the 'keywords')
    categories = entry.findall('r:category', namespaces=ns)
    category_terms = [category.attrib['{http://www.w3.org/2005/Atom}term'] for category in categories]
    paper['keywords'] = ', '.join(category_terms)

    all_papers.append(paper)

# Print out the keys and keywords for the first paper
print(all_papers[0].keys())
print("Keywords for the first paper:", all_papers[0]['keywords'])
