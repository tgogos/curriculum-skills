import pdfplumber
import requests
import re

# Format functions - Ignore

def print_colored_text(text: str, color_code: str) -> None:
    print(f"\033[{color_code}m{text}\033[0m")

def print_horizontal_line(length: int) -> None:
    print('=' * length)
    
def print_loading_line(length: int) -> None:
    print_colored_text('=' * length + '|] Loading...[|' + '=' * length, 33)
    
def print_horizontal_small_line(length: int) -> None:
    print('-' * length)
    

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
    
    text_after_marker = full_text[marker_index + len(marker):]
    return text_after_marker

def split_by_semester(text: str) -> list:
    print("Splitting text by semester")
    semesters = re.split(r'(?i)(\b\d+\s*(?:st|nd|rd|th)?\s*Semester\b)', text)
    combined_semesters = [''.join(semesters[i:i+2]) for i in range(1, len(semesters), 2)]
    print(f"Found semesters: {len(combined_semesters)}")
    return combined_semesters

def clean_lesson_name(name: str) -> str:
    return re.sub(r'\s*\(.*?\)\s*', '', name).strip()

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
                lesson_dict[lesson_name] = lesson_text

    return lesson_dict

def main(url: str):
    pdf_file_path = 'Program_of_Studies_2020-2021.pdf'
    download_pdf(url, pdf_file_path)

    pages = extract_text_from_pdf(pdf_file_path)

    marker = 'Course Outlines'
    text_after_marker = extract_text_after_marker(pages, marker)
    
    print_colored_text("Text after the marker (first 500 characters):", "32")
    print_colored_text(text_after_marker[:500], 32)
    print_horizontal_small_line(50)

    semesters = split_by_semester(text_after_marker)

    all_data = {}
    for i, semester_text in enumerate(semesters, 1):
        print(f"Processing Semester {i}")
        lessons = process_pages_by_lesson([page for page in pages if page in semester_text])
        lesson_count = len(lessons)
        all_data[f'Semester {i} ({lesson_count} lessons)'] = lessons

    if pages:
        first_page_text = pages[0]
        first_page_lines = first_page_text.split('\n')
        if len(first_page_lines) > 1 and first_page_lines[0].isupper():
            lesson_name = clean_lesson_name(first_page_lines[0])
            lesson_text = '\n'.join(first_page_lines[1:]).strip()
            # Add to Semester 1 if it exists
            if 'Semester 1' not in all_data:
                all_data['Semester 1'] = {}
            if lesson_name not in all_data['Semester 1']:
                all_data['Semester 1'][lesson_name] = lesson_text

    for semester, lessons in all_data.items():
        print_horizontal_line(50)
        print_colored_text(f'{semester}:', 33)
        print_horizontal_small_line(50)
        for lesson, description in lessons.items():
            print(f'  {lesson}')
            #print(f'    {description}')

if __name__ == "__main__":
    pdf_url = "https://www.uom.gr/assets/site/public/nodes/4254/9477-Program_of_Studies_2020-2021.pdf"
    main(pdf_url)
