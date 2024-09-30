import streamlit as st
import requests
from bs4 import BeautifulSoup
import markdownify
from datetime import datetime

# Function to fetch webpage content
def fetch_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch {url}: {e}")
        return None

# Function to extract metadata like author and date
def extract_metadata(soup):
    # Extracting meta tags for date and author
    author = None
    publish_date = None

    # Try to find the author meta tag
    if soup.find("meta", {"name": "author"}):
        author = soup.find("meta", {"name": "author"})['content']
    elif soup.find("meta", {"property": "article:author"}):
        author = soup.find("meta", {"property": "article:author"})['content']
    elif soup.find("meta", {"name": "byl"}):
        author = soup.find("meta", {"name": "byl"})['content']

    # Try to find the publish date from meta tags or structured data
    if soup.find("meta", {"property": "article:published_time"}):
        publish_date = soup.find("meta", {"property": "article:published_time"})['content']
    elif soup.find("meta", {"name": "date"}):
        publish_date = soup.find("meta", {"name": "date"})['content']
    elif soup.find("meta", {"name": "DC.date.issued"}):
        publish_date = soup.find("meta", {"name": "DC.date.issued"})['content']
    elif soup.find("time", {"itemprop": "datePublished"}):
        publish_date = soup.find("time", {"itemprop": "datePublished"}).get_text(strip=True)

    # If no publish date is found, use current date as a fallback
    if not publish_date:
        publish_date = datetime.now().strftime('%Y-%m-%d')

    return author, publish_date

# Modified function to convert HTML to Markdown, keeping content in sequence except nav and footer
def convert_to_markdown(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove nav, footer, and testimonial sections
    for nav in soup.find_all('nav'):
        nav.decompose()
    for footer in soup.find_all('footer'):
        footer.decompose()
    for testimonial in soup.find_all(class_="testimonials"):  # assuming testimonials class
        testimonial.decompose()
    for comment in soup.find_all(class_="comments"):  # if there's a comments section
        comment.decompose()

    # Now we will extract the content from the body, preserving the sequence
    body_content = soup.body  # Assuming the content resides in the body tag
    if not body_content:
        return ""  # Return empty if no body tag found

    content = ""

    # Iterate through all elements in the body, preserving sequence
    for element in body_content.descendants:
        if element.name in ['h1', 'h2', 'h3', 'h4', 'p', 'div']:  # Include divs and other content containers
            if element.get('class') in (["testimonials"], ["comments"], ["nav"], ["footer"]):  # Skip unwanted classes
                continue
            content += str(element)

    # Convert the selected HTML content to Markdown
    if content:
        markdown_content = markdownify.markdownify(content, heading_style="ATX")
        return markdown_content.strip()

    return ""

# Function to generate file-friendly title based on the URL
def generate_file_title(soup, url, author, publish_date):
    # Try to extract the title or date from meta or <title> tag
    page_title = soup.find('title').get_text(strip=True) if soup.find('title') else 'Untitled Page'
    
    # Clean title for file usage
    page_title = page_title.replace(' ', '-').replace('|', '').replace('/', '-')
    
    # Generate markdown header format with title, date, and author
    metadata_header = f"Title: {page_title}\nPublished on: {publish_date}\nAuthor: {author if author else 'Unknown'}"
    
    return metadata_header

# Streamlit app setup
st.title("Markdown Converter")

# Input field for URLs
urls_input = st.text_area("Enter URLs (one per line):")

# Button to run the conversion
if st.button("Run"):
    urls = urls_input.splitlines()
    if not urls:
        st.warning("Please enter at least one URL.")
    else:
        # Output file name
        output_file = "output.txt"
        
        # Open file to write markdown data
        with open(output_file, 'w', encoding='utf-8') as file:
            for url in urls:
                if url.strip():  # Skip empty lines
                    st.write(f"Processing {url}...")
                    html_content = fetch_content(url.strip())
                    if html_content:
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Extract metadata
                        author, publish_date = extract_metadata(soup)
                        
                        # Convert content to Markdown
                        markdown_data = convert_to_markdown(html_content)
                        
                        # Generate title and metadata
                        metadata_header = generate_file_title(soup, url.strip(), author, publish_date)
                        
                        # Write the content in the desired format
                        file.write(f"{metadata_header}\n\n")
                        file.write(markdown_data)
                        file.write("\n\n---\n\n")  # Add a separator between different URLs
        st.success(f"Markdown data saved to {output_file}")

        # Option to download the file
        with open(output_file, "rb") as file:
            btn = st.download_button(label="Download output.txt", data=file, file_name="output.txt", mime="text/plain")
