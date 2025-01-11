# make the downloading, solving, and uploading code asynchronous
import google.generativeai as genai
from google.generativeai import GenerativeModel
from dotenv import load_dotenv
import os
import base64
from pathlib import Path
from prompts import solve_prompt
load_dotenv()

def create_llm():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model: GenerativeModel = genai.GenerativeModel("gemini-1.5-flash")
    return model


def get_llm_solution(model: GenerativeModel, assginment_path: Path) -> str:
    """solves the assignment in the given path and returns the text output of the llm.

    Args:
        model (GenerativeModel): Gemini LLM

    Returns:
        str: output ofthe LLM
    """

    with open(assginment_path, "rb") as doc_file:
        doc_data = base64.standard_b64encode(doc_file.read()).decode("utf-8")
        response = model.generate_content(
            [{"mime_type": "application/pdf", "data": doc_data}, solve_prompt]
        )

        return response.text


if __name__ == "__main__":
    model = create_llm()
    print(get_llm_solution(model, "w2.pdf"))
