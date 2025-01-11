import nodriver as uc
import os
from endpoints import missing_endpoint, turned_in_endpoint, not_turned_in_endpoint
from dotenv import load_dotenv
from asyncio import TimeoutError
load_dotenv()

SLEEP_MULTIPLIER = 1

BASE_URL = "https://classroom.google.com"
email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")
download_directory = os.environ.get("DEFAULT_DOWNLOAD_DIRECTORY")


async def perform_login(tab):
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


async def get_assignment_page_urls(tab):
    while True:
        try:
            # assignment_button = await tab.wait_for(selector="a.nUg0Te", timeout=10)
            # assignment_buttons = await tab.query_selector_all("a.nUg0Te")
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
            assignment_metadata = {
                "assignment_names": assignment_names,
                "assignment_due_dates": assignment_due_dates,
                "assignment_page_urls": assignment_page_urls,
            }
            return assignment_metadata

        except TimeoutError as e:
            print("Checking if we're logged in")
            check1 = await tab.wait_for(text="To-do", timeout=10 * SLEEP_MULTIPLIER)
            check2 = await tab.wait_for(text="Assigned", timeout=10 * SLEEP_MULTIPLIER)
            if check1 and check2:
                print("We're logged in. No assignments found")
                return

            print("Logging In")
            await perform_login(tab)
            continue


async def get_assignment_file_urls(browser, assignment_metadata):
    assignment_page_urls = assignment_metadata["assignment_page_urls"]

    assignment_file_urls = []
    for assignment_page_url in assignment_page_urls:
        assignment_page_tab = await browser.get(assignment_page_url, new_tab=True)
        try:
            assignment_file_button = await assignment_page_tab.wait_for(
                selector="a.vwNuXe.JkIgWb.QRiHXd.yixX5e", timeout=10 * SLEEP_MULTIPLIER
            )
            assignment_file_buttons = await assignment_page_tab.query_selector_all(
                "a.vwNuXe.JkIgWb.QRiHXd.yixX5e"
            )
            assignment_file_urls.append([
                btn.__getattr__("href") for btn in assignment_file_buttons
            ])


        except TimeoutError:
            assignment_file_urls.append([])
            print("No attachment found for assignment with url: ", assignment_page_url)

        await assignment_page_tab.close()

    assignment_metadata["assignment_file_urls"] = assignment_file_urls

    return assignment_metadata


async def main():
    browser = await uc.start(
        user_data_dir="./user",
        browser_executable_path="/usr/bin/google-chrome",
        # sandbox=False,
    )
    tab = await browser.get(missing_endpoint)

    assignment_metadata = await get_assignment_page_urls(tab)
    # tab.close()
    assignment_metadata = await get_assignment_file_urls(browser, assignment_metadata)

    assignment_file_names = []
    for assignment_name, assignment_file_urls in zip(
        assignment_metadata["assignment_names"],
        assignment_metadata["assignment_file_urls"],
    ):
        assignment_file_names_current = []
        for assignment_file_url in assignment_file_urls:
            file_tab = await browser.get(assignment_file_url, new_tab=True)
            try:
                download_button = await file_tab.wait_for(selector="div.ndfHFb-c4YZDc-Bz112c.ndfHFb-c4YZDc-C7uZwb-LgbsSe-Bz112c.ndfHFb-c4YZDc-nupQLb-Bz112c", timeout=10 * SLEEP_MULTIPLIER)
                await browser.wait(5 * SLEEP_MULTIPLIER)
                assignment_file_name_tag = await file_tab.query_selector(
                    selector="meta[property='og:title']"
                )
                assignment_file_name = assignment_file_name_tag.__getattr__("content")
                assignment_file_names_current.append(assignment_file_name)

                await download_button.mouse_click()
                await browser.wait(5 * SLEEP_MULTIPLIER)
            except TimeoutError:
                print("No download button found for file with url: ", assignment_file_url)
                continue

        assignment_file_names.append(assignment_file_names_current)

    assignment_metadata["assignment_file_names"] = assignment_file_names
    print(assignment_metadata)

    await browser.wait(1000)

if __name__ == "__main__":

    uc.loop().run_until_complete(main())
