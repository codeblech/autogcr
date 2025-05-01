from pathlib import Path
from models import Assignment
from abc import ABC, abstractmethod


class Solver(ABC):
    """Class to handle solving assignments."""

    @abstractmethod
    def solve_assignment(self, assignment: Assignment) -> Path:
        """Abstract method to solve an assignment. It takes an assignment object and returns a path to the generated solution docx file.

        Args:
            assignment (Assignment): Assignment object containing instructions and files

        Returns:
            Path: Path to the generated solution file (PDF, DOCX, etc.)
        """
        pass
