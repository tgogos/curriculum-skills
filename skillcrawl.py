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
import os
import json
import mysql.connector


from database import write_to_database
from pdf_utils import download_pdf, extract_text_from_pdf, extract_text_after_marker, process_pages_by_lesson, split_by_semester
from output import print_yellow_line, print_horizontal_line, print_colored_text, print_horizontal_small_line, print_green_line
from menu import display_menu, parse_args 
from skills import get_skills_for_lesson, extract_and_get_title

CACHE_DIR = 'cache'
CACHE_FILE = 'pdf_cache.json'

os.makedirs(CACHE_DIR, exist_ok=True)

import requests


skill_extractor = SkillExtractor()



def main(url: str, simplified: bool, skills: bool, show_descr: bool, skillname: bool, database: bool, lesson_name: str = None):
    print_yellow_line(50)
    pdf_file_path = 'Program_of_Studies_2020-2021.pdf'
    download_pdf(url, pdf_file_path)

    pages = extract_text_from_pdf(pdf_file_path)

    marker = ['Course Outlines', 'Course Content']
    text_after_marker = extract_text_after_marker(pages, marker)

    semesters = split_by_semester(text_after_marker)

    all_data = {}
    for i, semester_text in enumerate(semesters, 1):
        lessons = process_pages_by_lesson([page for page in pages if page in semester_text])
        lesson_count = len(lessons)
        all_data[f'Semester {i} ({lesson_count} lessons)'] = lessons

    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'SkillCrawl'
    }

    if database:
        write_to_database(all_data, db_config)
        return


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
                            if skill_name:
                                print_colored_text(f'      [Skill]: {skill_name}', "32")
                        print_green_line(50)
                    else:
                        print_colored_text(f'    No skills found!', "31")
                    print_horizontal_small_line(25)

        elif simplified:
            print_horizontal_small_line(50)
            for semester, lessons in all_data.items():
                print_horizontal_line(50)
                print_colored_text(f'{semester}:', 33)
                print_horizontal_line(50)
                for lesson_name, lesson_description in lessons.items():
                    print_colored_text(f'  {lesson_name}', "32")
            print_horizontal_small_line(50)

    command, lesson_name = display_menu()

    if command == 'descr':
        main(pdf_url, simplified=False, skills=False, show_descr=True, skillname=False, database=False)
    elif command == 'skills':
        main(pdf_url, simplified=False, skills=True, show_descr=False, skillname=False, database=False, lesson_name=lesson_name)
    elif command == 'skillname':
        main(pdf_url, simplified=False, skills=False, show_descr=False, skillname=True, database=False, lesson_name=lesson_name)
    elif command == 'simplified':
        main(pdf_url, simplified=True, skills=False, show_descr=False, skillname=False, database=False)
    elif command == 'database':
        write_to_database(all_data, db_config)
    elif command == 'exit':
        print("Exiting program...")
        sys.exit(0)
    else:
        print("Invalid choice. Please try again.")
        main(url, simplified, skills, show_descr, skillname, database, lesson_name)

if __name__ == "__main__":
    pdf_url = "https://www.uom.gr/assets/site/public/nodes/4254/9477-Program_of_Studies_2020-2021.pdf"

    simplified_mode, skills_mode, show_descr, skillname_mode, database_mode, lesson_name = parse_args()

    if database_mode:
        main(pdf_url, simplified=False, skills=False, show_descr=False, skillname=False, database=True)
    elif simplified_mode or skills_mode or show_descr or skillname_mode:
        main(
            pdf_url,
            simplified=simplified_mode,
            skills=skills_mode,
            show_descr=show_descr,
            skillname=skillname_mode,
            database=False,
            lesson_name=lesson_name,
        )
    else:
        command, lesson_name = display_menu()

        if command == 'database':
            main(pdf_url, simplified=False, skills=False, show_descr=False, skillname=False, database=True)
        elif command == 'descr':
            main(pdf_url, simplified=False, skills=False, show_descr=True, skillname=False, database=False)
        elif command == 'skills':
            main(pdf_url, simplified=False, skills=True, show_descr=False, skillname=False, database=False, lesson_name=lesson_name)
        elif command == 'skillname':
            main(pdf_url, simplified=False, skills=False, show_descr=False, skillname=True, database=False, lesson_name=lesson_name)
        elif command == 'simplified':
            main(pdf_url, simplified=True, skills=False, show_descr=False, skillname=False, database=False)
        elif command == 'exit':
            print("Exiting program...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")
