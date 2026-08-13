import fitz # PyMuPDF
import os

def inspect_pdf(pdf_path):
    print("="*60)
    print("INSPECTING PDF:", pdf_path)
    print("="*60)
    doc = fitz.open(pdf_path)
    print("Page count:", len(doc))
    
    os.makedirs("extracted_assets", exist_ok=True)
    img_count = 0
    for p_num, page in enumerate(doc):
        print(f"\n--- PAGE {p_num + 1} ---")
        text = page.get_text()
        print("Text preview:")
        print(text[:800])
        print("...")
        
        # Extract images
        image_list = page.get_images(full=True)
        print(f"Images on page {p_num + 1}: {len(image_list)}")
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            img_filename = f"extracted_assets/logo_extracted_p{p_num+1}_{img_index+1}.{image_ext}"
            with open(img_filename, "wb") as f_img:
                f_img.write(image_bytes)
            print(f"Extracted image: {img_filename} (size: {len(image_bytes)} bytes, format: {image_ext})")
            img_count += 1

inspect_pdf("CSE 2024-25 C  Advance  learners template1.pdf")
inspect_pdf("CSE 2024-25 C  Slow  learners template.pdf")
