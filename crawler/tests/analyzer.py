import PyPDF2
import re
import pytest
from spacy.tokens import Doc
from wasabi import msg
from ojd_daps_skills import setup_spacy_extensions
from ojd_daps_skills.extract_skills.extract_skills import SkillsExtractor
import requests

def download_pdf(url, local_path):
    response = requests.get(url)
    with open(local_path, 'wb') as file:
        file.write(response.content)

def extract_text_from_pdf(pdf_file_path):
    with open(pdf_file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def split_by_semester(text):
    semesters = re.split(r'\d+st Semester|\d+nd Semester|\d+rd Semester|\d+th Semester', text)
    return [semester.strip() for semester in semesters if semester.strip()]

def split_by_lessons(semester_text):
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

def extract_skills_for_lessons(lessons, es):
    lesson_skills = {}
    for title, description in lessons.items():
        predicted_skills = es.get_skills([description])
        lesson_skills[title] = predicted_skills
    return lesson_skills

def main(pdf_url=None, pdf_file_path=None):
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








