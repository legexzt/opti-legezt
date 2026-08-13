import os
import shutil

os.makedirs("app/static/images", exist_ok=True)
if os.path.exists("extracted_assets/logo_extracted_p1_1.jpeg"):
    shutil.copy("extracted_assets/logo_extracted_p1_1.jpeg", "app/static/images/college_logo.jpeg")
    shutil.copy("extracted_assets/logo_extracted_p1_1.jpeg", "app/static/images/college_logo.png")
    print("Logo successfully copied to app/static/images/college_logo.jpeg and college_logo.png")
else:
    print("Warning: extracted_assets/logo_extracted_p1_1.jpeg not found")
