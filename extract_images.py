import olefile
import os

def extract_images_from_doc(filename, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Check for PNG or JPEG magic bytes
    # PNG: \x89PNG\r\n\x1a\n
    # JPG: \xff\xd8\xff
    png_starts = []
    idx = 0
    while True:
        pos = data.find(b'\x89PNG\r\n\x1a\n', idx)
        if pos == -1:
            break
        png_starts.append(pos)
        idx = pos + 8
        
    print(f"Found {len(png_starts)} PNGs in {filename}")
    for i, p_start in enumerate(png_starts):
        # find IEND
        iend = data.find(b'IEND\xaeB`\x82', p_start)
        if iend != -1:
            png_data = data[p_start:iend+8]
            out_name = os.path.join(out_dir, f"{os.path.splitext(filename)[0]}_img_{i+1}.png")
            with open(out_name, 'wb') as img_f:
                img_f.write(png_data)
            print(f"Saved {out_name} (size: {len(png_data)} bytes)")

extract_images_from_doc("Advanced learners template 25-26.doc", "extracted_assets")
extract_images_from_doc("Slow learners template 25-26.doc", "extracted_assets")
