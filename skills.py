import json
import requests
from esco_skill_extractor import SkillExtractor
import mysql.connector
from fuzzywuzzy import fuzz
from helpers import load_from_cache, save_to_cache
from output import print_colored_text, print_horizontal_line, print_loading_line, print_horizontal_small_line, print_green_line

skill_extractor = SkillExtractor()




def get_skills_for_lesson(university_name, all_data, lesson_name, skills=False, skillname=False, threshold=80, use_cache=True):
    cache = load_from_cache(university_name)
    cache_key = lesson_name.lower()

    # Check for just skills
    if use_cache and cache_key in cache and "skills" in cache[cache_key]:
        cached_skills = cache[cache_key]["skills"]
        print_colored_text(f"Using cached skills for '{lesson_name}'", 33)
        print_horizontal_small_line(50)
        for skill_url in cached_skills:
            print_colored_text(f'    Skill URL: {skill_url}', "32")
        return

    # Check for just skill names
    if use_cache and cache_key in cache and "skill_names" in cache[cache_key]:
        cached_skill_names = cache[cache_key]["skill_names"]
        print_colored_text(f"Using cached skill names for '{lesson_name}'", 33)
        print_horizontal_small_line(50)
        for skill_name in cached_skill_names:
            print_colored_text(f'    Skill Name: {skill_name}', "32")
        return

    for semester, lessons in all_data.items():
        matched_lessons = [(lesson, fuzz.partial_ratio(lesson_name.lower(), lesson.lower())) for lesson in lessons]
        matched_lessons = [lesson for lesson, score in matched_lessons if score >= threshold]

        if matched_lessons:
            print_horizontal_line(50)
            print_colored_text(f'{semester}:', 33)
            print_horizontal_small_line(50)

            for matched_lesson in matched_lessons:  # Iterate through the matched lessons
                lesson_data = lessons[matched_lesson]
                lesson_description = lesson_data.get("description", "")  # Safe access
                print(f'   {matched_lesson}')  # Use the matched lesson name
                print_horizontal_small_line(25)

                skills_list = skill_extractor.get_skills([lesson_description])  # Your skill extraction
                filtered_skills = set()
                filtered_skill_names = set()

                for skill_set in skills_list:
                    for skill_url in skill_set:
                        filtered_skills.add(skill_url)
                        skill_name = extract_and_get_title(skill_url)  # Extract name early
                        if skill_name:
                            filtered_skill_names.add(skill_name)

                if skills:  # Handle skills (URLs) - Only if skills=True
                    if filtered_skills:
                        print_colored_text(f'    Skills:', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            print_colored_text(f'        Skill URL: {skill_url}', "32")
                        print_green_line(50)

                        if use_cache:
                            if semester not in cache:
                                cache[semester] = {}
                            if "skills" not in cache[semester].get(matched_lesson, {}): # Check if skills key exists
                                cache[semester][matched_lesson] = cache[semester].get(matched_lesson, {}) # initialize to empty dict if matched_lesson key is not present
                            cache[semester][matched_lesson]["skills"] = list(filtered_skills) # Update only the skills
                            save_to_cache(university_name, cache)

                    else:
                        print_colored_text(f'    No skills found', "31")

                if skillname:  # Handle skill names - Only if skillname=True
                    if filtered_skill_names:
                        print_colored_text(f'    Skill Names:', "32")
                        print_green_line(50)
                        for skill_name in filtered_skill_names:
                            print_colored_text(f'        [Skill]: {skill_name}', "32")
                        print_green_line(50)

                        if use_cache:
                            if semester not in cache:
                                cache[semester] = {}
                            if "skill_names" not in cache[semester].get(matched_lesson, {}): # Check if skill_names key exists
                                cache[semester][matched_lesson] = cache[semester].get(matched_lesson, {}) # initialize to empty dict if matched_lesson key is not present
                            cache[semester][matched_lesson]["skill_names"] = list(filtered_skill_names) # Update only the skill_names
                            save_to_cache(university_name, cache)
                    elif filtered_skills and not filtered_skill_names: #If skillname is true but no skill_names were found, extract them from the URLs
                        print_colored_text(f'    Skill Names (Extracted from URLs):', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            skill_name = extract_and_get_title(skill_url)
                            if skill_name:
                                filtered_skill_names.add(skill_name)
                                print_colored_text(f'        [Skill]: {skill_name}', "32")
                        print_green_line(50)
                        if use_cache:
                            if semester not in cache:
                                cache[semester] = {}
                            if "skill_names" not in cache[semester].get(matched_lesson, {}): # Check if skill_names key exists
                                cache[semester][matched_lesson] = cache[semester].get(matched_lesson, {}) # initialize to empty dict if matched_lesson key is not present
                            cache[semester][matched_lesson]["skill_names"] = list(filtered_skill_names) # Update only the skill_names
                            save_to_cache(university_name, cache)

        else:
            print(f"Lesson '{lesson_name}' not found in {semester}")
    print_horizontal_line(25)


def extract_and_get_title(skill_url):
    try:
        if not skill_url.startswith("http://data.europa.eu/esco/skill/"):
            print("Invalid skill URL format.")
            return "Error: Invalid URL format"
        skill_id = skill_url.split('/skill/')[1]

        api_url = f"https://ec.europa.eu/esco/api/resource/skill?uri={skill_url}"
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            skill_title = data.get('preferredLabel', {}).get('en-us', None)
            return skill_title
        else:
            return None

    except Exception as e:
        print(f"Error: {e}")
        return "Error: Exception occurred"


def search_courses_by_skill(all_data, search_skill, skill_extractor, db_config, university_name, threshold=52, use_cache=True):
    from database import is_database_connected  # Assuming this is defined elsewhere
    if not search_skill:
        print_colored_text("No skill provided for search.", 31)
        return []

    print_horizontal_line(50)
    print_colored_text(f"Searching for courses related to skill: {search_skill}", 35)

    found_courses = []

    if is_database_connected(db_config):
        print_colored_text("Database connected. Fetching skills from database...", 32)

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT semester, lesson_name, skill_name 
                FROM skills_table 
                WHERE LOWER(skill_name) LIKE %s
            """
            cursor.execute(query, (f"%{search_skill.lower()}%",))

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            for row in results:
                similarity_score = fuzz.ratio(search_skill.lower(), row["skill_name"].lower())
                if similarity_score >= threshold:
                    found_courses.append((row["semester"], row["lesson_name"], row["skill_name"], similarity_score))

        except mysql.connector.Error as e:
            print_colored_text(f"Database error: {e}", 31)
            return []

    else:  # Database not connected
        print_colored_text("Database not connected. Using cache instead.", 33)
        print_horizontal_line(50)
        cache = load_from_cache(university_name)  # Assuming load_from_cache is defined
        if cache is None:
            cache = {}

        for semester, lessons in all_data.items():
            for lesson_name, lesson_data in lessons.items():
                lesson_cache = cache.get(semester, {}).get(lesson_name, {})
                lesson_skills = lesson_cache.get("skill_names", {})
                lesson_urls = lesson_cache.get("skills", {}) # Get the URLs from the cache
                lesson_description = lesson_data.get("description", "")

                if (not lesson_skills or not lesson_urls) and use_cache and lesson_description != "This lesson has no data!":  # Check for BOTH
                    print_colored_text(f"Cache incomplete for '{lesson_name}'! Creating/updating now.", 32)
                    print(f"Extracting skills for lesson '{lesson_name}'...")

                    lesson_description = lesson_data.get("description", "")
                    if isinstance(lesson_description, dict):
                        lesson_description = lesson_description.get("text", "")

                    if isinstance(lesson_description, str):
                        skills_list = skill_extractor.get_skills([lesson_description])
                        new_lesson_skills = set() # Dictionary for skill names
                        new_lesson_urls = set() # Set for skill URLs


                        for skill_set in skills_list:
                            for skill_url in skill_set:
                                new_lesson_urls.add(skill_url) # Add URL to set
                                skill_name = extract_and_get_title(skill_url)
                                if skill_name:
                                    new_lesson_skills.add(skill_name)  # Add name to dict with URL as key

                        if semester not in cache:
                            cache[semester] = {}
                        if lesson_name not in cache[semester]:
                            cache[semester][lesson_name] = {}
                        cache[semester][lesson_name]["skill_names"] = list(new_lesson_skills)  # Update skill names
                        cache[semester][lesson_name]["skills"] = list(new_lesson_urls) # Update skill URLs
                        save_to_cache(university_name, cache)
                    else:
                        print(f"Warning: Description for {lesson_name} is not a string. Skipping skill extraction.")

                if isinstance(lesson_skills, dict): # Check if it is a dictionary
                    for skill_url, skill_name in lesson_skills.items():
                        similarity_score = fuzz.ratio(search_skill.lower(), skill_name.lower())
                        if similarity_score >= threshold:
                            found_courses.append((semester, lesson_name, skill_name, similarity_score))

                elif isinstance(lesson_skills, list): #Handle skill_names stored as lists
                    for skill_name in lesson_skills:
                        similarity_score = fuzz.ratio(search_skill.lower(), skill_name.lower())
                        if similarity_score >= threshold:
                            found_courses.append((semester, lesson_name, skill_name, similarity_score))


    if found_courses:
        no_limit1 = True
        no_limit2 = True
        no_limit3 = True
        for semester, lesson_name, matched_skill, score in sorted(found_courses, key=lambda x: x[3], reverse=True):
            if score >= 70 and no_limit1:
                print_colored_text(f"Most Accurate Courses (Score >= 70)", 32)
                print_horizontal_small_line(50)
                no_limit1 = False
            elif score >= 56 and score < 70 and no_limit2:
                print_horizontal_small_line(50)
                print_colored_text(f"Mediumly Accurate Courses (Score >= 56)", 33)
                print_horizontal_small_line(50)
                no_limit2 = False
            elif score >= 40 and score < 56 and no_limit3:
                print_horizontal_small_line(50)
                print_colored_text(f"Least Accurate Courses (Score >= 52)", 34)
                print_horizontal_small_line(50)
                no_limit3 = False
            print(f" {lesson_name} | Matched Skill: {matched_skill} (Score: {score})")
        print_horizontal_line(50)
    else:
        print_horizontal_line(50)
        print_colored_text("No closely matching courses found.", 31)
        print_horizontal_line(50)

    return found_courses