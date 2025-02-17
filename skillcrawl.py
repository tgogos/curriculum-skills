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
from pdf_utils import download_pdf, extract_text_from_pdf, extract_text_after_marker, process_pages_by_lesson, split_by_semester, get_pdf_path
from output import print_yellow_line, print_logo, print_horizontal_line, print_colored_text, print_horizontal_small_line, print_green_line, print_loading_line
from menu import display_menu, parse_args 
from skills import get_skills_for_lesson, extract_and_get_title, search_courses_by_skill
from helpers import find_possible_university, load_from_cache, save_to_cache
from database import write_to_database

CACHE_DIR = 'cache'
CACHE_FILE = 'pdf_cache.json'
university_name = None
university_country = None

os.makedirs(CACHE_DIR, exist_ok=True)

import requests


skill_extractor = SkillExtractor()

UNI_FILE = "university_cache.json"
UNIVERSITY_API = "http://universities.hipolabs.com/search?name="

if os.path.exists(UNI_FILE):
    with open(UNI_FILE, "r") as f:
        university_cache = json.load(f)
else:
    university_cache = {}

def save_cache():
    """Saves the university cache to a JSON file."""
    with open(UNI_FILE, "w") as f:
        json.dump(university_cache, f, indent=4)

def get_university_country(university_name):
    """Searches for the university and returns the country."""
    response = requests.get(UNIVERSITY_API + university_name)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0].get("country", "Unknown")  # Extract country if found
    return "Unknown"


def main(pdf_file_path: str, simplified: bool, skills: bool, show_descr: bool, skillname: bool, database: bool, skillsearch: bool, lesson_name: str = None):
    print_yellow_line(50)
    if not pdf_file_path:
        return
    
    if pdf_file_path in university_cache:
        university_name = university_cache[pdf_file_path]
    else:
        print_colored_text(f"[INITIALIZATION] Searching for University Name inside the provided PDF...", 33)
        print_loading_line(50)
        university_name = find_possible_university(pdf_file_path)
        university_cache[pdf_file_path] = university_name  # Store in cache
        university_country = get_university_country(university_name)
        save_cache()  # Persist cache to JSON


    cached_data = load_from_cache(university_name)

    university_country = get_university_country(university_name)

    
    if cached_data:
        print(f"Loading data from cache for {university_name}...")
        all_data = cached_data
    else:
        print(f"No cache found for {university_name}. Processing PDF...")
        pages = extract_text_from_pdf(pdf_file_path)
        university_name = find_possible_university(pdf_file_path)
        if university_country == "Greece":
            marker = ['Course Outlines', 'Course Content']
            text_after_marker = extract_text_after_marker(pages, marker)

            semesters = split_by_semester(text_after_marker)

            all_data = {}
            for i, semester_text in enumerate(semesters, 1):
                lessons = process_pages_by_lesson([page for page in pages if page in semester_text])
                lesson_count = len(lessons)
                all_data[f'Semester {i} ({lesson_count} lessons)'] = lessons

            for semester, lessons in all_data.items():
                for lesson, description in lessons.items():
                    skills_list = skill_extractor.get_skills([description])
                    filtered_skills = set()
                    for skill_set in skills_list:
                        for skill_url in skill_set:
                            filtered_skills.add(skill_url)

                    all_data[semester][lesson] = {
                        "description": description,
                        "skills": list(filtered_skills),
                    }
            save_to_cache(university_name, all_data)

        else:
            print_horizontal_line(50)
            print("Processing PDF for skill extraction...")
            pages = extract_text_from_pdf(pdf_file_path)
            skills_list = skill_extractor.get_skills([pages])
            filtered_skills = set(skill for skill_set in skills_list for skill in skill_set)

            all_data = {
                university_name: {
                    "info": pages,
                    "skills": list(filtered_skills)
                }
            }

            print_horizontal_small_line(40)
            print_colored_text("Processing skills and skill names...", 33)
            print_horizontal_line(50)
            print_colored_text(f"{university_name} Skill Analysis", 33)
            print_horizontal_line(50)
            filtered_skill_names = set()
            for skill_set in skills_list:
                    for skill_url in skill_set:
                        filtered_skills.add(skill_url)
                        skill_name = extract_and_get_title(skill_url) 
                        if skill_name:
                            filtered_skill_names.add(skill_name)
            if filtered_skills:
                        print_colored_text(f'    Skills:', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            print_colored_text(f'        Skill URL: {skill_url}', "32")
                        print_green_line(50)
            if filtered_skill_names:
                        print_colored_text(f'    Skill Names:', "32")
                        print_green_line(50)
                        for skill_name in filtered_skill_names:
                            print_colored_text(f'        [Skill]: {skill_name}', "32")
                            all_data[university_name]["skill_name"] = skill_name
                        print_green_line(50)
            save_to_cache(university_name, all_data)

                        


        
    

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
            get_skills_for_lesson(university_name, all_data, lesson_name, skills=True, skillname=False)
        elif skillname:
            get_skills_for_lesson(university_name, all_data, lesson_name, skills=False, skillname=True)
        elif skillsearch:
            search_courses_by_skill(all_data, lesson_name, skill_extractor, db_config, university_name)
        else:
            print(f"Invalid command format. Use 'skills' or 'skillname' followed by lesson name, or 'skillsearch' followed by skill.")
    else:
        if show_descr:
            for semester, lessons in all_data.items():
                print_horizontal_line(50)
                print_colored_text(f'{semester}:', 33)
                print_horizontal_small_line(50)
                for lesson, lesson_data in lessons.items():
                    print(f'  {lesson}')
                    print_horizontal_small_line(25)
                    description = lesson_data.get("description")
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
                for lesson_name, lesson_data in lessons.items():
                    print(f'   {lesson_name}')
                    print_horizontal_small_line(25)

                    lesson_cache = cached_data.get(semester, {}).get(lesson_name, {})  # Get cached data
                    cached_skills = lesson_cache.get("skills")  # Get cached skills
                    cached_skill_names = lesson_cache.get("skill_names") # Get cached skill names

                    if cached_skills and cached_skill_names:  # If BOTH skills and skill_names are in the cache
                        print_colored_text(f'    Skills:', "32")
                        print_green_line(50)
                        for skill_url in cached_skills:
                            print_colored_text(f'        Skill URL: {skill_url}', "32")
                        print_green_line(50)
                        continue

                    lesson_description = lesson_data.get("description", "")

                    if isinstance(lesson_description, dict):
                        lesson_description = lesson_description.get("text", "")

                    if isinstance(lesson_description, str):
                        skills_list = skill_extractor.get_skills([lesson_description])
                        filtered_skills = set()
                        filtered_skill_names = set()

                        for skill_set in skills_list:
                            for skill_url in skill_set:
                                filtered_skills.add(skill_url)
                                skill_name = extract_and_get_title(skill_url)
                                if skill_name:
                                    filtered_skill_names.add(skill_name)

                    if filtered_skills:
                        print_colored_text(f'    Skills:', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            print_colored_text(f'        Skill URL: {skill_url}', "32")
                        print_green_line(50)

                        if cached_data:
                            if semester not in cached_data:
                                cached_data[semester] = {}
                            if "skills" not in cached_data[semester].get(lesson_name, {}):
                                cached_data[semester][lesson_name] = cached_data[semester].get(lesson_name, {})
                            cached_data[semester][lesson_name]["skills"] = list(filtered_skills)
                        save_to_cache(university_name, cached_data)

                    else:
                        print_colored_text(f'    No skills found', "31")

            print_horizontal_small_line(25)

        elif skillname:
            for semester, lessons in all_data.items():
                print_horizontal_line(50)
                print_colored_text(f'{semester}:', 33)
                print_horizontal_small_line(50)
                for lesson_name, lesson_data in lessons.items():
                    print(f'   {lesson_name}')

                    lesson_cache = cached_data.get(semester, {}).get(lesson_name, {})
                    cached_skill_names = lesson_cache.get("skill_names")
                    cached_skills = lesson_cache.get("skills") # Get the URLs from the cache

                    if cached_skill_names:  # If skill_names are in the cache
                        print_horizontal_line(25)
                        print_colored_text(f'    Skill Names (from cache):', "32")
                        print_horizontal_line(25)
                        for skill_name in cached_skill_names:
                            print_colored_text(f'        [Skill]: {skill_name}', "32")
                        print_green_line(50)
                        print_horizontal_line(25)
                        continue 


                    lesson_description = lesson_data.get("description", "")

                    if isinstance(lesson_description, dict):
                        lesson_description = lesson_description.get("text", "")

                    if isinstance(lesson_description, str):
                        skills_list = skill_extractor.get_skills([lesson_description])
                        filtered_skills = set()
                        filtered_skill_names = set()
                        

                        for skill_set in skills_list:
                            for skill_url in skill_set:
                                filtered_skills.add(skill_url)
                                skill_name = extract_and_get_title(skill_url)
                                if skill_name:
                                    filtered_skill_names.add(skill_name)

                        if filtered_skill_names:
                            print_colored_text(f'    Skill Names:', "32")
                            print_green_line(50)
                            for skill_name in filtered_skill_names:
                                print_colored_text(f'        [Skill]: {skill_name}', "32")
                            print_green_line(50)


                        elif filtered_skills and not filtered_skill_names:
                            print_colored_text(f'    Skill Names (Extracted from URLs):', "32")
                            print_green_line(50)
                            for skill_url in filtered_skills:
                                skill_name = extract_and_get_title(skill_url)
                                if skill_name:
                                    filtered_skill_names.add(skill_name)
                                    print_colored_text(f'        [Skill]: {skill_name}', "32")
                            print_green_line(50)
                            if cached_data:
                                if semester not in cached_data:
                                    cached_data[semester] = {}
                                if "skill_names" not in cached_data[semester].get(lesson_name, {}):
                                    cached_data[semester][lesson_name] = cached_data[semester].get(lesson_name, {})
                                cached_data[semester][lesson_name]["skill_names"] = list(filtered_skill_names)
                                if "skills" not in cached_data[semester].get(lesson_name, {}):
                                    cached_data[semester][lesson_name] = cached_data[semester].get(lesson_name, {})
                                cached_data[semester][lesson_name]["skills"] = list(filtered_skills)
                                save_to_cache(university_name, cached_data)

                        else:
                            print_colored_text(f'    No skills found!', "31")
                    else:
                        print(f"Warning: Description for {lesson_name} is not a string. Skipping skill extraction.")

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
        main(pdf_file_path, simplified=False, skills=False, show_descr=True, skillname=False, database=False, skillsearch=False)
    elif command == 'skills':
        main(pdf_file_path, simplified=False, skills=True, show_descr=False, skillname=False, database=False, skillsearch=False, lesson_name=lesson_name)
    elif command == 'skillname':
        main(pdf_file_path, simplified=False, skills=False, show_descr=False, skillname=True, database=False, skillsearch=False, lesson_name=lesson_name)
    elif command == 'simplified':
        main(pdf_file_path, simplified=True, skills=False, show_descr=False, skillname=False, database=False, skillsearch=False)
    elif command == 'skillsearch':
        main(pdf_file_path, simplified=False, skills=False, show_descr=False, skillname=False, database=False, skillsearch=True, lesson_name=lesson_name)
    elif command == 'database':
        write_to_database(all_data, db_config)
    elif command == 'exit':
        print("Exiting program...")
        sys.exit(0)
    else:
        print("Invalid choice. Please try again.")
        main(pdf_file_path, simplified, skills, show_descr, skillname, database, skillsearch, lesson_name)


    

if __name__ == "__main__":
    pdf_file_path = get_pdf_path() # Get the PDF path from the user
    if pdf_file_path in university_cache:
        university_name = university_cache[pdf_file_path]
        university_country = get_university_country(university_name)
    else:
        print_colored_text(f"[INITIALIZATION] Searching for University Name inside the provided PDF...", 33)
        print_loading_line(50)
        university_name = find_possible_university(pdf_file_path)
        university_cache[pdf_file_path] = university_name  # Store in cache
        university_country = get_university_country(university_name)
        save_cache()  # Persist cache to JSON

    if university_country != "Greece":
        simplified_mode, skills_mode, show_descr, skillname_mode, database_mode, skillsearch_mode, lesson_name = parse_args()

        if database_mode:
            main(pdf_file_path, simplified=False, skills=False, show_descr=False, skillname=False, database=True, skillsearch=False)
        elif simplified_mode or skills_mode or show_descr or skillname_mode or skillsearch_mode:
            main(
                pdf_file_path,  # Correctly pass pdf_file_path
                simplified=simplified_mode,
                skills=skills_mode,
                show_descr=show_descr,
                skillname=skillname_mode,
                database=False,
                skillsearch=skillsearch_mode,
                lesson_name=lesson_name,
            )
        else:
            while True:  # Loop for valid menu input
                print_logo()
                cached_data = load_from_cache(university_name)
                if cached_data:
                    print_green_line(50)
                    print(f"Loading data from cache for {university_name}...")
                    print_green_line(50)
                    all_data = cached_data
                    print_colored_text(f'    Skills:', "32")
                    print_green_line(50)
                    for skill_url in all_data.get("skills", []):
                        print_colored_text(f'        Skill URL: {skill_url}', "32")
                    print_green_line(50)

                    print_colored_text(f'    Skill Names:', "32")
                    print_green_line(50)
                    for skill_name in all_data.get("skill_name", []):
                        print_colored_text(f'        [Skill]: {skill_name}', "32")
                    print_green_line(50)
                else:
                    print("Processing PDF for skill extraction...")
                    pages = extract_text_from_pdf(pdf_file_path)
                    skills_list = skill_extractor.get_skills([" ".join(pages)])
                    filtered_skills = set(skill for skill_set in skills_list for skill in skill_set)

                    all_data = {
                        "info": pages,
                        "skills": list(filtered_skills)
                    }

                    print_colored_text("Processing skills and skill names...", 31)
                    print_horizontal_line(50)
                    print_colored_text(f"{university_name} Skill Analysis", 33)
                    print_horizontal_line(50)
                    filtered_skill_names = set()
                    for skill_set in skills_list:
                        for skill_url in skill_set:
                            filtered_skills.add(skill_url)
                            skill_name = extract_and_get_title(skill_url) 
                            if skill_name:
                                filtered_skill_names.add(skill_name)
                    if filtered_skills:
                            print_colored_text(f'    Skills:', "32")
                            print_green_line(50)
                            for skill_url in filtered_skills:
                                print_colored_text(f'        Skill URL: {skill_url}', "32")
                            print_green_line(50)
                    if filtered_skill_names:
                            print_colored_text(f'    Skill Names:', "32")
                            print_green_line(50)
                            for skill_name in filtered_skill_names:
                                print_colored_text(f'        [Skill]: {skill_name}', "32")
                            all_data["skill_name"] = list(filtered_skill_names)
                            print_green_line(50)
                    save_to_cache(university_name, all_data)
                        
                print("1. Change File")
                print("2. Exit")
                print_yellow_line(50)
                command = input("\nEnter your choice: ").strip().lower()
                if command == "change file" or command == "1":
                    exec(open(__file__).read())
                    break                 
                elif command == "exit" or command == "2":
                    print("\nExiting program...")
                    sys.exit(0)  # Exits the program
                else:
                    print("\nInvalid choice. Try again.")  # Will be triggered for invalid input


    if pdf_file_path:  # Proceed only if a PDF file path was returned
        simplified_mode, skills_mode, show_descr, skillname_mode, database_mode, skillsearch_mode, lesson_name = parse_args()

        if database_mode:
            main(pdf_file_path, simplified=False, skills=False, show_descr=False, skillname=False, database=True, skillsearch=False)
        elif simplified_mode or skills_mode or show_descr or skillname_mode or skillsearch_mode:
            main(
                pdf_file_path,  # Correctly pass pdf_file_path
                simplified=simplified_mode,
                skills=skills_mode,
                show_descr=show_descr,
                skillname=skillname_mode,
                database=False,
                skillsearch=skillsearch_mode,
                lesson_name=lesson_name,
            )
        else:
            while True:  # Loop for valid menu input
                command, lesson_name = display_menu()

                if command == 'database':
                    main(pdf_file_path, simplified=False, skills=False, show_descr=False, skillname=False, database=True, skillsearch=False)
                    break  # Exit loop after command execution
                elif command == 'descr':
                    main(pdf_file_path, simplified=False, skills=False, show_descr=True, skillname=False, database=False, skillsearch=False)
                    break
                elif command == 'skills':
                    main(pdf_file_path, simplified=False, skills=True, show_descr=False, skillname=False, database=False, skillsearch=False, lesson_name=lesson_name)
                    break
                elif command == 'skillname':
                    main(pdf_file_path, simplified=False, skills=False, show_descr=False, skillname=True, database=False, skillsearch=False, lesson_name=lesson_name)
                    break
                elif command == 'skillsearch':
                    main(pdf_file_path, simplified=False, skills=False, show_descr=False, skillname=False, database=False, skillsearch=True, lesson_name=lesson_name)
                    break
                elif command == 'simplified':
                    main(pdf_file_path, simplified=True, skills=False, show_descr=False, skillname=False, database=False, skillsearch=False)
                    break
                elif command == 'exit':
                    print("Exiting program...")
                    sys.exit(0)
                else:
                    print("Invalid choice. Please try again.")
