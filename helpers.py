import os
import re
import json
import requests
from fuzzywuzzy import fuzz
from esco_skill_extractor import SkillExtractor

CACHE_DIR = 'cache'
CACHE_FILE = 'pdf_cache.json'

os.makedirs(CACHE_DIR, exist_ok=True)

skill_extractor = SkillExtractor()

def clean_lesson_name(name: str) -> str:
    return re.sub(r'\s*\(.*?\)\s*', '', name).strip()

def load_cache():
    cache_file_path = os.path.join(CACHE_DIR, CACHE_FILE)
    if os.path.exists(cache_file_path):
        with open(cache_file_path, 'r') as cache_file:
            return json.load(cache_file)
    return {}

def save_cache(data):
    cache_file_path = os.path.join(CACHE_DIR, CACHE_FILE)
    with open(cache_file_path, 'w') as cache_file:
        json.dump(data, cache_file, indent=4)

def is_cached(key):
    cache = load_cache()
    return key in cache

def contains_greek_characters(text: str) -> bool:
    return bool(re.search(r'[Α-ω]', text))

def contains_no_lowercase_letters(text: str) -> bool:
    return not any(char.islower() for char in text)

def extract_description(text: str) -> str:
    start_marker = 'General competences'
    end_marker = 'Assessment'
    start_index = text.find(start_marker)
    if start_index == -1:
        return ""
    end_index = text.find(end_marker, start_index)
    if end_index == -1:
        end_index = len(text)
    description = text[start_index + len(start_marker):end_index].strip()
    description = description.replace('Course content', '').strip()
    return description if description else "This lesson has no data!"
