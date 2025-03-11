import re
import time
import logging
import random
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from fastapi import FastAPI
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

class CrawlRequest(BaseModel):
    url: str

@dataclass
class CourseInfo:
    semesters: dict  # {"Semester Name": {"Lesson Name": {"description": "", "skills": []}}}

class UniversityCrawler:
    def __init__(self, base_url, max_pages=500, depth_limit=6):
        self.base_url = base_url
        self.max_pages = max_pages
        self.depth_limit = depth_limit
        self.visited_urls = set()
        self.to_visit = [(base_url, 0)]
        self.semesters = {}
        self.pages_visited = 0
        self.university_name = "unknown_university"

    def _make_request(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed after {max_retries} attempts: {url}")
                    return None
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {url}")
                time.sleep(2)
        return None

    def crawl(self):
        while self.to_visit and self.pages_visited < self.max_pages:
            current_url, depth = self.to_visit.pop(0)
            if current_url in self.visited_urls:
                continue

            self.visited_urls.add(current_url)
            self.pages_visited += 1
            logger.info(f"Visiting: {current_url}")

            response = self._make_request(current_url)
            if not response:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            self._extract_university_name(soup)
            self._extract_courses(soup, current_url)
            if depth < self.depth_limit:
                self._extract_links(soup, current_url, depth)

            time.sleep(random.uniform(1, 3))  # Throttle requests

        logger.info(f"Crawl completed. Pages visited: {self.pages_visited}, Courses found: {sum(len(lessons) for lessons in self.semesters.values())}")
        self._save_results()
        return CourseInfo(semesters=self.semesters)

    def _extract_university_name(self, soup):
        title = soup.find("title")
        self.university_name = title.get_text().strip() if title else "Unknown University"

    def _extract_links(self, soup, current_url, depth):
        for a_tag in soup.find_all('a', href=True):
            link = a_tag.get('href', '').strip()
            if not link or link.startswith(('#', 'javascript:', 'mailto:')):
                continue
            absolute_url = urljoin(current_url, link)
            if urlparse(absolute_url).netloc == urlparse(self.base_url).netloc:
                if absolute_url not in self.visited_urls and absolute_url not in [url for url, _ in self.to_visit]:
                    self.to_visit.append((absolute_url, depth + 1))

    def _extract_courses(self, soup, current_url):
        semester_keywords = ["semester", "term", "fall", "spring", "winter", "summer"]
        course_keywords = ["course", "lesson", "subject", "module", "study"]

        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = " ".join(heading.get_text().split())  # Remove newlines within names
            if any(keyword.lower() in text.lower() for keyword in semester_keywords):
                semester_name = text
                if semester_name not in self.semesters:
                    self.semesters[semester_name] = {}
                
                next_element = heading.find_next_sibling()
                while next_element and next_element.name not in ['h1', 'h2', 'h3', 'h4']:
                    if next_element.name in ['ul', 'ol', 'table', 'div', 'p']:
                        self._extract_lessons(next_element, semester_name, current_url)
                    next_element = next_element.find_next_sibling()

    def _extract_lessons(self, element, semester_name, current_url):
        for li in element.find_all('li'):
            lesson_name = " ".join(li.get_text().split())  # Remove newlines within names
            link = li.find('a')
            description = "Description not found"

            if link and link.get('href'):
                lesson_url = urljoin(current_url, link.get('href'))
                if lesson_url not in self.visited_urls:
                    self.to_visit.append((lesson_url, 0))
                    description = self._fetch_description(lesson_url)
            else:
                description = self._extract_description(li)

            self.semesters[semester_name][lesson_name] = {
                "description": description,
                "skills": []  # Placeholder for skills extraction
            }

    def _fetch_description(self, url):
        response = self._make_request(url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 20:
                    return text
        return "Description not found"

    def _save_results(self):
        output_file = f"{self.university_name.replace(' ', '_').lower()}_courses.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.semesters, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved results to {output_file}")
