import requests
import mysql.connector
from datetime import datetime
import xml.etree.ElementTree as ET
import time

# Function to insert data into the database
def insert_paper(title, author, abstract, publication_date, url, keywords):
    # Connect to your MySQL database
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Lluvia190202*',
        database='deep_learning_papers'
    )
    cursor = conn.cursor()

    # SQL query to insert data
    insert_query = """
    INSERT INTO papers (title, author, abstract, publication_date, url, keywords, score)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (title, author, abstract, publication_date, url, keywords, 0.0))

    # Commit the transaction
    conn.commit()
    cursor.close()
    conn.close()

# Function to make a single API call to arXiv and fetch multiple papers
def fetch_papers_from_arxiv(query, max_results):
    url = f'http://export.arxiv.org/api/query?search_query={query}&max_results={max_results}'
    resp = requests.get(url)

    ns = {'r': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(resp.text)

    entries = root.findall('r:entry', namespaces=ns)
    for entry in entries:
        # Extracting title, abstract, publication date, and URL
        title = entry.find('r:title', ns).text if entry.find('r:title', ns) is not None else 'N/A'
        abstract = entry.find('r:summary', ns).text if entry.find('r:summary', ns) is not None else 'N/A'
        publication_date = entry.find('r:published', ns).text if entry.find('r:published', ns) is not None else 'N/A'
        url = entry.find('r:id', ns).text if entry.find('r:id', ns) is not None else 'N/A'

        # Formatting publication date
        if publication_date != 'N/A':
            publication_date = datetime.strptime(publication_date, '%Y-%m-%dT%H:%M:%SZ').date()

        # Extracting authors
        authors = entry.findall('r:author/r:name', namespaces=ns)
        author_names = [author.text for author in authors]
        author = ', '.join(author_names)

        # Extracting keywords
        categories = entry.findall('r:category', namespaces=ns)
        keywords = ', '.join([category.get('{http://www.w3.org/2005/Atom}term') for category in categories if category.get('{http://www.w3.org/2005/Atom}term') is not None])

        insert_paper(title, author, abstract, publication_date, url, keywords)

    # Respect arXiv's rate limit
    time.sleep(3)

# Main execution
if __name__ == "__main__":
    query = 'all:deep learning'
    max_results = 5
    fetch_papers_from_arxiv(query, max_results)

