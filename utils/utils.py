import pypandoc
from pypandoc.pandoc_download import download_pandoc

def ensure_pandoc_installed():
    try:
        pypandoc.get_pandoc_path()
    except OSError:
        print("Downloading pandoc binary...")
        download_pandoc()
