import os
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

def patch_ogre_vendor(cmakelists_path):
    if not os.path.exists(cmakelists_path):
        return

    git_reset(cmakelists_path)

    # Resolve SDK path on macOS
    sdk_path = "macosx" # default fallback
    try:
        result = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True)
        if result.returncode == 0:
            sdk_path = result.stdout.strip()
            print(f"Resolved macOS SDK path: {sdk_path}")
    except Exception as e:
        print(f"Failed to run xcrun: {e}")

    with open(cmakelists_path, "r") as f:
        content = f.read()

    # Force the sysroot if on macOS (or just always if we resolved it)
    if sdk_path and sdk_path != "macosx":
        patch_logic = f'\nif(APPLE)\n  set(CMAKE_OSX_SYSROOT "{sdk_path}" CACHE PATH "" FORCE)\nendif()\n'
        if "CMAKE_OSX_SYSROOT" not in content:
            content = content.replace("project(rviz_ogre_vendor)", "project(rviz_ogre_vendor)" + patch_logic)

    with open(cmakelists_path, "w") as f:
        f.write(content)
    
    print(f"Patched {cmakelists_path}")

if __name__ == "__main__":
    target = "src/ros2/rviz/rviz_ogre_vendor/CMakeLists.txt"
    if os.path.exists(target):
        patch_ogre_vendor(target)
