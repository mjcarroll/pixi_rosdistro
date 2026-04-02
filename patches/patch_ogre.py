import sys
import os
import re

def git_reset(path):
    pkg_dir = path if os.path.isdir(path) else os.path.dirname(path)
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

    with open(path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()
    
    # 1. Minimum policy for CMake 4 compatibility
    if 'set(CMAKE_POLICY_VERSION_MINIMUM 3.5)' not in content:
        content = content.replace('project(rviz_ogre_vendor)', 'project(rviz_ogre_vendor)\n\nset(CMAKE_POLICY_VERSION_MINIMUM 3.5)')
        print(f"Added CMAKE_POLICY_VERSION_MINIMUM to {path}")

    # 2. Fix macOS sysroot issue
    # We want to force CMAKE_OSX_SYSROOT to empty to avoid "macosx" being used.
    if 'DCMAKE_OSX_SYSROOT=""' not in content:
        content = content.replace(
            'list(APPEND OGRE_CMAKE_ARGS -DCMAKE_OSX_ARCHITECTURES=arm64;x86_64)',
            'list(APPEND OGRE_CMAKE_ARGS -DCMAKE_OSX_ARCHITECTURES=arm64;x86_64)\n  list(APPEND OGRE_CMAKE_ARGS -DCMAKE_OSX_SYSROOT="")'
        )
        print(f"Fixed macOS sysroot in {path}")

    with open(path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

def patch_extras(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
    git_reset(path)

    with open(path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()
    
    # Add Conda prefix to search path for macOS/Linux dependencies like console_bridge, tinyxml2
    conda_fix = """
# Add Conda prefix to search paths for dependencies
if(NOT "$ENV{CONDA_PREFIX}" STREQUAL "")
  list(APPEND CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}")
endif()
"""
    if 'CONDA_PREFIX' not in content:
        content = conda_fix + content
        print(f"Added CONDA_PREFIX fix to {path}")

    with open(path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

if __name__ == "__main__":
    target_cmake = 'src/ros2/rviz/rviz_ogre_vendor/CMakeLists.txt'
    target_extras = 'src/ros2/rviz/rviz_ogre_vendor/rviz_ogre_vendor-extras.cmake.in'
    
    p1 = patch_file(target_cmake)
    p2 = patch_extras(target_extras)
    
    if p1 or p2:
        print("Successfully patched rviz_ogre_vendor")
        sys.exit(0)
    else:
        sys.exit(0)
