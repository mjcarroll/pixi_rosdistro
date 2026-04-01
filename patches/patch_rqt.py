import os
import sys

def patch_rqt_gui_cpp(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add missing #include <unistd.h> for getpid() on Unix
    if 'getpid()' in content and '#include <unistd.h>' not in content:
        # Insert after #include <string> or similar
        if '#include <string>' in content:
            content = content.replace('#include <string>', '#include <string>\n#ifndef _WIN32\n# include <unistd.h>\n#endif')
            print(f"Patched {file_path} with unistd.h")
        else:
            # Just prepend it
            content = "#ifndef _WIN32\n# include <unistd.h>\n#endif\n" + content
            print(f"Prepended unistd.h to {file_path}")

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

if __name__ == "__main__":
    t1 = 'src/ros-visualization/rqt/rqt_gui_cpp/src/rqt_gui_cpp/nodelet_plugin_provider.cpp'
    patch_rqt_gui_cpp(t1)
    sys.exit(0)
