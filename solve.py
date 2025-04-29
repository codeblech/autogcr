# make the downloading, solving, and uploading code asynchronous
from google.genai import types
from google import genai
from dotenv import load_dotenv
import os
from pathlib import Path
from typing import List
from models import Assignment
from prompts import solve_prompt, system_prompt
from models import GeminiModel

load_dotenv()


class Solver:
    """Class to handle solving assignments using Gemini API."""

    def __init__(self):
        """Initialize the Solver with Gemini configuration."""
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def solve_assignment(self, assignment: Assignment) -> str:
        """Solve a single assignment using the Gemini model.

        Args:
            assignment (Assignment): Assignment object containing instructions and files

        Returns:
            str: Generated solution text
        """
        # Prepare the context for the model
        context = [solve_prompt]

        # Add all assignment files to the context
        attachments = []
        for file_path in assignment.assignment_doc_local_paths:
            if file_path.exists():
                attachments.append(
                    types.Part.from_bytes(
                        data=file_path.read_bytes(), mime_type="application/pdf"
                    )
                )

        context.append(
            f"Assignment Instructions:\n{assignment.assignment_instructions}"
        )
        context.extend(attachments)

        # Generate the solution
        response = self.client.models.generate_content(
            model=GeminiModel.FLASH_2_5_PREVIEW.value,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.9,
                max_output_tokens=100_000,
            ),
        )
        return response.text

    def solve_assignments(self, assignments: List[Assignment]) -> List[Assignment]:
        """Solve multiple assignments.

        Args:
            assignments (List[Assignment]): List of assignments to solve

        Returns:
            List[Assignment]: List of assignments with solutions added
        """
        for assignment in assignments:
            try:
                solution = self.solve_assignment(assignment)
                assignment.solution_text = solution
            except Exception as e:
                print(f"Error solving assignment {assignment.assignment_name}: {e}")
                assignment.solution_text = None

        return assignments


if __name__ == "__main__":
    solver = Solver()
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
