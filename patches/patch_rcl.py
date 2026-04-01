import os
import re
import sys

def patch_rcl_yaml_param_parser(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update include
    if '#include <threads.h>' in content and '#include <pthread.h>' not in content:
        content = content.replace(
            '#ifdef _WIN32\n#include <windows.h>\n#else\n#include <threads.h>\n#endif',
            '#ifdef _WIN32\n#include <windows.h>\n#elif defined(__APPLE__)\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif'
        )
        print(f"Patched include in {file_path}")

    # 2. Update once_flag definition
    if 'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;' in content:
        content = content.replace(
            '#else\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;\n#endif',
            '#elif defined(__APPLE__)\nstatic pthread_once_t c_locale_once_flag = PTHREAD_ONCE_INIT;\n#else\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;\n#endif'
        )
        print(f"Patched once_flag definition in {file_path}")

    # 3. Update call_once execution
    if 'call_once(&c_locale_once_flag, init_c_locale);' in content:
        content = content.replace(
            '#else\n  call_once(&c_locale_once_flag, init_c_locale);\n#endif',
            '#elif defined(__APPLE__)\n  pthread_once(&c_locale_once_flag, init_c_locale);\n#else\n  call_once(&c_locale_once_flag, init_c_locale);\n#endif'
        )
        print(f"Patched call_once execution in {file_path}")
        
    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    
    return True

if __name__ == "__main__":
    target = 'src/ros2/rcl/rcl_yaml_param_parser/src/parse.c'
    if os.path.exists(target):
        patch_rcl_yaml_param_parser(target)
    else:
        # We don't fail if the file is not there, maybe it hasn't been fetched yet
        print(f"Target not found: {target}")
    sys.exit(0)
