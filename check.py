import re

with open(r'D:\Data\Sherlock-Holmes-Sanskrit\adventures-sherlock-holmes\speckled-band.html', 'r', encoding='utf-8') as f:
    text = f.read()

words = text.split()
res = set()
for w in words:
    # remove html tags
    w = re.sub(r'<[^>]+>', '', w)
    # remove punctuation
    clean_w = re.sub(r'[^\w\u0900-\u097F]', '', w)
    if clean_w.endswith('त्') and (clean_w.startswith('अ') or clean_w.startswith('आ')):
        res.add(clean_w)

print("Found 'त्' ending:", res)

res_ktavatu = set()
for w in words:
    w = re.sub(r'<[^>]+>', '', w)
    clean_w = re.sub(r'[^\w\u0900-\u097F]', '', w)
    if clean_w.endswith('वान्') or clean_w.endswith('वती') or clean_w.endswith('वन्तः') or clean_w.endswith('वत्यः'):
        res_ktavatu.add(clean_w)

print("Found ktavatu:", res_ktavatu)

res_lit = set()
lit_words = ['उवाच', 'जगाम', 'चकार', 'बभूव', 'आह', 'ददर्श', 'तस्थौ', 'शुश्राव']
for w in words:
    w = re.sub(r'<[^>]+>', '', w)
    clean_w = re.sub(r'[^\w\u0900-\u097F]', '', w)
    if clean_w in lit_words:
        res_lit.add(clean_w)

print("Found lit:", res_lit)

res_sma = set()
for w in words:
    w = re.sub(r'<[^>]+>', '', w)
    clean_w = re.sub(r'[^\w\u0900-\u097F]', '', w)
    if clean_w == 'स्म':
        res_sma.add(clean_w)

print("Found sma:", res_sma)
