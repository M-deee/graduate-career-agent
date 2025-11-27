# Graduate Career Agent

An AI-powered career coach designed to help fresh graduates secure jobs, internships, and scholarships.

## Features
- **Chat Coach**: Interactive chat with an AI career expert.
- **CV Tailoring**: Upload your CV and a job description to get a tailored version.
- **Job Analysis**: Analyze job descriptions to understand requirements and gaps.
- **Profile Insights**: Extract skills and estimate ATS scores.

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
