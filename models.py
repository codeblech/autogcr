from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4, UUID

@dataclass
class Assignment:
    due_date_str: str # date on the website is not parsable due to varying formats
    assignment_details_page_url: str
    uuid: UUID = field(default_factory=uuid4)
    assignment_name: str = None
    classroom_name: str = None
    faculty_name: str = None
    assignment_instructions: str = None
    assignment_doc_urls: list[str] = field(default_factory=list)
    assignment_doc_local_paths: list[Path] = field(default_factory=list)
    solution_text: str = None
    solution_doc_local_path: Path = None
    no_longer_accepting_submissions: bool = False
