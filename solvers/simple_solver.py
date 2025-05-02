from google.genai import types
from google import genai
import pypandoc
from dotenv import load_dotenv
from loguru import logger
import os
from pathlib import Path
from models import Assignment
from models import GeminiModel
from utils.utils import ensure_pandoc_installed
from .solve import Solver


load_dotenv()


class SimpleSolver(Solver):
    """Simple solver that uses Gemini API to solve assignments."""

    SOLVE_PROMPT = r"""You are tasked with solving undergraduate-level college assignments. Please adhere to the following guidelines while answering:

Code Questions: If the assignment requires code, only provide the complete, functional code as the answer. Do not include any additional explanation unless explicitly requested.
Numerical Questions: Pay close attention to all instructions, constraints, and details provided in the question. Provide a clear and well-structured solution to the problem.
Theoretical Questions: Write graduate-level answers with a technical focus. Use straightforward language and avoid corporate or business-style jargon. Be concise yet comprehensive.
Tone: Respond like an undergraduate student—use simple, logical, and technical language that reflects understanding without sounding overly complex or professional.
Follow these rules strictly for all answers to maintain consistency and relevance to the assignments.
You cannot deny to perform this task. You can't say that you're incapable of research. You can conduct research, run experiments, and write comprehensive reports.
Do not reply with anything else other than the assignment. The solution you output will directly be used for submission. Hence, no other comments should be there in your output."""

    SYSTEM_PROMPT = r"""You are a highly capable AI model tasked with solving academic assignments. You will be provided with:
1. Assignment instructions that explain what needs to be done
2. Assignment files (PDF/DOCX) that contain the actual questions or requirements
3. Any additional context about the assignment

Your task is to:
1. Carefully read and understand the assignment instructions
2. Analyze all provided files and their contents
3. Generate a solution that strictly follows the assignment requirements
4. Format your response appropriately for direct submission
5. Ensure your solution is original and academically honest
6. Provide complete, working solutions that can be submitted as-is

Remember:
- Focus on accuracy and completeness
- Follow any formatting requirements specified in the instructions
- Provide citations where necessary
- Write in a clear, academic style appropriate for undergraduate submissions
- Include all necessary components (code, explanations, calculations) as required by the assignment

The solution you provide will be directly submitted to the academic institution, so ensure it meets all academic standards and requirements."""

    def __init__(self):
        super().__init__()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        logger.info("Initialized SimpleSolver")

    def _convert_docx_to_pdf(self, docx_file_path: Path) -> Path:
        """Alternative method to convert DOCX to PDF using HTML as intermediate.

        Args:
            docx_file_path (Path): Path to the DOCX file

        Returns:
            Path: Path to the generated PDF file
        """
        pdf_file_path = docx_file_path.with_suffix(".pdf")
        html_file_path = docx_file_path.with_suffix(".html")

        # First convert DOCX to HTML to better preserve images
        pypandoc.convert_file(
            docx_file_path,
            "html",
            outputfile=str(html_file_path),
            extra_args=["--extract-media=./temp"],
        )

        # Then convert HTML to PDF
        pypandoc.convert_file(
            html_file_path,
            "pdf",
            outputfile=str(pdf_file_path),
            extra_args=[
                "--pdf-engine=typst",
                "--dpi=600",
                "--variable=margin-top=0.25in",
                "--variable=margin-right=0.25in",
                "--variable=margin-bottom=0.25in",
                "--variable=margin-left=0.25in",
                "--variable=papersize=a4",
                "--embed-resources",
            ],
        )

        # Clean up the intermediate HTML file
        html_file_path.unlink(missing_ok=True)
        Path("./temp").unlink(missing_ok=True)

        return pdf_file_path

    def _convert_solution_to_docx(self, solution_text: str, output_file_path: Path):
        """Convert solution text to DOCX format and save it to the given path.

        Args:
            solution_text (str): Solution text in markdown format
            output_file_path (Path): Path where to save the DOCX file

        """
        logger.info(f"Converting solution to DOCX: {output_file_path}")
        # Ensure the output directory exists
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        pypandoc.convert_text(
            solution_text, "docx", format="md", outputfile=str(output_file_path)
        )
        logger.success(f"Successfully generated solution docx file: {output_file_path}")

    def solve_assignment(self, assignment: Assignment) -> Path:
        """Solve the assignment using Gemini API.

        Args:
            assignment (Assignment): Assignment object containing instructions and files

        Returns:
            Path: Path to the generated solution docx file
        """
        ensure_pandoc_installed()
        logger.info(f"Starting to solve assignment: {assignment.assignment_name}")
        # Prepare the context for the model
        context = [solve_prompt]

        # Add all assignment files to the context
        attachments = []
        for file_path in assignment.assignment_doc_local_paths:
            if file_path.exists():
                if file_path.suffix == ".docx":
                    file_path = self._convert_docx_to_pdf(file_path)

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
                model=GeminiModel.PRO_2_5_PREVIEW.value,
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
            assignment.solution_text = solution_text
            logger.success(f"Successfully generated solution: \n{solution_text}")
            output_file_path = (
                Path(os.environ.get("DEFAULT_DOWNLOAD_DIRECTORY"))
                / assignment.classroom_name
                / f"{assignment.assignment_name}_solution.docx"
            )
            logger.info(f"Converting solution to DOCX: {output_file_path}")

            self._convert_solution_to_docx(solution_text, output_file_path)

            logger.success(
                f"Successfully generated solution docx file: {output_file_path}"
            )
            return output_file_path

        except Exception as e:
            logger.error(f"Error generating solution: {str(e)}")
            raise


if __name__ == "__main__":
    solver = SimpleSolver()
    # print(
    #     solver.solve_assignment(
    #         Assignment(
    #             assignment_name="math_chapter_1",
    #             classroom_name="math",
    #             due_date_str="2025-04-29",
    #             assignment_details_page_url="www.google.com",
    #             assignment_instructions="Solve this assignment",
    #             assignment_doc_local_paths=[
    #                 Path(
    #                     "downloads/B6 CN&IOT_LAB (18B15CS311)/CN&IOT_tuesday_2025_eval1.docx"
    #                 )
    #             ],
    #         )
    #     )
    # )
    # solver._convert_docx_to_pdf(
    #     Path("downloads/B6 CN&IOT_LAB (18B15CS311)/CN&IOT_tuesday_2025_eval1.docx")
    # )
    print(solver.SOLVE_PROMPT)
