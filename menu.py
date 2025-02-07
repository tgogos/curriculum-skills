
import sys
from output import print_logo, print_yellow_line, print_colored_text, print_horizontal_small_line


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
    print_colored_text("[NEW] 5. Write to Database (Use 'database')", 34)
    print_colored_text("[NEW] 6. Search for a Course by Skill (Use 'skillsearch' followed by skill name)", 35)
    print("7. Exit")
    print_yellow_line(50)
    choice = input("Enter your choice: ").strip().lower()

    parts = choice.split(maxsplit=1)
    command = parts[0] if parts else "exit" 
    lesson_name = parts[1] if len(parts) > 1 else None 

    return command, lesson_name


def parse_args():
    """Parse command-line arguments."""
    simplified_mode = False
    skills_mode = False
    show_descr = False
    skillname_mode = False
    lesson_name = None
    database_mode = False
    skillsearch_mode = False

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
        elif sys.argv[1] == "skillsearch":
            skillsearch_mode = True
            if len(sys.argv) > 2:
                lesson_name = ' '.join(sys.argv[2:])
        elif sys.argv[1] == "database":
            database_mode = True
    return simplified_mode, skills_mode, show_descr, skillname_mode, database_mode, skillsearch_mode, lesson_name