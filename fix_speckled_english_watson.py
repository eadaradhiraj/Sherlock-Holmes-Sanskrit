import os

file_path = r"D:\Data\Sherlock-Holmes-Sanskrit\adventures-sherlock-holmes\speckled-band.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "Watson -": "I -"
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
