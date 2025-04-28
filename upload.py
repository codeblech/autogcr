import nodriver as uc
import pathlib
import os
from endpoints import missing_endpoint, turned_in_endpoint, not_turned_in_endpoint
from dotenv import load_dotenv
from asyncio import TimeoutError
from models import Assignment

load_dotenv()

SLEEP_MULTIPLIER = 0.6

BASE_URL = "https://classroom.google.com"


async def upload_assignment_files(browser, assignments: list[Assignment]):
    for assignment in assignments:
        tab = await browser.get(assignment.assignment_details_page_url, new_tab=True)

        # Check if the assignment cannot be turned in due to late submission
        # Mark as done button is not disabled only if the assignment can be turned in and no attachments are added
        # If some attachments are already added and late submission is not allowed, then the turn in button is disabled
        try:
            mark_as_done_button = await tab.wait_for(
                selector="button[guidedhelpid='submissionManager_markAsDone']",
                timeout=10 * SLEEP_MULTIPLIER,
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
            selector="div.VfPpkd-Jh9lGc", timeout=10 * SLEEP_MULTIPLIER
        )
        await add_files_button.click()

        file_button = await tab.wait_for(
            selector="span.VfPpkd-StrnGf-rymPhb-pZXsl", timeout=10 * SLEEP_MULTIPLIER
        )
        await file_button.click()
        await tab.sleep(5 * SLEEP_MULTIPLIER)
        try:
            upload_tab_button = await tab.find("Upload", best_match=True)
            await upload_tab_button.click()
            await tab.sleep(5 * SLEEP_MULTIPLIER)
        except TimeoutError:
            print("No upload tab button found")

        file_input_parent_div = await tab.find("or drag files here", best_match=True)
        file_input_element = await file_input_parent_div.children[0].children[1]
        await file_input_element.send_file(*assignment.assignment_doc_local_paths)
        await tab.sleep(20 * SLEEP_MULTIPLIER)

        turn_in_button = await tab.wait_for(
            selector="button[guidedhelpid='turnInButton']",
            timeout=10 * SLEEP_MULTIPLIER,
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
        await tab.sleep(2 * SLEEP_MULTIPLIER)
