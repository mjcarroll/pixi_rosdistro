import sys
import os
import re
import subprocess

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

def get_sdk_path():
    try:
        result = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        return ""

def patch_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
    git_reset(path)

    with open(path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()
    
    # 1. Minimum policy
    if 'set(CMAKE_POLICY_VERSION_MINIMUM 3.5)' not in content:
        content = content.replace('project(rviz_ogre_vendor)', 'project(rviz_ogre_vendor)\n\nset(CMAKE_POLICY_VERSION_MINIMUM 3.5)')

    # 2. Fix macOS sysroot aggressively
    sdk_path = get_sdk_path()
    if not sdk_path:
        # Fallback to a common path if xcrun fails
        sdk_path = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk"

    # Define the new block with the correct SDK path and quoted architectures
    new_apple_block = f"""if(APPLE)
  list(APPEND OGRE_CMAKE_ARGS -DOGRE_ENABLE_PRECOMPILED_HEADERS:BOOL=OFF)
  list(APPEND OGRE_CMAKE_ARGS "-DCMAKE_OSX_ARCHITECTURES=arm64;x86_64")
  list(APPEND OGRE_CMAKE_ARGS "-DCMAKE_OSX_SYSROOT={sdk_path}")
endif()"""

    # Replace variations of the apple block
    pattern = r"if\(APPLE\).*?endif\(\)"
    content = re.sub(pattern, new_apple_block, content, flags=re.DOTALL)
    
    # Also ensure we don't have -isysroot macosx anywhere
    content = content.replace("-isysroot macosx", f"-isysroot {sdk_path}")

    with open(path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    print(f"Patched {path} for macOS with SDK: {sdk_path}")
    return True

def patch_extras(path):
    if not os.path.exists(path):
        return False
    git_reset(path)
    with open(path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()
    conda_fix = """
# Add Conda prefix to search paths for dependencies
if(NOT "$ENV{CONDA_PREFIX}" STREQUAL "")
  list(APPEND CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}")
endif()
"""
    if 'CONDA_PREFIX' not in content:
        content = conda_fix + content
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
