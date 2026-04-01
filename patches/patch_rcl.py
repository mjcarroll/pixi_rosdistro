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
    # Target the #else...#endif block containing init_c_locale
    locale_pattern = r'#else\s+static locale_t c_locale = 0;\s+static once_flag c_locale_once_flag = ONCE_FLAG_INIT;\s+static void init_c_locale\(\)\s+\{\s+c_locale = newlocale\(LC_NUMERIC_MASK, "C", 0\);\s+\}\s+#endif'
    
    locale_replacement = """#elif defined(__APPLE__)
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

    if re.search(locale_pattern, content):
        content = re.sub(locale_pattern, locale_replacement, content)
        print(f"Patched locale block in {file_path}")
    elif 'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;' in content and 'pthread_once_t' not in content:
        # Fallback for simpler match
        content = content.replace(
            '#else\nstatic locale_t c_locale = 0;\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;',
            '#elif defined(__APPLE__)\nstatic locale_t c_locale = 0;\nstatic pthread_once_t c_locale_once_flag = PTHREAD_ONCE_INIT;\n#else\nstatic locale_t c_locale = 0;\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;'
        )
        print(f"Patched locale block (fallback) in {file_path}")

    # 3. Update call site in strtod_locale_independent
    # Look for the #else block that calls call_once
    # Original:
    # #else
    #   call_once(&c_locale_once_flag, init_c_locale);
    #
    #   if (0 == c_locale) {
    call_pattern = r'#else\s+call_once\(&c_locale_once_flag, init_c_locale\);\s+if \(0 == c_locale\) \{'
    
    call_replacement = """#elif defined(__APPLE__)
  pthread_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {
#else
  call_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {"""

    if re.search(call_pattern, content):
        content = re.sub(call_pattern, call_replacement, content)
        print(f"Patched call site in {file_path}")
    elif 'call_once(&c_locale_once_flag, init_c_locale);' in content and 'pthread_once' not in content:
        # Direct string replacement fallback
        content = content.replace(
            '#else\n  call_once(&c_locale_once_flag, init_c_locale);\n\n  if (0 == c_locale) {',
            call_replacement
        )
        print(f"Patched call site (fallback) in {file_path}")

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
