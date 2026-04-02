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

def patch_sip_helper(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    git_reset(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the dependency issue where it tries to add a dependency on a path
    old_code = '    add_dependencies(${_target_name} ${ARGN})'
    new_code = """    foreach(_dep ${ARGN})
      if(TARGET ${_dep})
        add_dependencies(${_target_name} ${_dep})
      endif()
    endforeach()"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(file_path, 'wb') as f:
            f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
        print(f"Patched {file_path}")
        return True
    return False

def patch_qt_gui_cpp(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    git_reset(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Force Qt6
    old_version = 'set(qt_gui_cpp_USE_QT_MAJOR_VERSION 5 CACHE STRING "The major version of Qt to be used")'
    new_version = 'set(qt_gui_cpp_USE_QT_MAJOR_VERSION 6 CACHE STRING "The major version of Qt to be used")'

    if old_version in content:
        content = content.replace(old_version, new_version)
        with open(file_path, 'wb') as f:
            f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
        print(f"Patched {file_path}")
        return True
    return False

if __name__ == "__main__":
    sip_helper = 'src/ros-visualization/python_qt_binding/cmake/sip_helper.cmake'
    qt_gui_cpp = 'src/ros-visualization/qt_gui_core/qt_gui_cpp/CMakeLists.txt'
    
    patch_sip_helper(sip_helper)
    patch_qt_gui_cpp(qt_gui_cpp)
    sys.exit(0)
