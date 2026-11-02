import os

file_path = r"D:\Data\Sherlock-Holmes-Sanskrit\adventures-sherlock-holmes\speckled-band.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "स्टोनरुपाख्या": "स्टोनरोपाख्या",
    "स्टोनरुपाख्ये": "स्टोनरोपाख्ये",
    '"Did you come by the morning train?"': 'Holmes - "Did you come by the morning train?"'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
