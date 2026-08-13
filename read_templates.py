import os
import sys

def read_doc_win32(filepath):
    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(os.path.abspath(filepath))
        text = doc.Content.Text
        tables_data = []
        for table in doc.Tables:
            t_data = []
            for row in table.Rows:
                r_data = [cell.Range.Text.strip().replace('\r\x07', '').replace('\x07', '') for cell in row.Cells]
                t_data.append(r_data)
            tables_data.append(t_data)
        doc.Close()
        word.Quit()
        return text, tables_data
    except Exception as e:
        return f"Win32 error: {e}", []

def read_doc_fallback(filepath):
    # try reading raw text / olefile
    with open(filepath, 'rb') as f:
        content = f.read()
    # extract strings
    import re
    strings = re.findall(b'[\x20-\x7E\r\n]{4,}', content)
    return "\n".join(s.decode('latin-1') for s in strings[:100]), []

print("=== Reading Advanced learners template 25-26.doc ===")
t1, tbl1 = read_doc_win32("Advanced learners template 25-26.doc")
if "Win32 error" in t1:
    print(t1)
    t1, tbl1 = read_doc_fallback("Advanced learners template 25-26.doc")
print("TEXT:")
print(t1[:1500])
print("\nTABLES COUNT:", len(tbl1))
for i, tbl in enumerate(tbl1):
    print(f"\n--- TABLE {i+1} (rows: {len(tbl)}) ---")
    for r in tbl[:10]:
        print(r)

print("\n\n=== Reading Slow learners template 25-26.doc ===")
t2, tbl2 = read_doc_win32("Slow learners template 25-26.doc")
if "Win32 error" in t2:
    print(t2)
    t2, tbl2 = read_doc_fallback("Slow learners template 25-26.doc")
print("TEXT:")
print(t2[:1500])
print("\nTABLES COUNT:", len(tbl2))
for i, tbl in enumerate(tbl2):
    print(f"\n--- TABLE {i+1} (rows: {len(tbl)}) ---")
    for r in tbl[:10]:
        print(r)
