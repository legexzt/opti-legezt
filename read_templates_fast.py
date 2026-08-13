import olefile
import re

def extract_text_from_doc(filename):
    print(f"\n==================== {filename} ====================")
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Try decoding utf-16le and latin-1 strings
    # In binary Word files (.doc), text is stored in WordDocument stream or 1Table stream
    ole = olefile.OleFileIO(filename)
    print("Streams in OLE:", ole.listdir())
    
    # Let's inspect WordDocument stream
    if ole.exists('WordDocument'):
        stream = ole.openstream('WordDocument')
        wdata = stream.read()
        print("WordDocument stream size:", len(wdata))
        
    # Let's extract all readable ASCII/UTF-16 text
    raw_ascii = re.findall(rb'[\x20-\x7E\r\n\t]{4,}', data)
    print("\n--- ALL EXTRACTED ASCII BLOCKS ---")
    for block in raw_ascii:
        decoded = block.decode('latin-1').strip()
        if len(decoded) > 5:
            print(decoded)

extract_text_from_doc("Advanced learners template 25-26.doc")
extract_text_from_doc("Slow learners template 25-26.doc")
