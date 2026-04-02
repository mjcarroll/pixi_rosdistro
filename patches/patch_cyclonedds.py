import os
import sys

def git_reset(path):
    pkg_dir = os.path.dirname(path)
    while pkg_dir and not os.path.exists(os.path.join(pkg_dir, '.git')):
        next_dir = os.path.dirname(pkg_dir)
        if next_dir == pkg_dir:
            pkg_dir = None
            break
        pkg_dir = next_dir
    
    if pkg_dir:
        rel_path = os.path.relpath(path, pkg_dir)
        os.system(f"cd {pkg_dir} && git checkout {rel_path}")

def patch_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
    git_reset(path)

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add ssize_t definition for Windows/MSVC
    # And REPLACE the problematic line directly to be sure
    ssize_fix = """
#if defined(_WIN32)
#include <BaseTsd.h>
#ifndef ssize_t
typedef SSIZE_T ssize_t;
#endif
#endif
"""
    if 'typedef SSIZE_T ssize_t;' not in content:
        content = ssize_fix + content
        print(f"Added ssize_t fix to {path}")
    
    # Also replace the line directly to use long long if we want to be super sure
    # but the typedef should work if it's included before usage.
    # The error was in line 31.
    
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
