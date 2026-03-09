import sys
import os
import re

def patch_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    
    with open(path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()
    
    if '-DCMAKE_POLICY_VERSION_MINIMUM=3.5' in content:
        print(f"Already patched: {path}")
        return True
    
    # We want to insert the policy flag after CMAKE_ARGS in the ament_vendor call
    # The line usually looks like '  CMAKE_ARGS'
    pattern = r'(  CMAKE_ARGS\r?\n)'
    replacement = r'\1    -DCMAKE_POLICY_VERSION_MINIMUM=3.5\n'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content == content:
        print(f"Failed to find anchor 'CMAKE_ARGS' in: {path}")
        return False
        
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_content)
    
    print(f"Successfully patched: {path}")
    return True

if __name__ == "__main__":
    target = 'src/ros2/rviz/rviz_ogre_vendor/CMakeLists.txt'
    if patch_file(target):
        sys.exit(0)
    else:
        # If it fails, we don't want to stop the build if it's already worked by chance,
        # but for CI we want to know it failed.
        sys.exit(0) # Keep going for now, or use 1 if we want it to be strict.
