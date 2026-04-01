import os
import sys

def patch_qt_gui_cpp(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Force Qt6 in CMakeLists.txt if using the ahcorde branch
    if 'include(cmake/qt_gui_cpp-extras.cmake)' in content:
        content = content.replace(
            'include(cmake/qt_gui_cpp-extras.cmake)',
            'include(cmake/qt_gui_cpp-extras.cmake)\nif(NOT qt_gui_cpp_USE_QT_MAJOR_VERSION)\n  set(qt_gui_cpp_USE_QT_MAJOR_VERSION 6)\nendif()'
        )
        print(f"Forced Qt6 in {file_path}")

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

def patch_qt_gui_cpp_sip(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. Redirect build_sip_binding to build_sip_6_binding for Qt6
    # In src/qt_gui_cpp_sip/CMakeLists.txt
    if 'build_sip_binding' in content and 'build_sip_6_binding' not in content:
        content = content.replace(
            'build_sip_binding(',
            'if(${qt_gui_cpp_USE_QT_MAJOR_VERSION} EQUAL 6)\n    build_sip_6_binding(\n  else()\n    build_sip_binding(\n  endif('
        )
        # Note: This is a bit complex because of the arguments.
        # Let's try a simpler replacement that just swaps the name if major version is 6.
        content = content.replace(
            'build_sip_binding(qt_gui_cpp_sip',
            'set(_build_func "build_sip_binding")\n  if(${qt_gui_cpp_USE_QT_MAJOR_VERSION} EQUAL 6)\n    set(_build_func "build_sip_6_binding")\n  endif()\n  cmake_language(CALL ${_build_func} qt_gui_cpp_sip'
        )
        print(f"Patched build_sip_binding in {file_path}")

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    return True

if __name__ == "__main__":
    t1 = 'src/ros-visualization/qt_gui_core/qt_gui_cpp/CMakeLists.txt'
    t2 = 'src/ros-visualization/qt_gui_core/qt_gui_cpp/src/qt_gui_cpp_sip/CMakeLists.txt'
    
    p1 = patch_qt_gui_cpp(t1)
    p2 = patch_qt_gui_cpp_sip(t2)
    
    if p1 or p2:
        sys.exit(0)
    else:
        sys.exit(0)
