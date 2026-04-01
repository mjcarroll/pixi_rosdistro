import os
import re
import sys

def patch_rcl_yaml_param_parser(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update include block
    # We'll be very aggressive and just replace the whole block if we find the key parts
    if '#include <threads.h>' in content and 'pthread.h' not in content:
        content = re.sub(
            r'#ifdef _WIN32\s+#include <windows\.h>\s+#else\s+#include <threads\.h>\s+#endif',
            '#ifdef _WIN32\n#include <windows.h>\n#elif defined(__APPLE__)\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif',
            content
        )
        print(f"Patched include block in {file_path}")

    # 2. Update once_flag definition
    # Look for the POSIX part specifically
    if 'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;' in content and 'pthread_once_t' not in content:
        content = content.replace(
            'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;',
            '#elif defined(__APPLE__)\nstatic pthread_once_t c_locale_once_flag = PTHREAD_ONCE_INIT;\n#else\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;\n#endif'
        )
        # Note: This might leave a dangling #else or duplicate #else if not careful.
        # Let's use a cleaner approach: find the POSIX block and replace it.
        content = re.sub(
            r'#else\s+static locale_t c_locale = 0;\s+static once_flag c_locale_once_flag = ONCE_FLAG_INIT;',
            '#elif defined(__APPLE__)\nstatic locale_t c_locale = 0;\nstatic pthread_once_t c_locale_once_flag = PTHREAD_ONCE_INIT;\n#else\nstatic locale_t c_locale = 0;\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;',
            content
        )
        print(f"Patched once_flag definition in {file_path}")

    # 3. Update call_once usage
    if 'call_once(&c_locale_once_flag, init_c_locale);' in content and 'pthread_once' not in content:
        content = content.replace(
            'call_once(&c_locale_once_flag, init_c_locale);',
            '#elif defined(__APPLE__)\n  pthread_once(&c_locale_once_flag, init_c_locale);\n#else\n  call_once(&c_locale_once_flag, init_c_locale);\n#endif'
        )
        # Again, clean up the surrounding block logic
        content = re.sub(
            r'#else\s+call_once\(&c_locale_once_flag, init_c_locale\);',
            '#elif defined(__APPLE__)\n  pthread_once(&c_locale_once_flag, init_c_locale);\n#else\n  call_once(&c_locale_once_flag, init_c_locale);',
            content
        )
        print(f"Patched call_once usage in {file_path}")

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    
    return True

if __name__ == "__main__":
    target = 'src/ros2/rcl/rcl_yaml_param_parser/src/parse.c'
    if os.path.exists(target):
        patch_rcl_yaml_param_parser(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
