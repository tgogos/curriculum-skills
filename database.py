import mysql.connector
from esco_skill_extractor import SkillExtractor
from skills import extract_and_get_title
from output import print_colored_text, print_horizontal_line, print_loading_line

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

def write_to_database(all_data, db_config):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        print_colored_text("Database connection established.", 33)

        for semester, lessons in all_data.items():
            for lesson_name, lesson_description in lessons.items():
                print_horizontal_line(50)
                print_colored_text(f"[Inserting lesson]: {lesson_name} into the database.", 32)
                print_horizontal_line(50)
                cursor.execute(
                    "INSERT INTO Lessons (lesson_name, semester, description) VALUES (%s, %s, %s)",
                    (lesson_name, semester, lesson_description),
                )
                lesson_id = cursor.lastrowid

                skills_list = skill_extractor.get_skills([lesson_description])
                filtered_skills = set()
                for skill_set in skills_list:
                    for skill_url in skill_set:
                        filtered_skills.add(skill_url)

                for skill_url in filtered_skills:
                    skill_name = extract_and_get_title(skill_url) or "Unknown Skill"
                    print_colored_text(f"[Inserting skill]: {skill_name} with URL ==> {skill_url}", 33)
                    cursor.execute(
                        "INSERT INTO Skills (skill_name, skill_url, lesson_id) VALUES (%s, %s, %s)",
                        (skill_name, skill_url, lesson_id),
                    )

        connection.commit()
        print_loading_line(25)
        print_colored_text("Data successfully written to the database!", 33)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        if connection.is_connected():
            connection.rollback()

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print_colored_text("Database connection closed.", 32)