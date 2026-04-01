import sys
import os
import re

def patch_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
    with open(path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()
    
    # 1. Minimum policy for CMake 4 compatibility
    if 'set(CMAKE_POLICY_VERSION_MINIMUM 3.5)' not in content:
        content = content.replace('project(rviz_ogre_vendor)', 'project(rviz_ogre_vendor)\n\nset(CMAKE_POLICY_VERSION_MINIMUM 3.5)')
        print(f"Added CMAKE_POLICY_VERSION_MINIMUM to {path}")

    # 2. Add CONFIG_EXTRAS if missing (it should be there, but to be sure)
    if 'CONFIG_EXTRAS "rviz_ogre_vendor-extras.cmake.in"' not in content:
        content = content.replace('ament_package()', 'ament_package(\n  CONFIG_EXTRAS "rviz_ogre_vendor-extras.cmake.in"\n)')
        print(f"Added CONFIG_EXTRAS to {path}")

    with open(path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

def patch_extras(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
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
