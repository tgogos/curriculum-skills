import json
from main import get_top_skills, TopSkillsRequest

def test_compare_top_skills():
    with open("tests/json/top_skills_cambridge_expected.json", "r", encoding="utf-8") as f:
        expected = json.load(f)

    response = get_top_skills(TopSkillsRequest(university_name="University of Cambridge", top_n=50))
    actual = response["top_skills"]

    assert len(actual) == len(expected["top_skills"]), f"Expected {len(expected['top_skills'])}, got {len(actual)}"


    for expected_skill, actual_skill in zip(expected["top_skills"], actual):
        assert actual_skill["skill"] == expected_skill["skill"]
        assert actual_skill["frequency"] == expected_skill["frequency"]

    matched_count = sum(
        1 for e, a in zip(expected["top_skills"], actual)
        if e["skill"] == a["skill"] and e["frequency"] == a["frequency"]
    )

    print("\n✅ Top Skills Matching Report")
    print(f"✔ Total top skills matched: {matched_count} / {len(expected['top_skills'])}")
    print("\n📋 Sample of actual top skills:")
    for skill in actual[:5]:
        print(f"- {skill['skill']} (freq: {skill['frequency']})")

