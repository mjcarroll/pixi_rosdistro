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
    if '#include <threads.h>' in content and 'pthread.h' not in content:
        pattern = r'#ifdef _WIN32\s+#include <windows\.h>\s+#else\s+#include <threads\.h>\s+#endif'
        replacement = """#ifdef _WIN32
#include <windows.h>
#elif defined(__APPLE__)
#include <pthread.h>
#else
#include <threads.h>
#endif"""
        content = re.sub(pattern, replacement, content)
        print(f"Patched include block in {file_path}")

    # 2. Update locale initialization block
    # We will look for the specific lines and replace them
    if 'static once_flag c_locale_once_flag' in content and 'pthread_once_t' not in content:
        # Replacement for the initialization part
        old_part = """#else
static locale_t c_locale = 0;
static once_flag c_locale_once_flag = ONCE_FLAG_INIT;

static void init_c_locale()
{
  c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);
}
#endif"""
        
        new_part = """#elif defined(__APPLE__)
static locale_t c_locale = 0;
static pthread_once_t c_locale_once_flag = PTHREAD_ONCE_INIT;

static void init_c_locale(void)
{
  c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);
}
#else
static locale_t c_locale = 0;
static once_flag c_locale_once_flag = ONCE_FLAG_INIT;

static void init_c_locale()
{
  c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);
}
#endif"""
        # Try direct replacement first
        if old_part in content:
            content = content.replace(old_part, new_part)
        else:
            # Try a regex if there are whitespace differences
            pattern = r'#else\s+static locale_t c_locale = 0;\s+static once_flag c_locale_once_flag = ONCE_FLAG_INIT;\s+static void init_c_locale\(\)\s+\{\s+c_locale = newlocale\(LC_NUMERIC_MASK, "C", 0\);\s+\}\s+#endif'
            content = re.sub(pattern, new_part, content)
        print(f"Patched locale block in {file_path}")

    # 3. Update call_once usage in strtod_locale_independent
    if 'call_once(&c_locale_once_flag, init_c_locale);' in content and 'pthread_once' not in content:
        old_call = """#else
  call_once(&c_locale_once_flag, init_c_locale);
#endif"""
        new_call = """#elif defined(__APPLE__)
  pthread_once(&c_locale_once_flag, init_c_locale);
#else
  call_once(&c_locale_once_flag, init_c_locale);
#endif"""
        if old_call in content:
            content = content.replace(old_call, new_call)
        else:
            pattern = r'#else\s+call_once\(&c_locale_once_flag, init_c_locale\);\s+#endif'
            content = re.sub(pattern, new_call, content)
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
