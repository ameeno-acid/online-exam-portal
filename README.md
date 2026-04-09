# Online Exam Portal

A web-based platform built with Flask that allows administrators to manage exams, subjects, and questions, while enabling students to register, select subjects, and take quizzes securely online.

## Features

- **Authentication System:** Separate login and registration for Administrators and Students.
- **Admin Panel:**
  - Create and manage exams.
  - Manage questions and options.
  - View registered users and result records.
- **Student Panel:**
  - View available subjects/exams (like Physics, Chemistry, Computer Science).
  - Attempt quizzes actively.
  - Immediate score calculation upon submission.

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite3
- **Frontend:** HTML, CSS (Vanilla), Vanilla JavaScript
- **Templating:** Jinja2

## Setup & Running Locally

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-url>
   cd "online exam portal"
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database:**
   ```bash
   python init_db.py
   ```

5. **Seed Initial Admin and Dataset (Optional):**
   ```bash
   python seed_admin.py
   python seed_datasets.py
   ```

6. **Run the Application:**
   ```bash
   python app.py
   ```

7. **Access the Application:**
   Open your browser and navigate to `http://localhost:5000`
