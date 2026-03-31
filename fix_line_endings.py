import os

def fix_line_endings(directory):
    print(f"Checking directory: {directory}")
    extensions = ('.sh', '.dsv', '.in', '.py', '.cmake', 'package.xml')
    for root, dirs, files in os.walk(directory):
        # Skip some directories to be safe
        if '.git' in dirs:
            dirs.remove('.git')
        if '.pixi' in dirs:
            dirs.remove('.pixi')
            
        for file in files:
            if file.endswith(extensions) or file == 'CMakeLists.txt' or file == 'package.xml':
                path = os.path.join(root, file)
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                    
                    # Replace CRLF with LF
                    new_content = content.replace(b'\r\n', b'\n')
                    
                    if new_content != content:
                        print(f"Fixing line endings: {path}")
                        with open(path, 'wb') as f:
                            f.write(new_content)
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    # Fix files in root, patches, and src
    for target in ['.', 'patches', 'src']:
        if os.path.exists(target):
            fix_line_endings(target)
