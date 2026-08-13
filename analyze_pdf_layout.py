import fitz
import json

def analyze_pdf_structure(pdf_path):
    print("="*60)
    print("ANALYZING PDF STRUCTURE:", pdf_path)
    print("="*60)
    doc = fitz.open(pdf_path)
    for p_num in range(min(4, len(doc))):
        page = doc[p_num]
        print(f"\n--- PAGE {p_num + 1} ---")
        text_blocks = page.get_text("blocks")
        for b in text_blocks:
            print(f"[{b[0]:.1f}, {b[1]:.1f}] {b[4].strip()[:100]}")
            
analyze_pdf_structure("CSE 2024-25 C  Advance  learners template1.pdf")
