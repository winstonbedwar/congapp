import requests
from bs4 import BeautifulSoup
from html2md import convert

url = "https://www.example.com"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract the main content
main_content = soup.find('div', class_='main-content')
html_content = str(main_content)

# Convert to Markdown
markdown = convert(html_content)
print(markdown)
