import olefile
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8')

def parse_word_doc(filename):
    ole = olefile.OleFileIO(filename)
    word_stream = ole.openstream('WordDocument').read()
    
    flags = struct.unpack_from('<H', word_stream, 0x000A)[0]
    fWhichTblStm = (flags >> 9) & 1
    tbl_stream_name = '1Table' if fWhichTblStm else '0Table'
    
    fcClx = struct.unpack_from('<I', word_stream, 0x01A2)[0]
    lcbClx = struct.unpack_from('<I', word_stream, 0x01A6)[0]
    
    if ole.exists(tbl_stream_name):
        tbl_stream = ole.openstream(tbl_stream_name).read()
        if fcClx < len(tbl_stream):
            clx_data = tbl_stream[fcClx:fcClx+lcbClx]
            pos = 0
            while pos < len(clx_data):
                clxt = clx_data[pos]
                pos += 1
                if clxt == 1:
                    cb = struct.unpack_from('<H', clx_data, pos)[0]
                    pos += 2 + cb
                elif clxt == 2:
                    lcb = struct.unpack_from('<I', clx_data, pos)[0]
                    pos += 4
                    pcd_data = clx_data[pos:pos+lcb]
                    n = (lcb - 4) // 12
                    cps = [struct.unpack_from('<I', pcd_data, i*4)[0] for i in range(n+1)]
                    pcds_offset = (n+1)*4
                    full_text = []
                    for i in range(n):
                        cp_start = cps[i]
                        cp_end = cps[i+1]
                        pcd = pcd_data[pcds_offset + i*8 : pcds_offset + (i+1)*8]
                        fcValue = struct.unpack_from('<I', pcd, 2)[0]
                        fCompressed = (fcValue & 0x40000000) != 0
                        fc = (fcValue & ~0x40000000)
                        char_count = cp_end - cp_start
                        if fCompressed:
                            actual_fc = fc // 2
                            piece_bytes = word_stream[actual_fc : actual_fc + char_count]
                            text = piece_bytes.decode('latin-1', errors='ignore')
                        else:
                            actual_fc = fc
                            piece_bytes = word_stream[actual_fc : actual_fc + char_count*2]
                            text = piece_bytes.decode('utf-16le', errors='ignore')
                        full_text.append(text)
                    joined = "".join(full_text)
                    print(f"=== FULL TEXT FOR {filename} ===")
                    print(joined)
                    print("\n" + "="*80 + "\n")
                    break

parse_word_doc("Advanced learners template 25-26.doc")
parse_word_doc("Slow learners template 25-26.doc")
