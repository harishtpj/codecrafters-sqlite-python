# Helper functions

def goto_root_page(fptr, root_page, page_size):
    fptr.seek((root_page - 1) * page_size)
