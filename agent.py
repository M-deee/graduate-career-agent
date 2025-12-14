import os
from typing import List, Dict
from huggingface_hub import InferenceClient
import config

class Agent:
    def __init__(self, system_prompt: str = config.SYSTEM_PROMPT):
        self.system_prompt = system_prompt
        # Legacy history format for chat
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        
        self.api_token = os.getenv("HF_TOKEN")
        print(f"HF KEY loaded: {bool(self.api_token)}")
        
        if not self.api_token:
            print("Warning: HF_TOKEN is not set.")
            
        # Initialize two clients
        self.general_client = InferenceClient(model=config.GENERAL_MODEL, token=self.api_token)
        self.code_client = InferenceClient(model=config.CODE_MODEL, token=self.api_token)

    def chat(self, user_input: str, history: List[Dict[str, str]] = None) -> str:
        """
        Sends a message to the Hugging Face Inference API using InferenceClient.
        If history is provided, it uses that context instead of the internal self.history details.
        """
        if not self.api_token:
            return "Error: HF_TOKEN is not set. Please set it to use the agent."

        # Use provided history or fallback to internal history (legacy support)
        messages = history if history is not None else self.history

        # Appending new message is handled by caller (main.py) when using DB history,
        # but if we are using internal history, we must append it.
        if history is None:
            self.history.append({"role": "user", "content": user_input})
        else:
            # When using DB history, the caller constructs the list, but we need to ensure
            # the current user input is in the messages sent to the model.
            messages.append({"role": "user", "content": user_input})

        try:
            # Use General Model
            response = self.general_client.chat_completion(
                messages=messages,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9
            )
            
            assistant_message = response.choices[0].message.content
            
            if history is None:
                self.history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
        except Exception as e:
            print(f"Error communicating with Hugging Face API: {e}")
            return f"Error: Unable to connect to the AI model. Details: {e}"

    def tailor_cv(self, cv_text: str, job_description: str) -> str:
        """
        Analyzes the CV and Job Description to provide a tailored version.
        USES CODE MODEL.
        """
        if not self.api_token:
            return "Error: HF_TOKEN is not set."

        prompt = f"""
        You are a CV Tailoring Expert. Your task is to extract the user's CV content and rewrite it to be perfectly tailored to the Job Description (JD).

        **INSTRUCTION**: Provide a clean, well-structured Markdown version of the CV.

        **Structure of your response:**
        1. **Analysis**: A brief bulleted list of 3-4 key changes you made and why.
        2. **Tailored CV**: The COMPLETE Markdown CV wrapped strictly in `[CV_START]` and `[CV_END]`.

        **Output Format:**
        Analysis:
        - ...
        - ...

        [CV_START]
        # Name
        ## Contact Info

        ## Profile
        ...

        ## Experience
        ...
        [CV_END]

        **Rules:**
        - NO conversational text.
        - The CV must be in standard Markdown (headers, bullet points).
        - Focus on professional formatting.

        JOB DESCRIPTION:
        {job_description}

        CV CONTENT:
        {cv_text}
        """
        
        # Note: We don't append to self.history for this specific task to be cleaner, 
        # or we could. But since we use different models, sharing history is tricky.
        # We'll treat this as stateless for the agent's memory or just not save it.
        # But previous implementation did append. Let's create a temp message list.
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            # Use Code Model
            response = self.code_client.chat_completion(
                messages=messages,
                max_tokens=2048, # More tokens for CV code
                temperature=0.2, # Lower temp for code precision
                top_p=0.9
            )
            
            assistant_message = response.choices[0].message.content
            # self.history.append({"role": "assistant", "content": assistant_message}) # Skip history for specialized task
            
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
        """Helper for single-turn requests without history. Uses General Model."""
        if not self.api_token:
            return "Error: HF_TOKEN is not set."
            
        try:
            # Use General Model
            response = self.general_client.chat_completion(
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
