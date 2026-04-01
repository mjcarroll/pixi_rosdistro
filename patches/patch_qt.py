import os
import sys

def patch_qt_gui_cpp(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Force Qt6 if the version variable is missing or empty
    # The ahcorde branch uses find_package(Qt${qt_gui_cpp_USE_QT_MAJOR_VERSION} ...)
    if 'include(cmake/qt_gui_cpp-extras.cmake)' in content:
        content = content.replace(
            'include(cmake/qt_gui_cpp-extras.cmake)',
            'include(cmake/qt_gui_cpp-extras.cmake)\nif(NOT qt_gui_cpp_USE_QT_MAJOR_VERSION)\n  set(qt_gui_cpp_USE_QT_MAJOR_VERSION 6)\nendif()'
        )
        print(f"Forced Qt6 in {file_path}")

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

if __name__ == "__main__":
    target = 'src/ros-visualization/qt_gui_core/qt_gui_cpp/CMakeLists.txt'
    if os.path.exists(target):
        patch_qt_gui_cpp(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
