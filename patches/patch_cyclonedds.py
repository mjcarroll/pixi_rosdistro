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
        # Use a more robust git checkout
        os.system(f"cd {pkg_dir} && git checkout -- {rel_path} 2>/dev/null")

def patch_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
    git_reset(path)

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add intptr_t/ssize_t fix
    if '#include <stdint.h>' not in content:
        content = content.replace('#include <stddef.h>', '#include <stddef.h>\n#include <stdint.h>')
    
    # Use a simpler replacement for the problematic line
    old_line = 'IDL_EXPORT ssize_t idl_untaint_path(char *path);'
    new_line = '#ifdef _WIN32\nIDL_EXPORT intptr_t idl_untaint_path(char *path);\n#else\nIDL_EXPORT ssize_t idl_untaint_path(char *path);\n#endif'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        print(f"Patched {path} with intptr_t for Windows")

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
