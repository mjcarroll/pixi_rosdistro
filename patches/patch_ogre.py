import sys
import os
import re

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
        os.system(f"cd {pkg_dir} && git checkout -- {rel_path} 2>/dev/null")

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

    # 2. Fix macOS sysroot and architectures quoting
    # We'll use a more robust way to find the SDK path on macOS
    # And ensure architectures are quoted properly
    apple_block = """if(APPLE)
  list(APPEND OGRE_CMAKE_ARGS -DOGRE_ENABLE_PRECOMPILED_HEADERS:BOOL=OFF)
  list(APPEND OGRE_CMAKE_ARGS -DCMAKE_OSX_ARCHITECTURES=arm64;x86_64)
  list(APPEND OGRE_CMAKE_ARGS -DCMAKE_OSX_SYSROOT="")
endif()"""

    new_apple_block = """if(APPLE)
  list(APPEND OGRE_CMAKE_ARGS -DOGRE_ENABLE_PRECOMPILED_HEADERS:BOOL=OFF)
  list(APPEND OGRE_CMAKE_ARGS "-DCMAKE_OSX_ARCHITECTURES=arm64;x86_64")
  # Find actual SDK path to avoid "macosx" broken default
  execute_process(COMMAND xcrun --show-sdk-path OUTPUT_VARIABLE SDK_PATH OUTPUT_STRIP_TRAILING_WHITESPACE)
  list(APPEND OGRE_CMAKE_ARGS "-DCMAKE_OSX_SYSROOT=${SDK_PATH}")
endif()"""

    if apple_block in content:
        content = content.replace(apple_block, new_apple_block)
        print(f"Fixed macOS sysroot and architecture quoting in {path}")
    else:
        # Try a different block if previous patches were applied
        fallback_apple = """if(APPLE)
  list(APPEND OGRE_CMAKE_ARGS -DOGRE_ENABLE_PRECOMPILED_HEADERS:BOOL=OFF)
  list(APPEND OGRE_CMAKE_ARGS -DCMAKE_OSX_ARCHITECTURES=arm64;x86_64)
endif()"""
        if fallback_apple in content:
             content = content.replace(fallback_apple, new_apple_block)
             print(f"Fixed macOS sysroot (fallback) in {path}")

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
