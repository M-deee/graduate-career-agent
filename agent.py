import os
from typing import List, Dict
from huggingface_hub import InferenceClient

class Agent:
    def __init__(self, model: str = "meta-llama/Llama-3.1-8B-Instruct", system_prompt: str = "You are a professional career coach specializing in helping fresh graduates secure jobs, internships, and scholarships. Provide precise, practical guidance. When rewriting CVs or documents, follow best industry standards, use clear and concise language, and focus on measurable achievements. Always maintain accuracy and avoid inventing information."):
        self.model = model
        self.system_prompt = system_prompt
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        # Hardcoded token as per previous user request/fix
        self.api_token = os.getenv("HF_TOKEN")
        
        print(f"HF KEY loaded: {bool(self.api_token)}") # Debug print as requested
        
        if not self.api_token:
            print("Warning: HF_TOKEN is not set.")
            
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
        You will receive a Job Description (JD) and a CV. Rewrite the CV so that it aligns more closely with the JD.

        Your tasks:
        1. Strengthen the summary to match the employer's needs.
        2. Emphasize relevant skills and experience from the CV—do not invent information.
        3. Improve bullet points using action verbs and measurable impact where appropriate.
        4. Remove irrelevant details that do not support the JD.
        5. Maintain clarity, structure, and a professional tone.

        Return:
        1. A complete, compilable LaTeX file using the `moderncv` class.
        2. A short, bullet-point explanation describing what changes were made and why.

        IMPORTANT:
        - Use the `moderncv` class:
          \\documentclass[11pt,a4paper,sans]{{moderncv}}
          \\moderncvstyle{{classic}}
          \\moderncvcolor{{blue}}
        - Wrap the LaTeX code strictly between `[LATEX_START]` and `[LATEX_END]` tags for extraction.
        - Ensure all special characters are properly escaped for LaTeX.

        JOB DESCRIPTION:
        {job_description}

        CV TO TAILOR:
        {cv_text}
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
        You will compare a Job Description (JD) with a candidate's CV.

        Perform the following tasks:
        1. Extract the required skills, tools, responsibilities, and qualifications from the JD.
        2. Perform a gap analysis: identify which important items from the JD are missing in the CV. Do not assume or invent skills.
        3. Rank each missing skill or qualification by importance using High / Medium / Low, based strictly on the JD.

        Return the results in a clear, structured Markdown format.

        JOB DESCRIPTION:
        {jd_text}

        CANDIDATE CV:
        {cv_text}
        """
        return self._simple_chat(prompt)

    def extract_skills(self, cv_text: str) -> str:
        prompt = f"""
        Extract skills from the CV and categorize them into:

        - Technical Skills  
        - Soft Skills  
        - Domain-Specific / Industry Skills  

        Rules:
        - Only extract skills explicitly mentioned in the CV.  
        - Do not infer or add skills that are not present.  
        - Present results in a clean Markdown list.

        CV CONTENT:
        {cv_text}
        """
        return self._simple_chat(prompt)

    def estimate_ats_score(self, cv_text: str) -> str:
        prompt = f"""
        Evaluate this CV for ATS (Applicant Tracking System) compatibility.

        Provide the following:

        1. **Estimated ATS Score (0–100)** based on keyword alignment, structure, readability, and formatting.
        2. **Formatting Issues**  
           Identify problems such as: tables, columns, graphics, excessive styling, unreadable headers, unusual fonts, missing sections, or non-ATS-safe elements.
        3. **Keyword Analysis**  
           Extract important keywords and indicate how well the CV uses them.
        4. **Actionable Recommendations**  
           Suggest practical changes to improve ATS compatibility. Do not add fictional experience.

        Return the results in a structured Markdown format.

        CV CONTENT:
        {cv_text}
        """
        return self._simple_chat(prompt)

    def summarize_jd(self, jd_text: str) -> str:
        prompt = f"""
        Summarize the following Job Posting into a structured and concise format.

        Include:

        - **Key Responsibilities**
        - **Critical Skills and Requirements**
        - **Nice-to-Have Skills**
        - **Company Expectations**
        - **Cultural or Workplace Attributes** (only if explicitly mentioned)

        Do not add information that is not present in the JD.

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
