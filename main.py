import pathlib
import os
import nodriver as uc
from dotenv import load_dotenv
from assignment_manager import AssignmentManager, GoogleClassroomConfig

load_dotenv()


async def main():
    """Main entry point for the Google Classroom automation."""
    # Initialize configuration
    config = GoogleClassroomConfig(
        email=os.environ.get("EMAIL"),
        password=os.environ.get("PASSWORD"),
        download_directory=pathlib.Path(os.environ.get("DEFAULT_DOWNLOAD_DIRECTORY")),
    )

    # Create and initialize assignment manager
    manager = AssignmentManager(config)
    await manager.initialize_browser()

    try:
        # Get and process assignments
        assignments = await manager.get_assignment_page_urls()
        if assignments:
            # Get file URLs and download files
            assignments = await manager.get_assignment_file_urls(assignments)
            await manager.download_assignment_files(assignments)

            # TODO: Replace this with actual solution file paths
            # For testing purposes - using a sample path
            sample_path = pathlib.Path("w2.pdf")
            for assignment in assignments:
                assignment.assignment_doc_local_paths = [sample_path]

            # Upload completed assignments
            await manager.upload_assignment_files(assignments)

            # Keep browser open for a while (for debugging/testing)
            await manager.browser.wait(1000)
    finally:
        print("Finished")


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
