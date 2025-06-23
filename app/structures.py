# Important structures defined for sqlite3 db file processing
import struct
import sys
from array import array
from dataclasses import dataclass

@dataclass
class FileHeader:
    magic: bytes
    page_size: int
    write_version: int
    read_version: int
    reserved_bytes: int

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls(*struct.unpack(
            "> 16s H B B B", data[:21]
        ))

@dataclass
class BTreePageHeader:
    page_type: int
    first_freeblock: int
    n_cells: int
    cell_content_area: int
    fragmented_free_bytes: int

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls(*struct.unpack("> B H H H B", data[:8]))

@dataclass
class CellPointerArray:
    ptrs: array

    @classmethod
    def from_bytes(cls, data: bytes, n_cells: int):
        arr = array('H')
        arr.frombytes(data[:n_cells * 2])
        if sys.byteorder == 'little':
            arr.byteswap()
        return cls(arr)

def read_varint(data: bytes, offset: int) -> tuple[int, int]:
    """Read a variable-length integer from bytes, return (value, bytes_consumed)"""
    value = 0
    bytes_read = 0
    
    for i in range(9):  # Max 9 bytes for a varint
        if offset + i >= len(data):
            break
            
        byte = data[offset + i]
        bytes_read += 1
        
        if i == 8:  # 9th byte uses all 8 bits
            value = (value << 8) | byte
            break
        else:
            value = (value << 7) | (byte & 0x7F)
            if (byte & 0x80) == 0:  # MSB is 0, this is the last byte
                break
    
    return value, bytes_read

@dataclass
class SqliteMasterCell:
    rowid: int
    payload_len: int
    hdr_len: int
    serial_types: list
    items: list

    @classmethod
    def from_bytes(cls, data: bytes):
        offset = 0

        payload_len, bytes_consumed = read_varint(data, offset)
        offset += bytes_consumed

        rowid, bytes_consumed = read_varint(data, offset)
        offset += bytes_consumed

        hdr_len, bytes_consumed = read_varint(data, offset)
        hdr_start = offset
        offset += bytes_consumed

        serial_types = []
        while offset < hdr_start + hdr_len:
            st, bytes_consumed = read_varint(data, offset)
            serial_types.append(st)
            offset += bytes_consumed

        items = []
        for st in serial_types:
            if st == 1:
                items.append(*struct.unpack('>b', data[offset:offset+1]))
                offset += 1
            elif st >= 13 and st % 2 == 1:
                # TEXT
                size = (st - 13) // 2
                try:
                    text = data[offset:offset+size].decode('utf-8')
                    items.append(text)
                except UnicodeDecodeError:
                    items.append(data[offset:offset+size])
                offset += size
            else:
                items.append(None)

        return cls(rowid, payload_len, hdr_len, serial_types, items)
