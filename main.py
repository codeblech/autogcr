import pathlib
import os
import nodriver as uc
from dotenv import load_dotenv
from loguru import logger
from assignment_manager import AssignmentManager, GoogleClassroomConfig
from solve import SimpleSolver

load_dotenv()

# Configure logger
logger.add("automation.log", rotation="10 MB", level="INFO")


async def main():
    """Main entry point for the Google Classroom automation."""
    # Initialize configuration
    logger.info("Initializing Google Classroom automation")
    config = GoogleClassroomConfig(
        email=os.environ.get("EMAIL"),
        password=os.environ.get("PASSWORD"),
        download_directory=pathlib.Path(os.environ.get("DEFAULT_DOWNLOAD_DIRECTORY")),
    )

    # Create and initialize assignment manager
    logger.info("Creating and initializing assignment manager")
    manager = AssignmentManager(config)
    await manager.initialize_browser()

    try:
        # Download assignments and their files
        logger.info("Starting assignment download")
        assignments = await manager.download_assignment_files()
        logger.info(f"Downloaded {len(assignments)} assignments")
        logger.info(f"Assignments: \n{assignments}")

        # Solve assignments
        for assignment in assignments:
            logger.info(f"Solving assignment: {assignment.assignment_name}")
            solver = SimpleSolver()
            assignment.solution_doc_local_path = solver.solve_assignment(assignment)

        # Upload completed assignments
        await manager.upload_assignment_files(assignments)

        # Keep browser open for a while (for debugging/testing)
        await manager.browser.wait(1000)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise
    finally:
        logger.info("Finished execution")


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
