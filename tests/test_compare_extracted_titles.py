import json
import os
from main import process_pdf, PDFProcessingRequest

def test_compare_extracted_titles():
    with open("tests/json/extracted_titles_expected.json", "r", encoding="utf-8") as f:
        expected = json.load(f)

    pdf_path = os.path.abspath("tests/sample_pdfs/Cambridge University.pdf")
    response = process_pdf(PDFProcessingRequest(pdf_name=pdf_path))

    actual = response["data"]

    for semester in expected["data"]:
        if semester in ["university_name", "university_country"]:
            continue

        assert semester in actual, f"Missing semester: {semester}"
        for lesson in expected["data"][semester]:
            assert lesson in actual[semester], f"Missing lesson: {lesson} in {semester}"
            assert isinstance(actual[semester][lesson], dict), f"{lesson} in {semester} is not a dict"
            assert actual[semester][lesson]["description"] == expected["data"][semester][lesson]["description"]
    

    total_semesters = len([s for s in expected["data"] if s not in ["university_name", "university_country"]])
    total_lessons = sum(len(lessons) for sem, lessons in expected["data"].items() if sem not in ["university_name", "university_country"])

    print(f"\n✅ Title Matching Report")
    print(f"✔ Semesters matched: {total_semesters}")
    print(f"✔ Lessons matched: {total_lessons}")

