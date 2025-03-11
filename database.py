import mysql.connector
from esco_skill_extractor import SkillExtractor
from skills import extract_and_get_title
from output import print_colored_text, print_horizontal_line, print_loading_line
from helpers import load_from_cache, save_to_cache

skill_extractor = SkillExtractor()

def is_database_connected(db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            conn.close()
            return True
    except mysql.connector.Error:
        return False
    return False

def get_university_id(cursor, university_name, country, number_of_semesters):
    """
    Check if a university exists; if not, insert it and return the university_id.
    """
    cursor.execute(
        "SELECT university_id FROM University WHERE university_name = %s AND country = %s",
        (university_name, country),
    )
    result = cursor.fetchone()

    if result:
        return result[0]
    
    cursor.execute(
        "INSERT INTO University (university_name, country, number_of_semesters) VALUES (%s, %s, %s)",
        (university_name, country, number_of_semesters),
    )
    return cursor.lastrowid

def write_to_database(all_data, db_config, university_name, country, number_of_semesters):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        print_colored_text("✅ Database connection established.", 33)

        university_id = get_university_id(cursor, university_name, country, number_of_semesters)

        cached_data = load_from_cache(university_name) or {}
        cached_skills = {}
        for semester, lessons in cached_data.items():
            if isinstance(lessons, dict):
                for lesson, data in lessons.items():
                    if isinstance(data, dict) and "skill_names" in data and "skills" in data:
                        cached_skills[lesson] = {
                            "skill_names": list(data["skill_names"]),
                            "skills": list(data["skills"]),
                            "skill_connect": data.get("skill_connect", {})  # Load existing skill_connect
                        }

        updated_skills_cache = {}

        for semester_name, lessons in all_data.items():
            if not isinstance(lessons, dict):
                continue

            for lesson_name, lesson_info in lessons.items():
                if not isinstance(lesson_info, dict):
                    continue

                lesson_desc = lesson_info.get("description", "")

                cursor.execute(
                    "INSERT INTO Lessons (lesson_name, semester, description, university_id) VALUES (%s, %s, %s, %s)",
                    (lesson_name, semester_name, lesson_desc, university_id),
                )

                lesson_id = cursor.lastrowid

                # Determine whether to use cached skills or extract new ones
                if lesson_name in cached_skills:
                    extracted_skills = cached_skills[lesson_name]["skill_names"]
                    extracted_skill_urls = cached_skills[lesson_name]["skills"]
                    skill_connect = cached_skills[lesson_name].get("skill_connect", {})
                else:
                    skills_list = skill_extractor.get_skills([lesson_desc])
                    extracted_skills = []
                    extracted_skill_urls = []
                    skill_connect = {}

                    for skill_set in skills_list:
                        for skill_url in skill_set:
                            skill_name = extract_and_get_title(skill_url) or "Unknown Skill"
                            skill_connect[skill_url] = skill_name  # Maintain URL-Skill mapping
                            
                    extracted_skill_urls = list(skill_connect.keys())
                    extracted_skills = list(skill_connect.values())

                    updated_skills_cache[lesson_name] = {
                        "skill_names": extracted_skills,
                        "skills": extracted_skill_urls,
                        "skill_connect": skill_connect  # Store mapping for cache update
                    }

                # Insert skills into the database, ensuring skill_connect consistency
                for skill_url, skill_name in skill_connect.items():
                    cursor.execute(
                        "INSERT INTO Skills (skill_name, skill_url, lesson_id) VALUES (%s, %s, %s)",
                        (skill_name, skill_url, lesson_id),
                    )

        # Update cache with the newly extracted skills and skill_connect
        for semester_name, lessons in all_data.items():
            if semester_name not in cached_data:
                cached_data[semester_name] = {}

            for lesson_name, skill_data in updated_skills_cache.items():
                if lesson_name in lessons:
                    cached_data[semester_name][lesson_name] = lessons[lesson_name]
                    cached_data[semester_name][lesson_name]["skill_names"] = skill_data["skill_names"]
                    cached_data[semester_name][lesson_name]["skills"] = skill_data["skills"]
                    cached_data[semester_name][lesson_name]["skill_connect"] = skill_data["skill_connect"]  # Add mapping

        save_to_cache(university_name, cached_data)

        connection.commit()
        print_colored_text("✅ Data successfully written to the database!", 33)

    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
        if connection.is_connected():
            connection.rollback()

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print_colored_text("🔒 Database connection closed.", 32)
