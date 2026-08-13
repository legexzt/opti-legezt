import olefile
import re

def dump_all_text(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print("="*60)
    print("ALL STRINGS FOR", filename)
    print("="*60)
    # UTF-16LE strings
    u_strings = re.findall(rb'(?:[\x20-\x7E]\x00){4,}', data)
    for s in u_strings:
        try:
            txt = s.decode('utf-16le').strip()
            if len(txt) > 3:
                print("[UTF16]", txt)
        except:
            pass
            
dump_all_text("Advanced learners template 25-26.doc")
dump_all_text("Slow learners template 25-26.doc")
