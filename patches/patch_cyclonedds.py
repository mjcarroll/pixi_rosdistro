import os
import re
import subprocess
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
        subprocess.run(["git", "checkout", "--", rel_path], cwd=pkg_dir, capture_output=True)

def patch_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
    git_reset(path)

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Standardize the intptr_t/ssize_t fix
    if '#include <stdint.h>' not in content:
        # Prepend it after the header guard
        content = content.replace('#ifndef FILE_H\n#define FILE_H', '#ifndef FILE_H\n#define FILE_H\n\n#include <stdint.h>')
    
    # Fix buggy WIN32 block
    old_block = """#if WIN32
# include <basetsd.h>
typedef SSIZE_T ssize_t;
#endif"""

    new_block = """#if defined(_WIN32) || defined(WIN32)
# include <basetsd.h>
# ifndef _SSIZE_T_DEFINED
typedef SSIZE_T ssize_t;
#  define _SSIZE_T_DEFINED
# endif
#endif"""

    if old_block in content:
        content = content.replace(old_block, new_block)
    
    # Handle the function signature
    old_line = 'IDL_EXPORT ssize_t idl_untaint_path(char *path);'
    new_line = '#ifdef _WIN32\nIDL_EXPORT intptr_t idl_untaint_path(char *path);\n#else\nIDL_EXPORT ssize_t idl_untaint_path(char *path);\n#endif'
    
    if old_line in content:
        content = content.replace(old_line, new_line)

    with open(path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    print(f"Patched {path}")
    return True

if __name__ == "__main__":
    target = 'src/eclipse-cyclonedds/cyclonedds/src/idl/src/file.h'
    if os.path.exists(target):
        patch_file(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
