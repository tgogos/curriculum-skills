import requests
from esco_skill_extractor import SkillExtractor
from fuzzywuzzy import fuzz
from helpers import load_cache, save_cache
from output import print_colored_text, print_horizontal_line, print_loading_line, print_horizontal_small_line, print_green_line

skill_extractor = SkillExtractor()


def get_skills_for_lesson(all_data, lesson_name, skills=False, skillname=False, threshold=80):
    cache = load_cache()
    print_horizontal_line(50)
    
    cached_skills = cache.get(lesson_name.lower())
    if cached_skills:
        print_colored_text(f"Using cached skills for '{lesson_name}'", 33)
        print_horizontal_small_line(50)
        for skill_url in cached_skills:
            print_colored_text(f'      Skill URL: {skill_url}', "32")
        return

    for semester, lessons in all_data.items():
        matched_lessons = [(lesson, fuzz.partial_ratio(lesson_name.lower(), lesson.lower())) for lesson in lessons]
    
        matched_lessons = [lesson for lesson, score in matched_lessons if score >= threshold]
        
        if matched_lessons:
            print_horizontal_line(50)
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


                        cache[lesson_name.lower()] = list(filtered_skills)
                        save_cache(cache)

                    else:
                        print_colored_text(f'    No skills found', "31")
                elif skillname:
                    if filtered_skills:
                        print_colored_text(f'    Skill Names:', "32")
                        print_green_line(50)
                        for skill_url in filtered_skills:
                            skill_name = extract_and_get_title(skill_url)
                            if skill_name:
                                print_colored_text(f'      [Skill]: {skill_name}', "32")
                        print_green_line(50)

                        cache[lesson_name.lower()] = list(filtered_skills)
                        save_cache(cache)
                    else:
                        print_colored_text(f'    No skills found!', "31")
                print_horizontal_small_line(25)
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
