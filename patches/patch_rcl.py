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
    # Target:
    # #ifdef _WIN32
    # #include <windows.h>
    # #else
    # #include <threads.h>
    # #endif
    include_old = '#ifdef _WIN32\n#include <windows.h>\n#else\n#include <threads.h>\n#endif'
    include_new = '#ifdef _WIN32\n#include <windows.h>\n#elif defined(__APPLE__)\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif'
    if include_old in content:
        content = content.replace(include_old, include_new)
        print(f"Patched include block in {file_path}")

    # 2. Update locale initialization block
    # Target:
    # #else
    # static locale_t c_locale = 0;
    # static once_flag c_locale_once_flag = ONCE_FLAG_INIT;
    # 
    # static void init_c_locale()
    # {
    #   c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);
    # }
    # #endif
    
    # We'll use a more flexible replacement for the POSIX part
    posix_old = '#else\nstatic locale_t c_locale = 0;\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;\n\nstatic void init_c_locale()\n{\n  c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);\n}\n#endif'
    posix_new = """#elif defined(__APPLE__)
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
    if posix_old in content:
        content = content.replace(posix_old, posix_new)
        print(f"Patched locale initialization block in {file_path}")
    else:
        # Try a version with potentially different whitespace/newlines
        pattern = r'#else\s+static locale_t c_locale = 0;\s+static once_flag c_locale_once_flag = ONCE_FLAG_INIT;\s+static void init_c_locale\(\)\s+\{\s+c_locale = newlocale\(LC_NUMERIC_MASK, "C", 0\);\s+\}\s+#endif'
        if re.search(pattern, content):
            content = re.sub(pattern, posix_new, content)
            print(f"Patched locale initialization block (regex) in {file_path}")

    # 3. Update call_once usage
    # Target:
    # #else
    #   call_once(&c_locale_once_flag, init_c_locale);
    # 
    #   if (0 == c_locale) {
    call_usage_old = '#else\n  call_once(&c_locale_once_flag, init_c_locale);\n\n  if (0 == c_locale) {'
    call_usage_new = """#elif defined(__APPLE__)
  pthread_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {
#else
  call_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {"""
    if call_usage_old in content:
        content = content.replace(call_usage_old, call_usage_new)
        print(f"Patched call_once usage in {file_path}")
    else:
        pattern = r'#else\s+call_once\(&c_locale_once_flag, init_c_locale\);\s+if \(0 == c_locale\) \{'
        if re.search(pattern, content):
            content = re.sub(pattern, call_usage_new, content)
            print(f"Patched call_once usage (regex) in {file_path}")

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
