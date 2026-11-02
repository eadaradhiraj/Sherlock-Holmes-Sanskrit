from bs4 import BeautifulSoup

with open(r'D:\Data\Sherlock-Holmes-Sanskrit\adventures-sherlock-holmes\speckled-band.html', 'r', encoding='utf-8') as f:
    text = f.read()

soup = BeautifulSoup(text, 'html.parser')
for span in soup.find_all('span', class_='segment'):
    s_text = span.get_text(strip=True)
    if s_text.startswith('"') or s_text.startswith("'") or s_text.startswith('“') or s_text.startswith('‘'):
        print(s_text)
