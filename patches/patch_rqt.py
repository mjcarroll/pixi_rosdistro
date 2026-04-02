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

    # Add unistd.h for getpid()
    old_code = '#include <rclcpp/rclcpp.hpp>'
    new_code = '#include <rclcpp/rclcpp.hpp>\n#ifndef _WIN32\n# include <unistd.h>\n#endif'

    if old_code in content and 'unistd.h' not in content:
        content = content.replace(old_code, new_code)
        with open(file_path, 'wb') as f:
            f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
        print(f"Patched {file_path} with unistd.h")
        return True
    
    return False

if __name__ == "__main__":
    target = 'src/ros-visualization/rqt/rqt_gui_cpp/src/rqt_gui_cpp/nodelet_plugin_provider.cpp'
    if os.path.exists(target):
        patch_file(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
