from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4, UUID
from enum import Enum
import pathlib


@dataclass
class Assignment:
    due_date_str: str  # date on the website is not parsable due to varying formats
    assignment_details_page_url: str
    uuid: UUID = field(default_factory=uuid4)
    assignment_name: str = None
    classroom_name: str = None
    faculty_name: str = None
    assignment_instructions: str = None
    assignment_doc_urls: list[str] = field(default_factory=list)
    assignment_doc_names: list[str] = field(default_factory=list)
    assignment_doc_local_paths: list[Path] = field(default_factory=list)
    solution_text: str = None
    solution_doc_local_path: Path = None
    no_longer_accepting_submissions: bool = False


@dataclass
class GoogleClassroomConfig:
    """Configuration class for Google Classroom automation."""

    email: str
    password: str
    download_directory: pathlib.Path
    browser_executable_path: str = "/usr/bin/google-chrome"
    user_data_dir: str = "./user"
    sleep_multiplier: float = 0.6
    base_url: str = "https://classroom.google.com"


class GeminiModel(Enum):
    """If new models are added, add them to the enum."""

    FLASH_2_5_PREVIEW = "gemini-2.5-flash-preview-04-17"
    PRO_2_5_PREVIEW = "gemini-2.5-pro-exp-03-25"
    FLASH_2_0 = "gemini-2.0-flash"
    FLASH_LITE_2_0 = "gemini-2.0-flash-lite"
