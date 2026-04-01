import os
import sys

def patch_class_loader(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix const correctness issue in multi_library_class_loader.hpp
    # Error: cannot initialize a variable of type 'ClassLoader *' with an rvalue of type 'const ClassLoader *'
    
    if 'const ClassLoader * loader = getClassLoaderForLibrary(library_path);' in content:
        print(f"Already patched in {file_path}")
        return True

    old_code = """  template<class Base>
  std::vector<std::string> getAvailableClassesForLibrary(const std::string & library_path) const
  {
    ClassLoader * loader = getClassLoaderForLibrary(library_path);"""
    
    new_code = """  template<class Base>
  std::vector<std::string> getAvailableClassesForLibrary(const std::string & library_path) const
  {
    const ClassLoader * loader = getClassLoaderForLibrary(library_path);"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        print(f"Patched getAvailableClassesForLibrary in {file_path}")
    else:
        # Try a more flexible match in case of whitespace differences
        import re
        pattern = r"(std::vector<std::string> getAvailableClassesForLibrary\(const std::string & library_path\) const\s*\{)\s*(ClassLoader \* loader = getClassLoaderForLibrary\(library_path\);)"
        replacement = r"\1\n    const ClassLoader * loader = getClassLoaderForLibrary(library_path);"
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print(f"Patched getAvailableClassesForLibrary (regex) in {file_path}")
        else:
            print(f"Could not find target code in {file_path}")
            return False

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    
    return True

if __name__ == "__main__":
    target = 'src/ros/class_loader/include/class_loader/multi_library_class_loader.hpp'
    if os.path.exists(target):
        patch_class_loader(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
