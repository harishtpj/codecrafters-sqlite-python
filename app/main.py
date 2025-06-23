import sys
from .structures import *
from .helpers import *

# import sqlparse - available if you need it!
DB_FILE = sys.argv[1]
CMD = sys.argv[2]

def read_table_info(cell_ptrs):
    tables = {}
    for ptr in cell_ptrs.ptrs:
        try:
            cell = SqliteMasterCell.from_bytes(page_data[ptr:])
            if len(cell.items) == 5:
                tables[cell.items[1]] = TableInfo(cell.items[0], *cell.items[2:]) 
        except Exception as e:
            print(f"Error parsing cell at offset {ptr}: {e}", file=sys.stderr)
            continue
    return tables


def main():
    if CMD == ".dbinfo":
        print(f"database page size: {hdr.page_size}")
        print(f"write version: {hdr.write_version}")
        print(f"read version: {hdr.read_version}")
        print(f"reserved bytes: {hdr.reserved_bytes}")
        print(f"number of tables: {btree_hdr.n_cells}")
    elif CMD == ".tables":
        print(*(table.tbl_name for table in tables.values() if table.type == 'table'))
        # for ptr in cell_ptrs.ptrs:
        #     try:
        #         cell = SqliteMasterCell.from_bytes(page_data[ptr:])
        #         print(cell)
        #         if len(cell.items) > 0 and cell.items[0] == "table":
        #             tables.append(cell.items[2])
        #     except Exception as e:
        #         print(f"Error parsing cell at offset {ptr}: {e}", file=sys.stderr)
        #         continue
        # print(*tables)
    elif CMD.startswith("select count(*) from"):
        _, table_name = CMD.rsplit(" ", 1)
        t_info = tables.get(table_name)
        if t_info is None:
            print("Table not found")
            sys.exit(1)
        goto_root_page(dbf, t_info.rootpage, hdr.page_size)
        r_page_data = dbf.read(hdr.page_size)

        #---count btree 
        hdr_offset = 100 if t_info.rootpage == 1 else 0
        new_btree_hdr = BTreePageHeader.from_bytes(r_page_data[hdr_offset:])
        print(new_btree_hdr.n_cells)
    elif CMD.startswith('select '):
        _, table_name = CMD.split()
        t_info = tables.get(table_name)
        if t_info is None:
            print("Table not found")
            sys.exit(1)
        goto_root_page(dbf, t_info.rootpage, hdr.page_size)
        r_page_data = dbf.read(hdr.page_size)

        #---read data 
        hdr_offset = 100 if t_info.rootpage == 1 else 0
        new_btree_hdr = BTreePageHeader.from_bytes(r_page_data[hdr_offset:])
        new_cell_ptrs = CellPointerArray.from_bytes(r_page_data[8:], new_btree_hdr.n_cells)
        for ptr in new_cell_ptrs.ptrs:
            try:
                cell = SqliteMasterCell.from_bytes(r_page_data[ptr:])
                print(cell)
            except Exception as e:
                print(f"Error parsing cell at offset {ptr}: {e}", file=sys.stderr)
                continue

    else:
        print(f"Invalid command: {CMD}")

with open(DB_FILE, 'rb') as dbf:
    hdr = FileHeader.from_bytes(dbf.read(100))
    dbf.seek(0)
    page_data = dbf.read(hdr.page_size)
    btree_hdr = BTreePageHeader.from_bytes(page_data[100:])
    cell_ptrs = CellPointerArray.from_bytes(page_data[108:], btree_hdr.n_cells)
    tables = read_table_info(cell_ptrs)
    main()

