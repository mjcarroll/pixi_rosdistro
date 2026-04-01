import os
import re
import sys

def patch_rcl_yaml_param_parser(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # We will use a more robust way to patch. 
    # We will look for the specific problematic lines and replace them with platform-specific ones.
    
    # 1. Include block
    # Original:
    # #ifdef _WIN32
    # #include <windows.h>
    # #else
    # #include <threads.h>
    # #endif
    if '#include <threads.h>' in content and 'pthread.h' not in content:
        # Use regex to replace the whole block regardless of whitespace
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

    # 2. Locale initialization block
    # We'll look for the static once_flag line and the surrounding context
    if 'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;' in content and 'pthread_once_t' not in content:
        # We'll replace the POSIX part of the block
        # Look for the #else ... #endif that contains our target
        pattern = r'#else\s+static locale_t c_locale = 0;\s+static once_flag c_locale_once_flag = ONCE_FLAG_INIT;\s+static void init_c_locale\(\)\s+\{\s+c_locale = newlocale\(LC_NUMERIC_MASK, "C", 0\);\s+\}\s+#endif'
        replacement = """#elif defined(__APPLE__)
static locale_t c_locale = 0;
static pthread_once_t c_locale_once_flag = PTHREAD_ONCE_INIT;

static void init_c_locale()
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
        content = re.sub(pattern, replacement, content)
        print(f"Patched locale block in {file_path}")

    # 3. call_once usage
    if 'call_once(&c_locale_once_flag, init_c_locale);' in content and 'pthread_once' not in content:
        pattern = r'#else\s+call_once\(&c_locale_once_flag, init_c_locale\);\s+#endif'
        replacement = """#elif defined(__APPLE__)
  pthread_once(&c_locale_once_flag, init_c_locale);
#else
  call_once(&c_locale_once_flag, init_c_locale);
#endif"""
        content = re.sub(pattern, replacement, content)
        print(f"Patched call_once usage in {file_path}")

    # Final sanity check: make sure we didn't end up with #elif after #else
    # This can happen if we did multiple replacements or if the file was already partially patched.
    # We'll just fix it by ensuring only one #else exists in these blocks.
    # Actually, the regex approach above should prevent this if it matches correctly.

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
