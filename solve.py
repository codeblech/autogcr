# make the downloading, solving, and uploading code asynchronous
from google.genai import types
from google import genai
from dotenv import load_dotenv
import os
import base64
from pathlib import Path
from typing import List
from models import Assignment
from prompts import solve_prompt, system_prompt

load_dotenv()


class Solver:
    """Class to handle solving assignments using Gemini API."""

    def __init__(self):
        """Initialize the Solver with Gemini configuration."""
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def _encode_file(self, file_path: Path) -> dict:
        """Encode a file to base64 and return it in the format expected by Gemini.

        Args:
            file_path (Path): Path to the file to encode

        Returns:
            dict: Dictionary containing mime_type and base64 encoded data
        """
        with open(file_path, "rb") as file:
            data = base64.standard_b64encode(file.read()).decode("utf-8")
            # Determine mime type based on file extension
            mime_type = (
                "application/pdf"
                if file_path.suffix == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            return {"mime_type": mime_type, "data": data}

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
            model="gemini-2.0-flash-lite",
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.9,
                max_output_tokens=2048,
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
    model = solver.model
    print(
        solver.solve_assignment(
            Assignment(
                name="w2", instructions="Solve this assignment", doc_paths=["w2.pdf"]
            )
        )
    )
