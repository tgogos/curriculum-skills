import re
import requests
from pypdf import PdfReader
import os
import sys
import yaml
import logging
from typing import List, Dict, Optional

sys.path.append('C:\\Users\\miafo\\AppData\\Local\\pypoetry\\Cache\\virtualenvs\\crawler-TjAGbN4O-py3.11\\Lib\\site-packages')
from ojd_daps_skills.pipeline.extract_skills.extract_skills import ExtractSkills


def download_pdf(url: str, local_path: str) -> None:
    response = requests.get(url)
    response.raise_for_status() 
    with open(local_path, 'wb') as file:
        file.write(response.content)


def extract_text_from_pdf(pdf_file_path: str) -> str:
    reader = PdfReader(pdf_file_path)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text


def split_by_semester(text: str) -> List[str]:
    semesters = re.split(r'\d+st Semester|\d+nd Semester|\d+rd Semester|\d+th Semester', text)
    return [semester.strip() for semester in semesters if semester.strip()]


def split_by_lessons(semester_text: str) -> Dict[str, str]:
    lessons = re.split(r'\n[A-Z ]+\s*-\s*[A-Z]+\n|\n[A-Z ]+\s*\n', semester_text)
    lesson_dict = {}
    for lesson in lessons:
        if lesson.strip():
            match = re.match(r'([A-Z ]+)\s*-\s*([A-Z]+)\s*(.*)', lesson.strip(), re.DOTALL)
            if match:
                title = match.group(1).strip()
                description = match.group(3).strip()
                lesson_dict[title] = description
    return lesson_dict


def extract_skills_for_lessons(lessons: Dict[str, str], skills_extractor: ExtractSkills) -> Dict[str, List[Dict]]:
    lesson_skills = {}
    for title, description in lessons.items():
        predicted_skills = skills_extractor.extract_skills([description])
        lesson_skills[title] = predicted_skills
    return lesson_skills


def main(pdf_url: Optional[str] = None, pdf_file_path: Optional[str] = None) -> Dict[str, Dict[str, List[Dict]]]:
    if pdf_url:
        local_pdf_path = 'downloaded_program.pdf'
        download_pdf(pdf_url, local_pdf_path)
        pdf_file_path = local_pdf_path

    if not pdf_file_path:
        raise ValueError("A PDF file path or URL must be provided.")

    text = extract_text_from_pdf(pdf_file_path)
    semesters = split_by_semester(text)

    es = ExtractSkills(config_name="extract_skills_toy", local=True)
    es.load()

    all_data = {}
    for i, semester in enumerate(semesters, 1):
        lessons = split_by_lessons(semester)
        lesson_skills = extract_skills_for_lessons(lessons, es)
        all_data[f'Semester {i}'] = lesson_skills

    return all_data


if __name__ == "__main__":
    pdf_url = 'https://www.uom.gr/assets/site/public/nodes/4254/9477-Program_of_Studies_2020-2021.pdf'
    data = main(pdf_url=pdf_url)

    for semester, lessons in data.items():
        print(f'{semester}:')
        for lesson, skills in lessons.items():
            print(f'  {lesson}: {skills}\n')

