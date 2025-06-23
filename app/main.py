import sys
from .structures import *

# import sqlparse - available if you need it!
DB_FILE = sys.argv[1]
CMD = sys.argv[2]

def main():
    if CMD == ".dbinfo":
        print(f"database page size: {hdr.page_size}")
        print(f"write version: {hdr.write_version}")
        print(f"read version: {hdr.read_version}")
        print(f"reserved bytes: {hdr.reserved_bytes}")
        print(f"number of tables: {btree_hdr.n_cells}")
    elif CMD == ".tables":
        cell_ptrs = CellPointerArray.from_bytes(page_data[108:], btree_hdr.n_cells)
        tables = []
        for ptr in cell_ptrs.ptrs:
            try:
                cell = SqliteMasterCell.from_bytes(page_data[ptr:])
                if len(cell.items) > 0 and cell.items[0] == "table":
                    tables.append(cell.items[1])
            except Exception as e:
                print(f"Error parsing cell at offset {ptr}: {e}", file=sys.stderr)
                continue
        print(*tables)
    else:
        print(f"Invalid command: {CMD}")

with open(DB_FILE, 'rb') as dbf:
    hdr = FileHeader.from_bytes(dbf.read(100))
    dbf.seek(0)
    page_data = dbf.read(hdr.page_size)
    btree_hdr = BTreePageHeader.from_bytes(page_data[100:])
    main()

