import os
import re
import requests
from pypdf import PdfReader
from typing import List, Dict
from ojd_daps_skills.pipeline.extract_skills.extract_skills import ExtractSkills

def download_pdf_from_url(url: str, save_path: str) -> str:
    print(f"Attempting to download PDF from URL: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"PDF downloaded successfully from {url}")
        return save_path
    except requests.exceptions.RequestException as e:
        print(f"Failed to download PDF from URL: {e}")
        return None

def extract_text_from_pdf(pdf_file_path: str) -> str:
    print(f"Extracting text from PDF: {pdf_file_path}")
    reader = PdfReader(pdf_file_path)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text() or ''
        text += page_text
    return text

def split_by_semester(text: str) -> List[str]:
    # WILL START SPLITTING BY SEMESTERS AND FINDING LESSONS AFTER IT READS 'COURSE OUTLINES'

    course_outline_start = re.search(r'Course Outlines', text)
    if not course_outline_start:
        print("No 'Course Outlines' section found.")
        return []

    print("Splitting text by semester")
    semesters = re.split(r'\d+st Semester|\d+nd Semester|\d+rd Semester|\d+th Semester', text)
    cleaned_semesters = [semester.strip() for semester in semesters if semester.strip()]
    print(f"Found semesters: {cleaned_semesters}")
    return cleaned_semesters

def split_by_lessons(semester_text: str) -> Dict[str, str]:
    # LESSONS ARE IN ALL CAPS
    # ANYTHING ELSE INCLUDED BEFORE IT READS THE NEXT LESSON IS CLASSIFIED UNDER SKILLS
    print("Splitting semester text into lessons")

    course_outline_start = re.search(r'Course Outlines', semester_text)
    if course_outline_start:
        semester_text = semester_text[course_outline_start.end():]

    lessons = re.split(r'\n([A-Z ]{2,})\n', semester_text)
    
    lesson_dict = {}
    for i in range(1, len(lessons), 2):
        title = lessons[i].strip()
        description = lessons[i + 1].strip()
        lesson_dict[title] = description
        print(f"Lesson found: {title}")

    return lesson_dict

def extract_skills_for_lessons(lessons: Dict[str, str], skills_extractor: ExtractSkills) -> Dict[str, List[Dict]]:
    print("Extracting skills for each lesson")
    lesson_skills = {}
    for title, description in lessons.items():
        print(f"Extracting skills for lesson: {title}")
        job_ad_with_skills = skills_extractor.extract_skills([description])
        lesson_skills[title] = {
            "raw_entities": [(ent.text, ent.label_) for ent in job_ad_with_skills[0].ents],
            "skill_spans": job_ad_with_skills[0]._.skill_spans,
            "mapped_skills": job_ad_with_skills[0]._.mapped_skills
        }
    return lesson_skills

def main(pdf_url: str = None, pdf_file_path: str = None) -> Dict[str, Dict[str, Dict]]:
    if not pdf_url and not pdf_file_path:
        raise ValueError("A PDF URL or file path must be provided.")

    if pdf_url:
        save_path = "downloaded_pdf.pdf"
        pdf_file_path = download_pdf_from_url(pdf_url, save_path)
        if not pdf_file_path and not os.path.exists(pdf_file_path):
            pdf_file_path = pdf_file_path
            print(f"URL failed, attempting to use local path: {pdf_file_path}")
    else:
        if not os.path.exists(pdf_file_path):
            raise FileNotFoundError(f"The file {pdf_file_path} was not found.")

    text = extract_text_from_pdf(pdf_file_path)
    semesters = split_by_semester(text)

    es = ExtractSkills(config_name="extract_skills_toy", local=True)

    all_data = {}
    for i, semester in enumerate(semesters, 1):
        print(f"Processing Semester {i}")
        lessons = split_by_lessons(semester)
        lesson_skills = extract_skills_for_lessons(lessons, es)
        all_data[f'Semester {i}'] = lesson_skills

    return all_data

if __name__ == "__main__":
    pdf_url = 'add the url to find the pdf' 
    pdf_file_path = 'fallback.pdf' # else access it solely locally
    data = main(pdf_url=pdf_url, pdf_file_path=pdf_file_path)

    for semester, lessons in data.items():
        print(f'{semester}:')
        for lesson, skills in lessons.items():
            print(f'  {lesson}:')
            print(f'    Skill Spans: {skills["skill_spans"]}')

