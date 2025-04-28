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
        await tab.sleep(10 * SLEEP_MULTIPLIER)

        mark_as_done_button = await tab.wait_for(
            selector="button[guidedhelpid='turnInButton']",
            timeout=10 * SLEEP_MULTIPLIER,
        )
        while mark_as_done_button.disabled:
            await tab.sleep(1 * SLEEP_MULTIPLIER)
        await mark_as_done_button.click()
