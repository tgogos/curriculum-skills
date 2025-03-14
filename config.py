import os

CACHE_DIR = 'cache'
CACHE_FILE = 'pdf_cache.json'

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'SkillCrawl')
}
