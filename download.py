import nodriver as uc
import pathlib
import os
from endpoints import missing_endpoint, turned_in_endpoint, not_turned_in_endpoint
from dotenv import load_dotenv
from asyncio import TimeoutError
from models import Assignment
from upload import upload_assignment_files

load_dotenv()

SLEEP_MULTIPLIER = 0.6

BASE_URL = "https://classroom.google.com"
email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")
download_directory = pathlib.Path(os.environ.get("DEFAULT_DOWNLOAD_DIRECTORY"))


def get_drive_download_link(view_link):
    file_id = view_link.split("/d/")[1].split("/")[0]
    direct_link = (
        f"https://drive.usercontent.google.com/u/0/uc?id={file_id}&export=download"
    )
    return direct_link


async def perform_login(tab):
    try:
        email_input_box = await tab.select("input[type=email]")
        print("sending email keys")
        await email_input_box.send_keys(email)
        await tab.sleep(2 * SLEEP_MULTIPLIER)
        next_button = await tab.find("Next", best_match=True)
        print("clicking next button")
        await next_button.mouse_click()

        await tab.sleep(5 * SLEEP_MULTIPLIER)

        password_input_box = await tab.select("input[type=password]")
        print("sending password keys")
        await password_input_box.send_keys(password)
        await tab.sleep(2 * SLEEP_MULTIPLIER)
        next_button = await tab.find("Next", best_match=True)
        print("clicking next button")
        await next_button.mouse_click()
        await tab.sleep(5 * SLEEP_MULTIPLIER)

        if await tab.find("2-Step Verification", best_match=True):
            print("Please perform 2-Step Verification manually")
            # loading spinner
    except TimeoutError:
        # this is the case where the user is logged out probably due to inactivity. there appears a 'use another account' button.
        pass


async def get_assignment_page_urls(tab):
    while True:
        try:
            # Wait for the assignment button to appear (this is a proxy for page loaded state)
            assignment_button = await tab.wait_for(
                selector="li.MHxtic.QRiHXd", timeout=10 * SLEEP_MULTIPLIER
            )
            assignment_buttons = await tab.query_selector_all("li.MHxtic.QRiHXd")

            # Find urls for assignment pages
            assignment_page_button_a_tags = [
                await btn.query_selector("a.nUg0Te") for btn in assignment_buttons
            ]
            assignment_page_urls = [
                btn.__getattr__("href") for btn in assignment_page_button_a_tags
            ]
            assignment_page_urls = [BASE_URL + url for url in assignment_page_urls]

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

            assignments = [
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

            return assignments

        except TimeoutError as e:
            print("Checking if we're logged in")
            try:
                check1 = await tab.wait_for(text="To-do", timeout=10 * SLEEP_MULTIPLIER)
                check2 = await tab.wait_for(
                    text="Assigned", timeout=10 * SLEEP_MULTIPLIER
                )
                if check1 and check2:
                    print("We're logged in. No assignments found")
                    return
            except TimeoutError:
                print("Logging In")
                await perform_login(tab)
                continue


async def get_assignment_file_urls(browser, assignments: list[Assignment]):
    for assignment in assignments:
        assignment_page_tab = await browser.get(
            assignment.assignment_details_page_url, new_tab=True
        )

        # Wait for instructions first - this ensures page is loaded
        try:
            instructions_element = await assignment_page_tab.wait_for(
                selector="div.nGi02b.tLDEHd.j70YMc", timeout=10 * SLEEP_MULTIPLIER
            )
            if instructions_element:
                assignment.assignment_instructions = instructions_element.text

        except TimeoutError:
            print("No instructions found - timeout waiting for instructions element")
            assignment.assignment_instructions = "No instructions found"
        except Exception as e:
            print(f"Error getting instructions: {e}")
            assignment.assignment_instructions = "Error getting instructions"

        # Then try to get attachments
        try:
            # This assignment_file_button is to check if the page has loaded the attachments.
            assignment_file_button = await assignment_page_tab.wait_for(
                selector="a.vwNuXe.JkIgWb.QRiHXd.yixX5e", timeout=3 * SLEEP_MULTIPLIER
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


async def download_assignment_files(tab, browser, assignments: list[Assignment]):
    for assignment in assignments:

        download_directory_current = download_directory / assignment.classroom_name
        assignment_doc_local_path = (
            download_directory_current / assignment.assignment_name
        )
        assignment.assignment_doc_local_paths.append(assignment_doc_local_path)

        await tab.set_download_path(download_directory_current)
        print(assignment_doc_local_path)

        for assignment_file_url in assignment.assignment_doc_urls:
            assignment_file_url = get_drive_download_link(assignment_file_url)

            # tab.download_file does not work here.
            # await tab.download_file(get_drive_download_link(assignment_file_url), name)
            # So we rather open a new tab and that automatically downloads the file.
            download_tab = await tab.get(assignment_file_url, new_tab=True)
            # a sleep is needed here to ensure the file is downloaded in the right directory. if we don't wait, the download directory is changed in the next iteration before the file is downloaded.
            await download_tab.sleep(8 * SLEEP_MULTIPLIER)


async def main():
    browser = await uc.start(
        user_data_dir="./user",
        browser_executable_path="/usr/bin/google-chrome",
        # sandbox=False,
    )
    tab = await browser.get(missing_endpoint)

    assignments = await get_assignment_page_urls(tab)
    assignments = await get_assignment_file_urls(browser, assignments)
    print(assignments)
    await download_assignment_files(tab, browser, assignments)

    sample_path = pathlib.Path("w2.pdf")
    for assignment in assignments:
        assignment.assignment_doc_local_paths = [sample_path]

    await upload_assignment_files(browser, assignments)

    await browser.wait(1000)


if __name__ == "__main__":

    uc.loop().run_until_complete(main())
