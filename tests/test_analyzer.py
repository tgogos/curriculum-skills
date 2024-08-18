import re
import os
from pypdf import PdfReader
from typing import List, Dict
from ojd_daps_skills.pipeline.extract_skills.extract_skills import ExtractSkills

def extract_text_from_pdf(pdf_file_path: str) -> str:
    print(f"Extracting text from PDF: {pdf_file_path}")
    reader = PdfReader(pdf_file_path)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text() or ''
        text += page_text
        print(f"Page text: {page_text[:500]}...") 
    return text

def split_by_semester(text: str) -> List[str]:
    print("Splitting text by semester")
    semesters = re.split(r'\d+st Semester|\d+nd Semester|\d+rd Semester|\d+th Semester', text)
    cleaned_semesters = [semester.strip() for semester in semesters if semester.strip()]
    print(f"Found semesters: {cleaned_semesters}")
    return cleaned_semesters

def split_by_lessons(semester_text: str) -> Dict[str, str]:
    print("Splitting semester text into lessons")
    lessons = re.split(r'\n[A-Z ]+\s*-\s*[A-Z]+\n|\n[A-Z ]+\s*\n', semester_text)
    lesson_dict = {}
    for lesson in lessons:
        if lesson.strip():
            match = re.match(r'([A-Z ]+)\s*-\s*([A-Z]+)\s*(.*)', lesson.strip(), re.DOTALL)
            if match:
                title = match.group(1).strip()
                description = match.group(3).strip()
                lesson_dict[title] = description
                print(f"Lesson found: {title} - Description: {description[:100]}...")  
    return lesson_dict

def extract_skills_for_lessons(lessons: Dict[str, str], skills_extractor: ExtractSkills) -> Dict[str, List[Dict]]:
    print("Extracting skills for each lesson")
    lesson_skills = {}
    for title, description in lessons.items():
        print(f"Extracting skills for lesson: {title}")
        predicted_skills = skills_extractor.extract_skills([description])
        lesson_skills[title] = predicted_skills
        print(f"Skills for {title}: {predicted_skills}")
    return lesson_skills

def main(pdf_file_path: str) -> Dict[str, Dict[str, List[Dict]]]:
    if not pdf_file_path:
        raise ValueError("A PDF file path must be provided.")

    # Ensure the file exists
    if not os.path.exists(pdf_file_path):
        raise FileNotFoundError(f"The file {pdf_file_path} was not found.")

    text = extract_text_from_pdf(pdf_file_path)
    semesters = split_by_semester(text)

    es = ExtractSkills(config_name="extract_skills_toy", local=True)
    es.load()

    all_data = {}
    for i, semester in enumerate(semesters, 1):
        print(f"Processing Semester {i}")
        lessons = split_by_lessons(semester)
        lesson_skills = extract_skills_for_lessons(lessons, es)
        all_data[f'Semester {i}'] = lesson_skills

    return all_data

if __name__ == "__main__":
    pdf_file_path = '/home/ren/Downloads/nesta-crawler-main/9477-Program_of_Studies_2020-2021.pdf'
    data = main(pdf_file_path=pdf_file_path)

    for semester, lessons in data.items():
        print(f'{semester}:')
        for lesson, skills in lessons.items():
            print(f'  {lesson}: {skills}\n')

