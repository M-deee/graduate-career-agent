import os

# Configuration settings
GENERAL_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
CODE_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
# API_URL is no longer single-source, used inside agent logic

# System Prompt
SYSTEM_PROMPT = """You are a professional career coach specializing in helping fresh graduates secure jobs, internships, and scholarships. Provide precise, practical guidance. When rewriting CVs or documents, follow best industry standards, use clear and concise language, and focus on measurable achievements. Always maintain accuracy and avoid inventing information."""

# Secret Keys
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey") # Change in production
