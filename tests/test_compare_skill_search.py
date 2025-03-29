import json
from main import search_skill, SkillSearchRequest

def test_compare_skill_search():
    with open("tests/json/C_skill_search_expected.json", "r", encoding="utf-8") as f:
        expected = json.load(f)

    response = search_skill(SkillSearchRequest(skill="C++"))
    actual = response["results"]

    for uni in expected["results"]:
        assert uni in actual, f"Missing university: {uni}"
        for semester in expected["results"][uni]:
            assert semester in actual[uni], f"Missing semester: {semester} in {uni}"
            for lesson in expected["results"][uni][semester]:
                assert lesson in actual[uni][semester], f"Missing lesson: {lesson} in {uni}, {semester}"
                expected_skills = expected["results"][uni][semester][lesson]
                actual_skills = actual[uni][semester][lesson]
                assert actual_skills == expected_skills, f"Mismatch in skill search result for {lesson}"

    total_universities = len(expected["results"])
    total_semesters = sum(len(expected["results"][uni]) for uni in expected["results"])
    total_lessons = sum(
        len(lessons)
        for uni in expected["results"]
        for sem, lessons in expected["results"][uni].items()
    )
    total_skills = sum(
        len(skills)
        for uni in expected["results"]
        for sem in expected["results"][uni]
        for skills in expected["results"][uni][sem].values()
    )

    print(f"\n✅ Skill Search Report")
    print(f"✔ Universities matched: {total_universities}")
    print(f"✔ Semesters matched: {total_semesters}")
    print(f"✔ Lessons matched: {total_lessons}")
    print(f"✔ Skills matched: {total_skills}")

