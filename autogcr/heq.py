import hrequests

import os
from endpoints import missing_endpoint, turned_in_endpoint, not_turned_in_endpoint
from dotenv import load_dotenv
import time

load_dotenv()

SLEEP_MULTIPLIER = 1
BASE_URL = "https://classroom.google.com"
email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")
download_directory = os.environ.get("DEFAULT_DOWNLOAD_DIRECTORY")

def perform_login(page):
    # Wait for and fill email
    page.awaitSelector("input[type=email]")
    page.type("input[type=email]", email)
    time.sleep(2 * SLEEP_MULTIPLIER)
    
    # Click next
    next_button = page.html.find("button[type=button]")
    next_button.click()
    time.sleep(5 * SLEEP_MULTIPLIER)

    # Wait for and fill password
    page.awaitSelector("input[type=password]")
    page.type("input[type=password]", password)
    time.sleep(2 * SLEEP_MULTIPLIER)
    
    # Click next
    next_button = page.html.find("button[type=button]")
    next_button.click()
    time.sleep(5 * SLEEP_MULTIPLIER)

    # Check for 2FA
    if "2-Step Verification" in page.html.text:
        print("Please perform 2-Step Verification manually")
        # Wait for manual 2FA completion
        page.awaitUrl(BASE_URL)

def get_assignment_page_urls(page):
    # Wait for assignments to load
    page.awaitSelector("li.MHxtic.QRiHXd")
    
    # Get assignment elements
    assignments = page.html.find_all("li.MHxtic.QRiHXd")
    
    assignment_names = []
    assignment_due_dates = []
    assignment_page_urls = []

    for assignment in assignments:
        # Get assignment name
        name_elem = assignment.find("p.asQXV.oDLUVd.YVvGBb")
        assignment_names.append(name_elem.text if name_elem else "Unnamed")

        # Get due date
        due_date_elem = assignment.find("p.EhRlC.tGZ0W.pOf0gc")
        assignment_due_dates.append(due_date_elem.text if due_date_elem else "No due date")

        # Get assignment URL
        url_elem = assignment.find("a.nUg0Te")
        if url_elem and 'href' in url_elem.attrs:
            assignment_page_urls.append(BASE_URL + url_elem.attrs['href'])

    return {
        "assignment_names": assignment_names,
        "assignment_due_dates": assignment_due_dates,
        "assignment_page_urls": assignment_page_urls
    }

def get_assignment_file_urls(browser_session, assignment_metadata):
    assignment_file_urls = []

    for url in assignment_metadata["assignment_page_urls"]:
        resp = browser_session.get(url)
        page = resp.render()
        try:
            page.awaitSelector("a.vwNuXe.JkIgWb.QRiHXd.yixX5e", timeout=10 * SLEEP_MULTIPLIER)
            file_buttons = page.html.find_all("a.vwNuXe.JkIgWb.QRiHXd.yixX5e")
            file_urls = [btn.attrs['href'] for btn in file_buttons if 'href' in btn.attrs]
            assignment_file_urls.append(file_urls)
        except:
            print(f"No attachment found for assignment with url: {url}")
            assignment_file_urls.append([])
        page.close()

    assignment_metadata["assignment_file_urls"] = assignment_file_urls
    return assignment_metadata

def main():
    # Create a BrowserSession instance
    browser_session = hrequests.BrowserSession(
        browser_args=["--start-maximized"],  # Optional browser arguments
        headless=False  # Use headful mode for first-time 2FA
    )
    
    try:
        # Initial navigation and login
        resp = browser_session.get(missing_endpoint)
        page = resp.render()
        
        # Handle login if needed
        if "Sign in" in page.html.text:
            perform_login(page)
        
        assignment_metadata = get_assignment_page_urls(page)
        page.close()
        
        # Get file URLs and handle downloads
        assignment_metadata = get_assignment_file_urls(browser_session, assignment_metadata)
        
        # Handle file downloads
        assignment_file_names = []
        for urls in assignment_metadata["assignment_file_urls"]:
            current_files = []
            for file_url in urls:
                resp = browser_session.get(file_url)
                page = resp.render()
                try:
                    # Wait for download button
                    page.awaitSelector("div.ndfHFb-c4YZDc-Bz112c", timeout=10 * SLEEP_MULTIPLIER)
                    time.sleep(5 * SLEEP_MULTIPLIER)
                    
                    # Get file name
                    title_meta = page.html.find("meta[property='og:title']")
                    if title_meta:
                        file_name = title_meta.attrs.get('content')
                        current_files.append(file_name)
                    
                    # Click download
                    page.click("div.ndfHFb-c4YZDc-Bz112c")
                    time.sleep(5 * SLEEP_MULTIPLIER)
                except:
                    print(f"No download button found for file with url: {file_url}")
                    continue
                finally:
                    page.close()
            
            assignment_file_names.append(current_files)
        
        assignment_metadata["assignment_file_names"] = assignment_file_names
        print(assignment_metadata)

    finally:
        # Always close the browser session
        browser_session.close()

if __name__ == "__main__":
    main()