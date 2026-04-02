import os
import sys

def patch_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
    # Reset first if it's a git repo
    pkg_dir = path
    while pkg_dir and not os.path.exists(os.path.join(pkg_dir, '.git')):
        next_dir = os.path.dirname(pkg_dir)
        if next_dir == pkg_dir:
            pkg_dir = None
            break
        pkg_dir = next_dir
    
    if pkg_dir:
        # We found the git root for this file
        rel_path = os.path.relpath(path, pkg_dir)
        os.system(f"cd {pkg_dir} && git checkout {rel_path}")

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add ssize_t definition for Windows/MSVC
    ssize_fix = """
#if defined(_WIN32) && !defined(_SSIZE_T_DEFINED)
#include <BaseTsd.h>
typedef SSIZE_T ssize_t;
#define _SSIZE_T_DEFINED
#endif
"""
    if 'typedef SSIZE_T ssize_t;' not in content:
        if '#ifndef FILE_H' in content:
            content = content.replace('#ifndef FILE_H', '#ifndef FILE_H' + ssize_fix)
            print(f"Added ssize_t fix to {path}")
        else:
            content = ssize_fix + content
            print(f"Prepended ssize_t fix to {path}")

    with open(path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

if __name__ == "__main__":
    target = 'src/eclipse-cyclonedds/cyclonedds/src/idl/src/file.h'
    if os.path.exists(target):
        patch_file(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
