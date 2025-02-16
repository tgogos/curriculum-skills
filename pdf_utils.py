
import os
import pdfplumber
import requests
import re
import glob
from thefuzz import fuzz, process
from output import print_loading_line
from helpers import is_cached, load_cache, save_cache, contains_no_lowercase_letters, clean_lesson_name, contains_greek_characters
from output import print_colored_text


def download_pdf(url: str, save_path: str) -> str:
    curriculum_folder = "curriculum"
    os.makedirs(curriculum_folder, exist_ok=True)
    save_path = os.path.join(curriculum_folder, save_path)

    if os.path.exists(save_path):
        print("Curriculum already retrieved!")
        return save_path

    print(f"Downloading PDF from {url}")
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)
    return save_path

def extract_text_from_pdf(pdf_file_path: str) -> list:
    cache_key = f"text_{pdf_file_path}"
    if is_cached(cache_key):
        print(f"Loading text from cache for {pdf_file_path}")
        print_loading_line(25)
        return load_cache()[cache_key]
    
    print(f"Extracting text from PDF: {pdf_file_path}")
    print_loading_line(25)
    page_texts = []
    with pdfplumber.open(pdf_file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            page_texts.append(text)

    cache = load_cache()
    cache[cache_key] = page_texts
    save_cache(cache)
    return page_texts


def extract_text_after_marker(text: list, markers: list) -> str:
    cache_key = f"text_after_marker_{hash(''.join(markers))}"

    if is_cached(cache_key):
        print(f"Loading text after markers from cache.")
        print_loading_line(25)
        return load_cache()[cache_key]

    print_colored_text(f" >>> Extracting text after markers: {', '.join(markers)}", 34)
    full_text = '\n'.join(text)
    for marker in markers:
        marker_index = full_text.lower().find(marker.lower())
        if marker_index != -1:
            print_colored_text(f"Found marker: {marker}", 32)
            return full_text[marker_index + len(marker):]
    
    print("No marker found in the text.")
    return ""

def split_by_semester(text: str) -> list:
    cache_key = f"semesters_{hash(text)}"
    if is_cached(cache_key):
        print(f"Loading semesters from cache")
        return load_cache()[cache_key]
    
    print("Splitting text by semester")
    semesters = re.split(r'(?i)(\b\d+\s*(?:st|nd|rd|th)?\s*Semester\b)', text)
    combined_semesters = []
    seen_semesters = set()
    for i in range(1, len(semesters), 2):
        semester = ''.join(semesters[i:i+2]).strip()  # Remove leading/trailing whitespace
        best_match = process.extractOne(semester, list(seen_semesters)) if seen_semesters else None #find best match
        if best_match is None or best_match[1] < 90:  # Adjust threshold as needed
            combined_semesters.append(semester)
            seen_semesters.add(semester)
    
    cache = load_cache()
    cache[cache_key] = combined_semesters
    save_cache(cache)
    
    return combined_semesters

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


def get_pdf_path():
    """Searches for PDF files in the 'curriculum' folder and prompts the user to choose."""
    pdf_files = glob.glob("curriculum/*.pdf")  # Find all PDFs in 'curriculum'

    if not pdf_files:
        print_colored_text("No PDF files found in the 'curriculum' folder.", 31)
        return None

    if len(pdf_files) == 1:
        print_colored_text(f"Found PDF file: {pdf_files[0]}", 32)
        return pdf_files[0]

    print_colored_text("Multiple PDF files found. Please choose one:", 32)
    for i, file in enumerate(pdf_files):
        print(f"{i + 1}. {file}")

    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(pdf_files):
                return pdf_files[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")