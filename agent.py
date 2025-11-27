import os
from typing import List, Dict
from huggingface_hub import InferenceClient

class Agent:
    def __init__(self, model: str = "meta-llama/Llama-4-Scout-17B-16E-Instruct", system_prompt: str = "You are an expert career coach for fresh graduates. Your goal is to help them secure jobs, internships, and scholarships by tailoring their CVs and providing actionable advice."):
        self.model = model
        self.system_prompt = system_prompt
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        # Hardcoded token as per previous user request/fix
        self.api_token = os.getenv("HUGGINGFACEHUB_API_KEY")
        
        print(f"HF KEY loaded: {bool(self.api_token)}") # Debug print as requested
        
        if not self.api_token:
            print("Warning: HUGGINGFACEHUB_API_KEY is not set.")
            
        self.client = InferenceClient(model=self.model, token=self.api_token)

    def chat(self, user_input: str) -> str:
        """
        Sends a message to the Hugging Face Inference API using InferenceClient.
        """
        if not self.api_token:
            return "Error: HF_TOKEN is not set. Please set it to use the agent."

        self.history.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat_completion(
                messages=self.history,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9
            )
            
            assistant_message = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
        except Exception as e:
            print(f"Error communicating with Hugging Face API: {e}")
            return f"Error: Unable to connect to the AI model. Details: {e}"

    def tailor_cv(self, cv_text: str, job_description: str) -> str:
        """
        Analyzes the CV and Job Description to provide a tailored version.
        """
        if not self.api_token:
            return "Error: HF_TOKEN is not set."

        prompt = f"""
        I have a CV and a Job Description (JD). Please rewrite the CV to better match the JD.
        Highlight relevant skills, adjust the summary, and optimize bullet points.
        
        JOB DESCRIPTION:
        {job_description}
        
        CURRENT CV:
        {cv_text}
        
        Please provide the tailored CV in Markdown format, followed by a brief explanation of changes.
        """
        
        # We don't add this to the main chat history to keep the context clean, 
        # or we can if we want the user to be able to ask follow-ups.
        # Let's add it to history so they can ask "Why did you change X?"
        
        self.history.append({"role": "user", "content": f"Please tailor my CV for this job:\n\n{job_description}\n\nMy CV content:\n{cv_text}"})
        
        try:
            response = self.client.chat_completion(
                messages=self.history,
                max_tokens=1024, # Need more tokens for CV generation
                temperature=0.7,
                top_p=0.9
            )
            
            assistant_message = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
        except Exception as e:
            print(f"Error tailoring CV: {e}")
            return f"Error: Unable to tailor CV. Details: {e}"

    def clear_history(self):
        self.history = [{"role": "system", "content": self.system_prompt}]

    def analyze_jd(self, jd_text: str, cv_text: str) -> str:
        prompt = f"""
        Analyze the following Job Description (JD) and Candidate CV.
        Provide:
        1. List of required skills, tools, and qualifications from the JD.
        2. Gap analysis: What is missing in the CV compared to the JD?
        3. Priority scoring: Rank the missing skills by importance (High/Medium/Low).

        JOB DESCRIPTION:
        {jd_text}

        CANDIDATE CV:
        {cv_text}
        """
        return self._simple_chat(prompt)

    def extract_skills(self, cv_text: str) -> str:
        prompt = f"""
        Extract all skills from the following CV and categorize them into:
        - Technical Skills
        - Soft Skills
        - Domain-Specific Skills
        
        CV CONTENT:
        {cv_text}
        """
        return self._simple_chat(prompt)

    def estimate_ats_score(self, cv_text: str) -> str:
        prompt = f"""
        Analyze the following CV for ATS (Applicant Tracking System) compatibility.
        Provide:
        1. Estimated ATS Score (0-100).
        2. Formatting issues (e.g., tables, columns, graphics).
        3. Keyword density analysis.
        4. Suggestions for improvement.

        CV CONTENT:
        {cv_text}
        """
        return self._simple_chat(prompt)

    def summarize_jd(self, jd_text: str) -> str:
        prompt = f"""
        Summarize the following Job Posting into a structured format:
        - Key Responsibilities
        - Critical Skills
        - Nice-to-have Requirements
        - Company Expectations
        - Cultural Attributes

        JOB POSTING:
        {jd_text}
        """
        return self._simple_chat(prompt)

    def _simple_chat(self, prompt: str) -> str:
        """Helper for single-turn requests without history."""
        if not self.api_token:
            return "Error: HF_TOKEN is not set."
            
        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.7,
                top_p=0.9
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in AI request: {e}")
            return f"Error: {e}"
