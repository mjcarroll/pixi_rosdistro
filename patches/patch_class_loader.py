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

def patch_file(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    git_reset(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Library path comparison (stricmp for Windows)
    old_code = """    for (auto& it : classes_available_map) {
      if (it.second == library_path) {
        classes.push_back(it.first);
      }
    }"""

    new_code = """    for (auto& it : classes_available_map) {
      // Use case-insensitive comparison on Windows
#ifdef _WIN32
      if (_stricmp(it.second.c_str(), library_path.c_str()) == 0) {
#else
      if (it.second == library_path) {
#endif
        classes.push_back(it.first);
      }
    }"""

    if old_code in content:
        content = content.replace(old_code, new_code)

    # 2. Const-correctness for ClassLoader pointers
    # Use regex to find all occurrences of ClassLoader * loader = getClassLoaderForLibrary(...)
    pattern = r"(ClassLoader\s*\*\s*loader\s*=\s*getClassLoaderForLibrary\s*\(\s*library_path\s*\)\s*;)"
    content = re.sub(pattern, r"const \1", content)

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    
    print(f"Patched {file_path}")
    return True

if __name__ == "__main__":
    target = 'src/ros/class_loader/include/class_loader/multi_library_class_loader.hpp'
    if os.path.exists(target):
        patch_file(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
