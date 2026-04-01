import os
import sys

def patch_qt_gui_cpp(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Ensure qt_gui_cpp_USE_QT_MAJOR_VERSION is set to 6
    if 'include(cmake/qt_gui_cpp-extras.cmake)' in content:
        if 'set(qt_gui_cpp_USE_QT_MAJOR_VERSION 6)' not in content:
            content = content.replace(
                'include(cmake/qt_gui_cpp-extras.cmake)',
                'include(cmake/qt_gui_cpp-extras.cmake)\nset(qt_gui_cpp_USE_QT_MAJOR_VERSION 6)'
            )
            print(f"Forced Qt6 in {file_path}")

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

if __name__ == "__main__":
    t1 = 'src/ros-visualization/qt_gui_core/qt_gui_cpp/CMakeLists.txt'
    patch_qt_gui_cpp(t1)
    sys.exit(0)
