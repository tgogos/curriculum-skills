from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import write_to_database, is_database_connected
from skills import get_skills_for_lesson, search_courses_by_skill, search_courses_by_skill_database, extract_and_get_title
from pdf_utils import extract_text_from_pdf, split_by_semester, process_pages_by_lesson, extract_text_after_marker
from config import DB_CONFIG
import os
import json
from helpers import find_possible_university, load_from_cache, save_to_cache, load_university_cache, save_cache
from skillcrawl import get_university_country
from typing import List
from fuzzywuzzy import process
from fastapi import UploadFile
from esco_skill_extractor import SkillExtractor
from typing import Dict, Optional
import re
from crawler import UniversityCrawler

skill_extractor = SkillExtractor()

app = FastAPI(title="SkillCrawl API", description="API for skill extraction and course search.")

class CrawlRequest(BaseModel):
    url: str

class PDFProcessingRequest(BaseModel):
    pdf_name: str

class SkillSearchRequest(BaseModel):
    skill: str
    university: str = None 

class LessonRequest(BaseModel):
    university_name: str
    lesson_name: str

@app.get("/health")
def health_check():
    return {"status": "running"}

@app.get("/list_pdfs")
def list_pdfs():

    university_cache = load_university_cache()
    curriculum_folder = "curriculum"
    if not os.path.exists(curriculum_folder):
        os.makedirs(curriculum_folder) 
    
    pdf_files = []
    
    for f in os.listdir(curriculum_folder):
        if f.endswith(".pdf"):
            cached_data = load_from_cache(f) or {}

            university_name = cached_data.get("university_name", "").strip()
            university_country = cached_data.get("university_country", "").strip()

            if not university_name or "unknown" in university_name.lower():
                filename = f.replace(".pdf", "")
                university_name = re.sub(r"[^a-zA-Z0-9]+", " ", filename).strip()
                print(f"Extracted university name from filename in /list_pdfs: {university_name}") 

            if not university_country or university_country.lower() == "unknown":
                university_country = get_university_country(university_name) if university_name else "Unknown"

            pdf_files.append({
                "filename": f,
                "university_name": university_name,
                "university_country": university_country
            })

            university_cache[university_name] = {
                "name": university_name,
                "country": university_country,
                "pdf_file": f
            }
            save_cache()
    
    return {"pdf_files": pdf_files}

@app.post("/process_pdf")
def process_pdf(request: PDFProcessingRequest):
    print(f"Received request to process PDF: {request.pdf_name}")
    
    curriculum_folder = "curriculum"
    if not os.path.exists(curriculum_folder):
        os.makedirs(curriculum_folder)
    
    matching_files = [f for f in os.listdir(curriculum_folder) if f.endswith(".pdf") and request.pdf_name in f]
    
    if not matching_files:
        raise HTTPException(
            status_code=404, 
            detail=f"No PDF matching '{request.pdf_name}' found in 'curriculum/'. Available PDFs: {os.listdir(curriculum_folder)}"
        )
    
    pdf_path = os.path.join(curriculum_folder, matching_files[0])
    pages = extract_text_from_pdf(pdf_path)
    
    university_name = find_possible_university(pdf_path) or ""
    university_country = get_university_country(university_name) if university_name else "Unknown"

    university_cache = load_university_cache()
    

    if university_name in university_cache:
        university_country = university_cache[university_name].get("country", "Unknown")
    else:
        filename = os.path.basename(pdf_path).replace(".pdf", "")
        

        if not university_name or "Unknown University" in university_name or university_country == "Unknown":
            university_name = re.sub(r"[^a-zA-Z0-9]+", " ", filename).strip()
            print(f"Extracted university name from filename: {university_name}")
        
        university_country = get_university_country(university_name) if university_name else "Unknown"


        university_cache[university_name] = {
            "name": university_name,
            "country": university_country
        }
        save_cache()
    
    marker = ['Course Outlines', 'Course Content']
    text_after_marker = extract_text_after_marker(pages, marker)
    
    semesters = split_by_semester(text_after_marker)
    all_data = {}
    
    for i, semester_text in enumerate(semesters, 1):
        lessons = process_pages_by_lesson([page for page in pages if page in semester_text])
        lesson_count = len(lessons)
        lesson_data = {}
        
        for lesson, description in lessons.items():
            skills_list = skill_extractor.get_skills([description])
            filtered_skills = {skill_url for skill_set in skills_list for skill_url in skill_set}
            
            lesson_data[lesson] = {
                "description": description,
                "skills": list(filtered_skills)
            }
        
        all_data[f"Semester {i} ({lesson_count} lessons)"] = lesson_data
    
    if university_name:
        all_data["university_name"] = university_name
        all_data["university_country"] = university_country
    
    if not isinstance(all_data, dict):
        raise ValueError("Data to be cached must be a dictionary.")
    
    save_to_cache(university_name, all_data)
    
    return {"message": "PDF processed successfully.", "data": all_data}


CACHE_DIR = "cache"  

def load_all_cached_data():
    """
    Searches through the cache folder and loads data for all universities.
    Returns a dictionary where keys are university names, and values are their cached lessons.
    """
    all_data = {}

    if not os.path.exists(CACHE_DIR):
        print("⚠️ Cache directory does not exist.")
        return {}

    for filename in os.listdir(CACHE_DIR):
        if filename.endswith(".json"): 
            university_name = filename.replace(".json", "")
            try:
                with open(os.path.join(CACHE_DIR, filename), "r", encoding="utf-8") as file:
                    all_data[university_name] = json.load(file)
            except json.JSONDecodeError:
                print(f"❌ Failed to load cache for {university_name}. Skipping...")
    
    return all_data 

@app.post("/filter_skillnames")
def get_skills(request: LessonRequest):
    """
    API endpoint to get skill names based on university and lesson name.
    - First checks cache.
    - If not in cache, searches the database.
    - If missing in database, writes from cache to the database.
    """


    if request.university_name:
        all_data = load_from_cache(request.university_name)
    else:
        all_data = load_all_cached_data() 


    skills = get_skills_for_lesson(request.university_name, all_data, request.lesson_name, skillname=True, db_config=DB_CONFIG)

    return {"Data": skills or []} 

@app.post("/calculate_skillnames")
def calculate_skillnames(university_name: str, lesson_name: Optional[str] = None):
    """
    Calculate skill names for a specific university, using fuzzy matching for university & lesson names.
    
    Args:
        university_name (str): The university to retrieve skills for.
        lesson_name (Optional[str]): If provided, only extract skills for this lesson.

    Returns:
        dict: Extracted skill names for the university (or specific lesson).
    """

    all_cached_data = load_all_cached_data() 
    university_names = [name.replace("_cache", "").strip() for name in all_cached_data.keys()]

    if not university_names:
        raise HTTPException(status_code=404, detail="No universities found in cache.")


    best_match, score = process.extractOne(university_name, university_names)

    if score < 70:  
        raise HTTPException(status_code=404, detail=f"No close match found for university '{university_name}'.")

    print(f"[INFO] Fuzzy matched university '{university_name}' -> '{best_match}' with score {score}")

    university_name = next((key for key in all_cached_data.keys() if best_match in key), best_match)
    cached_data = all_cached_data[university_name]

    extracted_skills = {}

    university_name = university_name.replace("_cache", "").strip()

    for semester, lessons in cached_data.items():
        if semester in ["university_name", "university_country"]:  
            continue  

        if lesson_name:
            lesson_names = list(lessons.keys())
            best_lesson_match, lesson_score = process.extractOne(lesson_name, lesson_names)
            
            if lesson_score < 85:
                raise HTTPException(status_code=404, detail=f"No close match found for lesson '{lesson_name}'.")

            print(f"[INFO] Fuzzy matched lesson '{lesson_name}' -> '{best_lesson_match}' with score {lesson_score}")
            lesson_name = best_lesson_match
            lessons = {lesson_name: lessons[lesson_name]}

        for lesson, lesson_data in lessons.items():
            print(f"[INFO] Processing skills for: {lesson} in {semester}")

            lesson_cache = cached_data.get(semester, {}).get(lesson, {})
            cached_skill_names = set(lesson_cache.get("skill_names", []))
            cached_skills = set(lesson_cache.get("skills", []))

            lesson_description = lesson_data.get("description", "")

            if isinstance(lesson_description, dict):
                lesson_description = lesson_description.get("text", "")

            if not isinstance(lesson_description, str):
                print(f"[WARNING] Description for {lesson} is not a string. Skipping skill extraction.")
                continue

            skills_list = skill_extractor.get_skills([lesson_description])
            new_skills = set()
            new_skill_names = set()

            for skill_set in skills_list:
                for skill_url in skill_set:
                    new_skills.add(skill_url)

                    skill_name = extract_and_get_title(skill_url)
                    if skill_name and skill_name not in cached_skill_names:
                        cached_skill_names.add(skill_name)
                        new_skill_names.add(skill_name)

            if new_skill_names:
                if semester not in cached_data:
                    cached_data[semester] = {}
                if lesson not in cached_data[semester]:
                    cached_data[semester][lesson] = {}

                cached_data[semester][lesson]["skill_names"] = list(cached_skill_names)
                save_to_cache(university_name, cached_data)

            updated_skills = cached_skills | new_skills
            if updated_skills != cached_skills:
                cached_data[semester][lesson]["skills"] = list(updated_skills)
                save_to_cache(university_name, cached_data)

            extracted_skills[lesson] = list(cached_skill_names)

    return {"university_name": university_name, "skills": extracted_skills}


@app.post("/search_skill")
def search_skill(request: SkillSearchRequest):
    """
    You can search if a skill exists in the database.
    In return:
    - University name(s) the skill is in
    - Lesson(s) the skill is in
    - And frequency of appearance
    """
    if not is_database_connected(DB_CONFIG):
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    results = search_courses_by_skill_database(request.skill, DB_CONFIG, request.university)
    return {"results": results}


@app.get("/search_json_in_cache")
def search_json_in_cache(university_name: str):
    """
    Searches for a cached JSON file based on a fuzzy match of the university name.
    """
    cache_folder = "cache"
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder) 
    
    json_files = [f for f in os.listdir(cache_folder) if f.endswith(".json")]
    
    if not json_files:
        raise HTTPException(status_code=404, detail="No cached files found.")

    best_match, score = process.extractOne(university_name, json_files)

    if score < 60: 
        raise HTTPException(status_code=404, detail=f"No close match found for university: {university_name}")

    file_path = os.path.join(cache_folder, best_match)
    with open(file_path, "r", encoding="utf-8") as file:
        cached_data = json.load(file)

    return {
        "message": "Cached file found.",
        "matched_file": best_match,
        "match_score": score,
        "data": cached_data
    }


@app.post("/save_to_db")
def save_to_db(university_name: str):
    """
    Searches for a cached JSON file using fuzzy matching and saves its data to the database.
    """

    if not is_database_connected(DB_CONFIG):
        raise HTTPException(status_code=500, detail="Database connection failed.")

    cache_folder = "cache"
    
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)
    
    json_files = [f for f in os.listdir(cache_folder) if f.endswith(".json")]
    
    if not json_files:
        raise HTTPException(status_code=404, detail="No cached files found.")

    print(f"Available cached files: {json_files}")

    best_match, score = process.extractOne(university_name, json_files)

    print(f"Fuzzy match result: {best_match} (score: {score})") 

    if score < 60: 
        raise HTTPException(status_code=404, detail=f"No close match found for university: {university_name}")

    file_path = os.path.join(cache_folder, best_match)
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=f"Corrupted or invalid JSON file: {best_match}")

    university_name = data.get("university_name", "").strip()
    university_country = data.get("university_country", "").strip()
    number_of_semesters = len(data) - 2 

    if not university_name or not university_country:
        raise HTTPException(status_code=400, detail="Missing university name or country in the cached data.")
    
    write_to_database(data, DB_CONFIG, university_name, university_country, number_of_semesters)

    return {
        "message": "Data saved to database successfully.",
        "matched_file": best_match,
        "match_score": score
    }

CACHE_FOLDER = "cache"

@app.post("/save_all_to_db")
def save_all_to_db():
    """
    Dynamically finds JSON files in the cache folder and saves their contents to the database.
    Process is sped up with Cache files.
    """
    if not is_database_connected(DB_CONFIG):
        raise HTTPException(status_code=500, detail="Database connection failed.")

    json_files = [f for f in os.listdir(CACHE_FOLDER) if f.endswith(".json") and f != "pdf_cache.json"]

    if not json_files:
        raise HTTPException(status_code=404, detail="No valid university data found in cache.")

    for json_file in json_files:
        json_path = os.path.join(CACHE_FOLDER, json_file)

        try:
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            university_name = data.get("university_name", "").replace("_cache", "").strip()
            university_country = data.get("university_country", "")
            number_of_semesters = len([key for key in data.keys() if key not in ["university_name", "university_country"]])

            if not university_name or not university_country:
                print(f"[WARNING] Skipping {json_file}: Missing university name or country.")
                continue  

            write_to_database(data, DB_CONFIG, university_name, university_country, number_of_semesters)
            print(f"[INFO] Saved {university_name} to database.")

        except json.JSONDecodeError:
            print(f"[ERROR] Failed to parse {json_file}. Skipping.")
            continue

    return {"message": "All valid university data saved to the database successfully."}

@app.post("/crawl", summary="Start a web crawl")
def crawl_university(request: CrawlRequest):
    """
    [Warning] A very primitive version of the crawler, for accessing university sites and extracting lesson data automatically.
    - Requires a URL, preferrably on the curriculum page 
    """
    url = request.url
    
    crawler = UniversityCrawler(url)
    course_info = crawler.crawl()
    
    return {"university": crawler.university_name, "courses": course_info.semesters}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
