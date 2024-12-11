import pdfplumber
import requests
import re
import sys
from esco_skill_extractor import SkillExtractor
from bs4 import BeautifulSoup
import time
from urllib.parse import quote_plus
from fuzzywuzzy import fuzz
import pyfiglet

skill_extractor = SkillExtractor()

# Format functions - Ignore
def print_colored_text(text: str, color_code: str) -> None:
    print(f"\033[{color_code}m{text}\033[0m")

def print_logo():
    logo = pyfiglet.figlet_format("SKILLCRAWL")
    print(logo)

def print_horizontal_line(length: int) -> None:
    print('=' * length)

def print_loading_line(length: int) -> None:
    print_colored_text('=' * length + '|] Loading...[|' + '=' * length, 33)

def print_horizontal_small_line(length: int) -> None:
    print('-' * length)

def print_green_line(length: int) -> None:
    print_colored_text('=' * length, 32)

def print_yellow_line(length: int) -> None:
    print_colored_text('=' * length, 33)

# Helper functions
def contains_greek_characters(text: str) -> bool:
    return bool(re.search(r'[Α-ω]', text))

def contains_no_lowercase_letters(text: str) -> bool:
    return not any(char.islower() for char in text)

# Main Functions
def download_pdf(url: str, save_path: str) -> str:
    print(f"Downloading PDF from {url}")
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)
    return save_path

def extract_text_from_pdf(pdf_file_path: str) -> list:
    print(f"Extracting text from PDF: {pdf_file_path}")
    print_loading_line(25)
    page_texts = []
    with pdfplumber.open(pdf_file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            page_texts.append(text)
    return page_texts

def extract_text_after_marker(text: list, marker: str) -> str:
    print_colored_text(f" >>> Extracting text after marker: {marker}", 34)
    full_text = '\n'.join(text)
    marker_index = full_text.lower().find(marker.lower())
    if marker_index == -1:
        print("Marker not found in the text.")
        return ""
    return full_text[marker_index + len(marker):]

def split_by_semester(text: str) -> list:
    print("Splitting text by semester")
    semesters = re.split(r'(?i)(\b\d+\s*(?:st|nd|rd|th)?\s*Semester\b)', text)
    combined_semesters = [''.join(semesters[i:i+2]) for i in range(1, len(semesters), 2)]
    print(f"Found semesters: {len(combined_semesters)}")
    return combined_semesters

def clean_lesson_name(name: str) -> str:
    return re.sub(r'\s*\(.*?\)\s*', '', name).strip()

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

def process_pages_by_lesson(pages: list) -> dict:
    print("Processing pages by lesson")
    lesson_dict = {}
    num_lines_to_check = 2
    for page in pages:
        lines = page.split('\n')
        if not lines:
            continue
        potential_lesson_name = ""
        for i in range(min(num_lines_to_check, len(lines))):
            line = lines[i].strip()
            if line.isupper() or any(keyword in line.lower() for keyword in ["lesson", "course"]):
                potential_lesson_name += line + " "
        if potential_lesson_name:
            lesson_name = clean_lesson_name(potential_lesson_name.strip())
            if contains_no_lowercase_letters(lesson_name) and not contains_greek_characters(lesson_name):
                lesson_text = '\n'.join(lines[num_lines_to_check:]).strip()
                lesson_description = extract_description(lesson_text)
                if lesson_description:
                    lesson_dict[lesson_name] = lesson_description
    return lesson_dict

def extract_and_get_title(skill_url):
    try:
        skill_id = skill_url.split('/skill/')[1]
        base_url = "https://esco.ec.europa.eu/en/classification/skill?uri=http%3A%2F%2Fdata.europa.eu%2Fesco%2Fskill%2F"
        combined_url = base_url + quote_plus(skill_id)
        response = requests.get(combined_url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else "No title found"
            if '| ESCO' in title:
                title = title.split(' | ESCO')[0].strip()
            return title
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return "Error: Failed to fetch page"
    except Exception as e:
        print(f"Error: {e}")
        return "Error: Exception occurred"


def display_menu():
    print_logo()
    print_yellow_line(50)
    print("Select an option:")
    print_yellow_line(50)
    print("1. Show Semesters, Lessons, and Descriptions (Use 'descr')")
    print("2. Show only Semesters and Lessons -Simplified version- (Use 'simplified')")
    print_colored_text("[RECOMMENDED] 3. Show Skills [URLs] (Use 'skills')", 32)
    print_colored_text(" |__ [RECOMMENDED] 3.1. Show Skills for a specific lesson [URLs] (Use 'skills' and lesson name, exp.'python crawler.py skills algorithms')", 32)
    print_colored_text("[SLOW] 4. Get Skill Names from URLs (Use 'skillname')", 33)
    print_colored_text(" |__ [SLOW, RECOMMENDED] 4.1. Get Skill Names from URLs (Use 'skillname', exp.'python crawler.py skillname algorithms')", 33)
    print("5. Exit")
    print_yellow_line(50)
    choice = input("Enter your choice: ").strip().lower()

    parts = choice.split(maxsplit=1)
    command = parts[0] if parts else "exit" 
    lesson_name = parts[1] if len(parts) > 1 else None 

    return command, lesson_name

def get_skills_for_lesson(all_data, lesson_name, skills=False, skillname=False, threshold=80):
    print_horizontal_line(50)
    for semester, lessons in all_data.items():
        matched_lessons = [(lesson, fuzz.partial_ratio(lesson_name.lower(), lesson.lower())) for lesson in lessons]
    
        matched_lessons = [lesson for lesson, score in matched_lessons if score >= threshold]
        
        if matched_lessons:
            print_colored_text(f'{semester}:', 33)
            print_horizontal_small_line(50)
            for lesson_name in matched_lessons:
                lesson_description = lessons[lesson_name]
                print(f'  {lesson_name}')
                print_horizontal_small_line(25)

                skills_list = skill_extractor.get_skills([lesson_description])

                filtered_skills = set()
                for skill_set in skills_list:
                    for skill_url in skill_set:
                        filtered_skills.add(skill_url)

                if skills:
                    if filtered_skills:
                        print_colored_text(f'    Skills:', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            print_colored_text(f'      Skill URL: {skill_url}', "32")
                        print_green_line(50)
                    else:
                        print_colored_text(f'    No skills found', "31")
                elif skillname:
                    if filtered_skills:
                        print_colored_text(f'    Skill Names:', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            skill_name = extract_and_get_title(skill_url)
                            print_colored_text(f'      [Skill]: {skill_name}', "32")
                        print_green_line(50)
                    else:
                        print_colored_text(f'    No skills found!', "31")
                print_horizontal_small_line(25)
        else:
            print(f"Lesson '{lesson_name}' not found in {semester}")

def parse_args():
    """Parse command-line arguments."""
    simplified_mode = False
    skills_mode = False
    show_descr = False
    skillname_mode = False
    lesson_name = None

    if len(sys.argv) > 1:
        if sys.argv[1] == "simplified":
            simplified_mode = True
        elif sys.argv[1] == "skills":
            skills_mode = True
            if len(sys.argv) > 2:
                lesson_name = ' '.join(sys.argv[2:])
        elif sys.argv[1] == "descr":
            show_descr = True
        elif sys.argv[1] == "skillname":
            skillname_mode = True
            if len(sys.argv) > 2:
                lesson_name = ' '.join(sys.argv[2:])
    return simplified_mode, skills_mode, show_descr, skillname_mode, lesson_name

def main(url: str, simplified: bool, skills: bool, show_descr: bool, skillname: bool, lesson_name: str = None):
    print_yellow_line(50)
    pdf_file_path = 'Program_of_Studies_2020-2021.pdf'
    download_pdf(url, pdf_file_path)

    pages = extract_text_from_pdf(pdf_file_path)

    marker = 'Course Outlines'
    text_after_marker = extract_text_after_marker(pages, marker)

    semesters = split_by_semester(text_after_marker)

    all_data = {}
    for i, semester_text in enumerate(semesters, 1):
        lessons = process_pages_by_lesson([page for page in pages if page in semester_text])
        lesson_count = len(lessons)
        all_data[f'Semester {i} ({lesson_count} lessons)'] = lessons

    if lesson_name:
        if skills:
            get_skills_for_lesson(all_data, lesson_name, skills=True, skillname=False)
        elif skillname:
            get_skills_for_lesson(all_data, lesson_name, skills=False, skillname=True)
        else:
            print(f"Invalid command format. Use 'skills' or 'skillname' followed by lesson name.")
    else:
        if show_descr:
            for semester, lessons in all_data.items():
                print_horizontal_line(50)
                print_colored_text(f'{semester}:', 33)
                print_horizontal_small_line(50)
                for lesson, description in lessons.items():
                    print(f'  {lesson}')
                    print_horizontal_small_line(25)
                    if description == "This lesson has no data!":
                        print_colored_text(f'    {description}', "31")
                    else:
                        print_colored_text(f'    {description}', "32")
                    print_horizontal_small_line(25)
        elif skills:
            for semester, lessons in all_data.items():
                print_horizontal_line(50)
                print_colored_text(f'{semester}:', 33)
                print_horizontal_small_line(50)
                for lesson, description in lessons.items():
                    print(f'  {lesson}')
                    print_horizontal_small_line(25)

                    skills_list = skill_extractor.get_skills([description])

                    filtered_skills = set()
                    for skill_set in skills_list:
                        for skill_url in skill_set:
                            filtered_skills.add(skill_url)

                    if filtered_skills:
                        print_colored_text(f'    Skills:', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            print_colored_text(f'      Skill URL: {skill_url}', "32")
                        print_green_line(50)
                    else:
                        print_colored_text(f'    No skills found', "31")
                    print_horizontal_small_line(25)

        elif skillname:
            for semester, lessons in all_data.items():
                print_horizontal_line(50)
                print_colored_text(f'{semester}:', 33)
                print_horizontal_small_line(50)
                for lesson, description in lessons.items():
                    print(f'  {lesson}')
                    print_horizontal_small_line(25)

                    skills_list = skill_extractor.get_skills([description])

                    filtered_skills = set()
                    for skill_set in skills_list:
                        for skill_url in skill_set:
                            filtered_skills.add(skill_url)

                    if filtered_skills:
                        print_colored_text(f'    Skill Names:', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            skill_name = extract_and_get_title(skill_url)
                            print_colored_text(f'      [Skill]: {skill_name}', "32")
                        print_green_line(50)
                    else:
                        print_colored_text(f'    No skills found!', "31")
                    print_horizontal_small_line(25)

    if simplified:
        print_horizontal_small_line(50)
        print_horizontal_line(50)

if __name__ == "__main__":
    pdf_url = "https://www.uom.gr/assets/site/public/nodes/4254/9477-Program_of_Studies_2020-2021.pdf"

    simplified_mode, skills_mode, show_descr, skillname_mode, lesson_name = parse_args()

    if simplified_mode or skills_mode or show_descr or skillname_mode:
        main(
            pdf_url,
            simplified=simplified_mode,
            skills=skills_mode,
            show_descr=show_descr,
            skillname=skillname_mode,
            lesson_name=lesson_name,
        )
    else:
        command, lesson_name = display_menu()

        if command == 'descr':
            main(pdf_url, simplified=False, skills=False, show_descr=True, skillname=False)
        elif command == 'skills':
            main(pdf_url, simplified=False, skills=True, show_descr=False, skillname=False, lesson_name=lesson_name)
        elif command == 'skillname':
            main(pdf_url, simplified=False, skills=False, show_descr=False, skillname=True, lesson_name=lesson_name)
        elif command == 'simplified':
            main(pdf_url, simplified=True, skills=False, show_descr=False, skillname=False)
        elif command == 'exit':
            print("Exiting program...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")
