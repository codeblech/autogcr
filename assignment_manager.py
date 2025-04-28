import nodriver as uc
import pathlib
from typing import Optional, List
from dataclasses import dataclass
from endpoints import missing_endpoint, turned_in_endpoint, not_turned_in_endpoint
from asyncio import TimeoutError
from models import Assignment


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


class AssignmentManager:
    """Manages Google Classroom assignments including downloading, solving, and uploading."""

    def __init__(self, config: GoogleClassroomConfig):
        self.config = config
        self.browser = None
        self.current_tab = None

    @staticmethod
    def _get_drive_download_link(view_link: str) -> str:
        """Convert Google Drive view link to direct download link."""
        file_id = view_link.split("/d/")[1].split("/")[0]
        return (
            f"https://drive.usercontent.google.com/u/0/uc?id={file_id}&export=download"
        )

    async def initialize_browser(self) -> None:
        """Initialize the browser session."""
        self.browser = await uc.start(
            user_data_dir=self.config.user_data_dir,
            browser_executable_path=self.config.browser_executable_path,
        )
        self.current_tab = await self.browser.get(missing_endpoint)

    async def perform_login(self) -> None:
        """Handle Google Classroom login process."""
        try:
            email_input_box = await self.current_tab.select("input[type=email]")
            print("sending email keys")
            await email_input_box.send_keys(self.config.email)
            await self.current_tab.sleep(2 * self.config.sleep_multiplier)
            next_button = await self.current_tab.find("Next", best_match=True)
            print("clicking next button")
            await next_button.mouse_click()

            await self.current_tab.sleep(5 * self.config.sleep_multiplier)

            password_input_box = await self.current_tab.select("input[type=password]")
            print("sending password keys")
            await password_input_box.send_keys(self.config.password)
            await self.current_tab.sleep(2 * self.config.sleep_multiplier)
            next_button = await self.current_tab.find("Next", best_match=True)
            print("clicking next button")
            await next_button.mouse_click()
            await self.current_tab.sleep(5 * self.config.sleep_multiplier)

            if await self.current_tab.find("2-Step Verification", best_match=True):
                print("Please perform 2-Step Verification manually")
        except TimeoutError:
            # User is logged out due to inactivity
            pass

    async def get_assignment_page_urls(self) -> Optional[List[Assignment]]:
        """Fetch and parse assignment URLs and details from the main page."""
        while True:
            try:
                # Wait for the assignment button to appear (this is a proxy for page loaded state)
                assignment_button = await self.current_tab.wait_for(
                    selector="li.MHxtic.QRiHXd",
                    timeout=20 * self.config.sleep_multiplier,
                )
                assignment_buttons = await self.current_tab.query_selector_all(
                    "li.MHxtic.QRiHXd"
                )

                # Find urls for assignment pages
                assignment_page_button_a_tags = [
                    await btn.query_selector("a.nUg0Te") for btn in assignment_buttons
                ]
                assignment_page_urls = [
                    btn.__getattr__("href") for btn in assignment_page_button_a_tags
                ]
                assignment_page_urls = [
                    self.config.base_url + url for url in assignment_page_urls
                ]

                # Find names of assignments
                assignment_names = [
                    await btn.query_selector("p.asQXV.oDLUVd.YVvGBb")
                    for btn in assignment_buttons
                ]
                assignment_names = [name.text for name in assignment_names]

                # Find due dates of assignments
                assignment_due_dates = [
                    await btn.query_selector("p.EhRlC.tGZ0W.pOf0gc")
                    for btn in assignment_buttons
                ]
                assignment_due_dates = [
                    date.text if date is not None else "No due date"
                    for date in assignment_due_dates
                ]

                # Find classroom names
                classroom_names = [
                    await btn.query_selector("p.dDKhVc.YVvGBb")
                    for btn in assignment_buttons
                ]
                classroom_names = [name.text for name in classroom_names]

                return [
                    Assignment(
                        assignment_name=name,
                        due_date_str=due_date,
                        assignment_details_page_url=url,
                        classroom_name=classroom_name,
                    )
                    for name, due_date, url, classroom_name in zip(
                        assignment_names,
                        assignment_due_dates,
                        assignment_page_urls,
                        classroom_names,
                    )
                ]

            except TimeoutError:
                print("Checking if we're logged in")
                try:
                    check1 = await self.current_tab.wait_for(
                        text="To-do", timeout=10 * self.config.sleep_multiplier
                    )
                    check2 = await self.current_tab.wait_for(
                        text="Assigned", timeout=10 * self.config.sleep_multiplier
                    )
                    if check1 and check2:
                        print("We're logged in. No assignments found")
                        return None
                except TimeoutError:
                    print("Logging In")
                    await self.perform_login()
                    continue

    async def get_assignment_file_urls(
        self, assignments: List[Assignment]
    ) -> List[Assignment]:
        """Fetch file URLs and instructions for each assignment."""
        for assignment in assignments:
            assignment_page_tab = await self.browser.get(
                assignment.assignment_details_page_url, new_tab=True
            )

            # Wait for instructions first - this ensures page is loaded
            try:
                instructions_element = await assignment_page_tab.wait_for(
                    selector="div.nGi02b.tLDEHd.j70YMc",
                    timeout=10 * self.config.sleep_multiplier,
                )
                if instructions_element:
                    assignment.assignment_instructions = instructions_element.text

            except TimeoutError:
                print(
                    "No instructions found - timeout waiting for instructions element"
                )
                assignment.assignment_instructions = "No instructions found"
            except Exception as e:
                print(f"Error getting instructions: {e}")
                assignment.assignment_instructions = "Error getting instructions"

            # Then try to get attachments
            try:
                # This assignment_file_button is to check if the page has loaded the attachments.
                assignment_file_button = await assignment_page_tab.wait_for(
                    selector="a.vwNuXe.JkIgWb.QRiHXd.yixX5e",
                    timeout=3 * self.config.sleep_multiplier,
                )

                assignment_file_buttons = []
                all_attachment_divs = await assignment_page_tab.query_selector_all(
                    "div.r0VQac.QRiHXd.Aopndd"
                )
                # check which attachment does not have a cross button. the ones that have a cross button are the ones that are user uploaded.
                for attachment_div in all_attachment_divs:
                    for child in attachment_div.children:
                        if child.tag_name == "div" and child.children:
                            break
                        elif child.tag_name == "a":
                            continue
                        else:
                            assignment_file_buttons.append(
                                await attachment_div.query_selector(
                                    "a.vwNuXe.JkIgWb.QRiHXd.yixX5e"
                                )
                            )
                            break

                assignment.assignment_doc_urls = [
                    btn.__getattr__("href") for btn in assignment_file_buttons
                ]
            except TimeoutError:
                assignment.assignment_doc_urls = []
                print(
                    "No attachment found for assignment with url: ",
                    assignment.assignment_details_page_url,
                )

            await assignment_page_tab.close()

        return assignments

    async def download_assignment_files(self, assignments: List[Assignment]) -> None:
        """Download files for each assignment."""
        for assignment in assignments:
            download_directory_current = (
                self.config.download_directory / assignment.classroom_name
            )
            assignment_doc_local_path = (
                download_directory_current / assignment.assignment_name
            )
            assignment.assignment_doc_local_paths.append(assignment_doc_local_path)

            await self.current_tab.set_download_path(download_directory_current)
            print(assignment_doc_local_path)

            for assignment_file_url in assignment.assignment_doc_urls:
                assignment_file_url = self._get_drive_download_link(assignment_file_url)

                # tab.download_file does not work here.
                # await tab.download_file(get_drive_download_link(assignment_file_url), name)
                # So we rather open a new tab and that automatically downloads the file.
                download_tab = await self.current_tab.get(
                    assignment_file_url, new_tab=True
                )
                # a sleep is needed here to ensure the file is downloaded in the right directory. if we don't wait, the download directory is changed in the next iteration before the file is downloaded.
                await download_tab.sleep(8 * self.config.sleep_multiplier)

    async def upload_assignment_files(self, assignments: List[Assignment]) -> None:
        """Upload completed assignments."""
        for assignment in assignments:
            tab = await self.browser.get(
                assignment.assignment_details_page_url, new_tab=True
            )

            # Check if the assignment cannot be turned in due to late submission
            try:
                mark_as_done_button = await tab.wait_for(
                    selector="button[guidedhelpid='submissionManager_markAsDone']",
                    timeout=10 * self.config.sleep_multiplier,
                )
                if "disabled" in mark_as_done_button.attributes:
                    print(
                        f"Assignment {assignment.assignment_name} for subject {assignment.classroom_name} cannot be turned in due to late submission"
                    )
                    continue
            except TimeoutError:
                print(
                    f"Some attachment is already added but the assignment {assignment.assignment_name} for subject {assignment.classroom_name} is not yet turned in. It may or may not be accepting submissions."
                )

            add_files_button = await tab.wait_for(
                selector="div.VfPpkd-Jh9lGc", timeout=10 * self.config.sleep_multiplier
            )
            await add_files_button.click()

            file_button = await tab.wait_for(
                selector="span.VfPpkd-StrnGf-rymPhb-pZXsl",
                timeout=10 * self.config.sleep_multiplier,
            )
            await file_button.click()
            await tab.sleep(5 * self.config.sleep_multiplier)
            try:
                upload_tab_button = await tab.find("Upload", best_match=True)
                await upload_tab_button.click()
                await tab.sleep(5 * self.config.sleep_multiplier)
            except TimeoutError:
                print("No upload tab button found")

            file_input_parent_div = await tab.find(
                "or drag files here", best_match=True
            )
            file_input_element = await file_input_parent_div.children[0].children[1]
            await file_input_element.send_file(*assignment.assignment_doc_local_paths)
            await tab.sleep(20 * self.config.sleep_multiplier)

            turn_in_button = await tab.wait_for(
                selector="button[guidedhelpid='turnInButton']",
                timeout=10 * self.config.sleep_multiplier,
            )
            if "disabled" in turn_in_button.attributes:
                print(
                    f"Assignment {assignment.assignment_name} for subject {assignment.classroom_name} cannot be turned in due to late submission"
                )
                continue
            print("Turning in assignment")
            await turn_in_button.click()
            buttons_div = await tab.query_selector("div.VfPpkd-T0kwCb")
            turn_in_confirmation_button = buttons_div.children[1]
            print("Clicking confirm button for turnin in")
            await turn_in_confirmation_button.click()
            await tab.sleep(2 * self.config.sleep_multiplier)
