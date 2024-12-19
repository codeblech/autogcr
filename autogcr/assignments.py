import nodriver as uc
import os
from endpoints import missing_endpoint, turned_in_endpoint, not_turned_in_endpoint
from dotenv import load_dotenv
import json
import asyncio
from asyncio import TimeoutError

load_dotenv()

BASE_URL = "https://classroom.google.com"
email = os.environ.get("email")
password = os.environ.get("password")


async def perform_login(tab):
    email_input_box = await tab.select("input[type=email]")
    print("sending email keys")
    await email_input_box.send_keys(email)
    await tab.sleep(2)
    next_button = await tab.find("Next", best_match=True)
    print("clicking next button")
    await next_button.mouse_click()

    await tab.sleep(5)

    password_input_box = await tab.select("input[type=password]")
    print("sending password keys")
    await password_input_box.send_keys(password)
    await tab.sleep(2)
    next_button = await tab.find("Next", best_match=True)
    print("clicking next button")
    await next_button.mouse_click()
    await tab.sleep(5)

    if await tab.find("2-Step Verification", best_match=True):
        print("Please perform 2-Step Verification manually")
        # loading spinner


async def get_assignment_page_urls(tab):
    while True:
        try:
            # assignment_button = await tab.wait_for(selector="a.nUg0Te", timeout=10)
            # assignment_buttons = await tab.query_selector_all("a.nUg0Te")
            assignment_button = await tab.wait_for(
                selector="li.MHxtic.QRiHXd", timeout=10
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
            print(assignment_metadata)
            return assignment_metadata

        except TimeoutError as e:
            print("Checking if we're logged in")
            check1 = await tab.wait_for(text="To-do", timeout=100)
            check2 = await tab.wait_for(text="Assigned", timeout=100)
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
                selector="a.vwNuXe.JkIgWb.QRiHXd.yixX5e", timeout=10
            )
            assignment_file_buttons = await assignment_page_tab.query_selector_all(
                "a.vwNuXe.JkIgWb.QRiHXd.yixX5e"
            )
            assignment_file_urls_current = [
                btn.__getattr__("href") for btn in assignment_file_buttons
            ]
            assignment_file_urls.append(assignment_file_urls_current)

        except TimeoutError:
            print("No attachment found for assignment with url: ", assignment_page_url)

        await assignment_page_tab.close()


    assignment_metadata["assignment_file_urls"] = assignment_file_urls
    print(assignment_metadata)
    return assignment_metadata



async def main():
    browser = await uc.start(
        user_data_dir="./user",
        browser_executable_path="/usr/bin/google-chrome",
        # sandbox=False,
    )
    tab = await browser.get(not_turned_in_endpoint)

    assignment_page_urls = await get_assignment_page_urls(tab)
    page_url_to_file_url = await get_assignment_file_urls(browser, assignment_page_urls)
    print(page_url_to_file_url)


if __name__ == "__main__":

    uc.loop().run_until_complete(main())
