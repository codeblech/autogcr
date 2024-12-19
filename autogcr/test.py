# Input URL
url = "https://drive.google.com/file/d/1jeDExeBxPSnJkVRf_0h2-SEEd54Fms4z/view"

# Splitting the URL to extract the file ID
parts = url.split("/")
file_id = parts[5] if len(parts) > 5 else None

if file_id:
    print("Extracted ID:", file_id)
else:
    print("No file ID found.")
