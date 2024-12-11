FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir pdfplumber requests beautifulsoup4 urllib3 fuzzywuzzy pyfiglet esco-skill-extractor python-Levenshtein

CMD ["python", "skillcrawl.py"]
