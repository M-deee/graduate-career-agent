# Graduate Career Agent

An AI-powered career coach designed to help fresh graduates secure jobs, internships, and scholarships.

## Features

### 1. Chat Coach
- **Interactive Career Advice**: Engage in a natural conversation with an AI career expert.
- **Personalized Guidance**: Get advice on job search strategies, interview preparation, and career planning.
- **Context-Aware**: The agent maintains conversation history to provide relevant follow-up responses.

### 2. CV Tailoring
- **Job-Specific Optimization**: Upload your CV (PDF) and a job description to receive a rewritten version of your CV.
- **Skill Highlighting**: The agent identifies and emphasizes skills relevant to the specific job opportunity.
- **Markdown Output**: The tailored CV is provided in a clean Markdown format, ready for editing.

### 3. Job Analysis
- **Gap Analysis**: Compare your CV against a job description to identify missing skills or qualifications.
- **Priority Scoring**: Receive a ranked list of missing skills (High/Medium/Low importance) to focus your upskilling efforts.
- **Requirement Extraction**: Automatically extract key requirements, tools, and qualifications from job postings.

### 4. Profile Insights
- **Skill Extraction**: Automatically extract and categorize skills from your CV into Technical, Soft, and Domain-Specific categories.
- **ATS Score Estimation**: Get an estimated ATS (Applicant Tracking System) compatibility score (0-100).
- **Improvement Suggestions**: Receive actionable feedback on formatting, keyword density, and structure to improve your ATS ranking.

### 5. Job Description Summarization
- **Structured Summary**: Convert lengthy job descriptions into concise summaries.
- **Key Information**: Quickly identify Key Responsibilities, Critical Skills, Company Expectations, and Cultural Attributes.

## Setup

1.  **Clone the repository**
    ```bash
    git clone <your-repo-url>
    cd graduate-career-agent
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**
    Create a `.env` file based on `.env.example` and add your Hugging Face token:
    ```
    HF_TOKEN=your_token_here
    ```

4.  **Run Locally**
    ```bash
    python main.py
    ```
    Visit `http://localhost:8000` in your browser.

## Deployment
This project includes a `Dockerfile` and `Procfile` for easy deployment on platforms like Render or Heroku.

## Technologies
- Python (FastAPI)
- HTML/CSS/JS (Vanilla)
- Hugging Face Inference API (Meta Llama 3)
