# 🧠 SKILLCRAWL

**SkillCrawl** is a tool that helps you search into university curricula and extract important skills that students are expected to learn — all from PDF files. It uses the official **ESCO** skill framework and leverages the `esco-skill-extractor` to identify real-world competencies and link them back to course content.

You can run it interactively in your terminal, use its web API with Swagger UI, or even connect it to a MySQL database. Whether you're doing academic research, analyzing skill trends, or building a course recommender, SkillCrawl saves you time by automating the skill detection.

> ⚙️ **Coming soon**: An **automated web crawler** is currently under development to let you scan entire university websites for curriculum pages — no PDFs required! It’s still experimental but already crawling basic lesson data from real websites.

---

## 🚀 What Does SkillCrawl Actually Do?

SkillCrawl is like a skill-focused academic detective. Here's how it works:

- 📥 Takes in PDF files of university curricula.
- 🔍 Reads and processes the text using PDF-aware techniques.
- 🗂️ Splits course content into **semesters** and **individual lessons**, even if the formatting is inconsistent.
- 🧩 For each lesson, it extracts related **ESCO skills** (the EU’s official database of competencies and qualifications).
- 🧠 Lets you **search by skill** (e.g., "data analysis") and find which courses teach it — or browse what skills each course covers.
- 🛢️ Supports **saving everything to MySQL**, so you can build dashboards or analyze data later.
- 🔁 Keeps a local **cache** of all processed files for instant reuse.
- 💬 Comes with both a full **FastAPI/Swagger web interface** and a **terminal menu**.
- 🌐 (Experimental) A **crawler module** is being built to auto-visit university websites and scrape curriculum content without any manual download.

---

## 🛠️ Usage

### ➤ FastAPI Mode (Swagger UI)
Run the API with:

```bash
uvicorn main:app --reload
```

Then open: [http://127.0.0.1:8000/docs#/](http://127.0.0.1:8000/docs#/)

Here you can:
- Process PDFs
- Search for skills (by name or URL) or courses -in a specific university or globally-
- Get top N skills per university or globally
- Fetch full lesson/skill breakdowns
- Save data to DB with a click

Ensure:
- Your database (`SkillCrawl`) is set up using `skillcrawl.sql`.
- XAMPP/MySQL is running.

---

## 🧪 Example Output

SkillCrawl prints matching lessons and their associated ESCO skills:

```
Semester 1:
  Introduction to Programming
    Skill: problem solving
    Skill: code debugging
```

Or search in reverse:

```
Skill: machine learning

Matched Course: AI and Ethics (Score: 84)
```

---

## 🏗️ Project Structure

| File/Folder         | Purpose |
|---------------------|---------|
| `main.py`           | FastAPI app |
| `skillcrawl.py`     | Entry point with menu & CLI control |
| `pdf_utils.py`      | PDF parsing, semester/lesson splitting |
| `database.py`       | Handles writing to MySQL |
| `skills.py`         | Skill extraction, DB lookup, and fuzzy matching |
| `output.py`         | Visual output helpers (ASCII, color, lines) |
| `config.py`         | DB and cache config |
| `helpers.py`        | Utility functions (caching, validation, detection) |
| `menu.py`           | Terminal ASCII Interface |
| `skillcrawl.sql`    | SQL schema to set up the database |
| `requirements.txt`  | List of required Python libraries |
| `cache/`            | Stores processed data by university |
| `tests/`            | Stores the available test cases you can run |
| `README.md`         | You're reading it! |

---

## 📚 Use Cases

- Curriculum Analysis & Benchmarking
- Educational Skill Mapping
- Automated Course Tagging
- Career Pathway Recommendations
- Academic Skill Graph Construction

---

## 🧩 Requirements

Install all dependencies:

```bash
pip install -r requirements.txt
```

Recommended: **Python 3.10**  
Avoid Python 3.11+ due to compatibility with `esco-skill-extractor`.

---

## 💾 Database Setup

Initialize the database using:

```bash
mysql -u root -p < skillcrawl.sql
```

Make sure to configure the connection details in `skillcrawl.py` and `skills.py` under `db_config`.

---

## 🔄 Caching

Processed results are cached per university PDF in:
- `cache/pdf_cache.json`
- `university_cache.json`

*Where university is replaced by a respective university name that the cache represents.*

You can delete these files to force re-processing.

-----

![skillab](https://th.bing.com/th/id/OIP.XWHdKPsdkbsZ4HvK6B5jWwHaCH?rs=1&pid=ImgDetMain) 


