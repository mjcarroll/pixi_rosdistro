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
    # Using more flexible regex to find the include block
    include_pattern = r'#ifdef _WIN32\s+#include <windows\.h>\s+#else\s+#include <threads\.h>\s+#endif'
    include_replacement = '#ifdef _WIN32\n#include <windows.h>\n#elif defined(__APPLE__)\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif'
    
    if re.search(include_pattern, content):
        content = re.sub(include_pattern, include_replacement, content)
        print(f"Patched include block in {file_path}")
    elif '#include <threads.h>' in content and '#elif defined(__APPLE__)' not in content:
        # Fallback for direct string replacement if regex fails
        content = content.replace(
            '#ifdef _WIN32\n#include <windows.h>\n#else\n#include <threads.h>\n#endif',
            include_replacement
        )
        print(f"Patched include block (fallback) in {file_path}")

    # 2. Update once_flag definition
    once_flag_pattern = r'#else\s+static once_flag c_locale_once_flag = ONCE_FLAG_INIT;\s+#endif'
    once_flag_replacement = '#elif defined(__APPLE__)\nstatic pthread_once_t c_locale_once_flag = PTHREAD_ONCE_INIT;\n#else\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;\n#endif'
    
    if re.search(once_flag_pattern, content):
        content = re.sub(once_flag_pattern, once_flag_replacement, content)
        print(f"Patched once_flag definition in {file_path}")
    elif 'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;' in content and '#elif defined(__APPLE__)' not in content:
        content = content.replace(
            '#else\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;\n#endif',
            once_flag_replacement
        )
        print(f"Patched once_flag definition (fallback) in {file_path}")

    # 3. Update call_once execution
    call_once_pattern = r'#else\s+call_once\(&c_locale_once_flag, init_c_locale\);\s+#endif'
    call_once_replacement = '#elif defined(__APPLE__)\n  pthread_once(&c_locale_once_flag, init_c_locale);\n#else\n  call_once(&c_locale_once_flag, init_c_locale);\n#endif'
    
    if re.search(call_once_pattern, content):
        content = re.sub(call_once_pattern, call_once_replacement, content)
        print(f"Patched call_once execution in {file_path}")
    elif 'call_once(&c_locale_once_flag, init_c_locale);' in content and 'pthread_once' not in content:
        # Use a more targeted replacement if it's within the block
        content = content.replace(
            '#else\n  call_once(&c_locale_once_flag, init_c_locale);\n#endif',
            call_once_replacement
        )
        print(f"Patched call_once execution (fallback) in {file_path}")
        
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
