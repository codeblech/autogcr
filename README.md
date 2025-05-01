## Usage Instructions

1. Install python dependencies:

    ```bash
    poetry install
    ```

2. Install typst

    Linux, macOS, WSL

    ```sh
    curl -fsSL https://typst.community/typst-install/install.sh | sh
    ```

    Windows

    ```ps1
    irm https://typst.community/typst-install/install.ps1 | iex
    ```

> [!NOTE]
> Typst is required to convert docx assignment attachments to pdf.
> If installation fails, refer to [this](https://github.com/typst-community/typst-install)

3. Create a `.env` file and set the `GEMINI_API_KEY` environment variable:

    ```bash
    EMAIL=<your-email>
    PASSWORD=<your-password>
    DEFAULT_DOWNLOAD_DIRECTORY ="./downloads"
    GEMINI_API_KEY=<your-gemini-api-key>
    ```
