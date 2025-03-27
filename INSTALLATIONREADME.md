# 🧰 Installation Options
You can run SkillCrawl in two ways:

- 🐳 With Docker Compose – fast, portable, and no local Python setup needed.

- ⚙️ Manually with Python – useful for development or testing without containers.

The sections below walk you through both options.

## 🐳 Install & Run with Docker Compose

### 📁 Prerequisites
- Docker & Docker Compose

### ⚙️ Step-by-Step
1. Clone the repo:
```bash
git clone https://github.com/skillab-project/curriculum-skills.git
cd curriculum-skills
```

2. Create a `.env` file:
```env
APP_NAME=skillcrawl-api
DOCKER_REG=
DOCKER_REPO=
DOCKER_TAG=latest

MYSQL_ROOT_PASSWORD=root
MYSQL_USER=skilluser
MYSQL_PASSWORD=skillpass
MYSQL_DATABASE=SkillCrawl
```

3. Run the containers:
```bash
docker-compose --env-file .env up --build
```

4. Open your browser:
```
http://localhost:5002/docs
```
You'll see the Swagger UI with access to all endpoints.

---

## 🧪 Using Without Docker (Manual Mode)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Launch the API:
```bash
uvicorn main:app --reload
```

Visit:
```
http://127.0.0.1:8000/docs
```

---

## 📄 Database Setup

The MySQL schema is automatically loaded from `skillcrawl.sql` when the database container is initialized.

It contains tables for:
- `University`
- `Lessons`
- `Skills`

DB runs on:
```
localhost:5003
```

Use credentials from `.env` to connect.

---

## 🧠 API Endpoints (via Swagger UI)

Key endpoints:
- `/process_pdf`: Upload and process a PDF
- `/search_skill`: Search for courses that teach a skill
- `/filter_skillnames`: Get skill names for a lesson
- `/calculate_skillnames`: Enrich skills using external API
- `/get_top_skills`: Get top N skills per university
- `/get_top_skills_all`: Get top skills across all universities
- `/get_universities_by_skills`: Returns university names and their corresponding courses, for universities that contain every skill in the provided list.
