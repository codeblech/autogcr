# make the downloading, solving, and uploading code asynchronous
from google.genai import types
from google import genai
from dotenv import load_dotenv
from loguru import logger
import os
from pathlib import Path
from typing import List
from models import Assignment
from prompts import solve_prompt, system_prompt
from models import GeminiModel
from abc import ABC, abstractmethod
from utils.markdown2docx import convert_markdown_to_docx

load_dotenv()


class Solver(ABC):
    """Class to handle solving assignments using Gemini API."""

    def __init__(self):
        """Initialize the Solver with Gemini configuration."""
        logger.info("Initializing Solver with Gemini API")
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    @abstractmethod
    def solve_assignment(self, assignment: Assignment) -> Path:
        """Abstract method to solve an assignment. It takes an assignment object and returns a path to the generated solution docx file.

        Args:
            assignment (Assignment): Assignment object containing instructions and files

        Returns:
            Path: Path to the generated solution docx file
        """
        pass


class SimpleSolver(Solver):
    """Simple solver that uses Gemini API to solve assignments."""

    def __init__(self):
        super().__init__()
        logger.info("Initialized SimpleSolver")

    def solve_assignment(self, assignment: Assignment) -> Path:
        logger.info(f"Starting to solve assignment: {assignment.assignment_name}")
        # Prepare the context for the model
        context = [solve_prompt]

        # Add all assignment files to the context
        attachments = []
        for file_path in assignment.assignment_doc_local_paths:
            if file_path.exists() and file_path.suffix == ".pdf":
                logger.debug(f"Adding file to context: {file_path}")
                attachments.append(
                    types.Part.from_bytes(
                        data=file_path.read_bytes(), mime_type="application/pdf"
                    )
                )
            else:
                logger.warning(f"File not found: {file_path}")

        context.append(
            f"Assignment Instructions:\n{assignment.assignment_instructions}"
        )
        context.extend(attachments)

        # Generate the solution
        logger.info("Generating solution using Gemini API")
        try:
            response = self.client.models.generate_content(
                model=GeminiModel.FLASH_LITE_2_0.value,
                contents=context,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.9,
                    max_output_tokens=100_000,
                ),
            )
            if response.text is None:
                logger.error("No response from Gemini API")
                raise Exception("No response from Gemini API")
            solution_text = response.text
            logger.success(f"Successfully generated solution: \n{solution_text}")
            output_file_path = (
                Path(os.environ.get("DEFAULT_DOWNLOAD_DIRECTORY"))
                / assignment.classroom_name
                / f"{assignment.assignment_name}_solution.docx"
            )
            logger.info(f"Converting solution to DOCX: {output_file_path}")
            solution_docx_path = convert_markdown_to_docx(
                solution_text, output_file_path=output_file_path, input_is_file=False
            )
            logger.success(f"Successfully generated solution: {solution_docx_path}")
            return solution_docx_path
        except Exception as e:
            logger.error(f"Error generating solution: {str(e)}")
            raise


if __name__ == "__main__":
    solver = SimpleSolver()
    print(
        solver.solve_assignment(
            Assignment(
                assignment_name="w2",
                due_date_str="2025-04-29",
                assignment_details_page_url="www.google.com",
                assignment_instructions="Solve this assignment",
                assignment_doc_local_paths=[Path("w2.pdf")],
            )
        )
    )
