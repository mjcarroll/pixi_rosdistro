import os
import sys

def patch_rcl_yaml_param_parser(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update include block
    # Simple and direct
    old_include = '#ifdef _WIN32\n#include <windows.h>\n#else\n#include <threads.h>\n#endif'
    new_include = '#ifdef _WIN32\n#include <windows.h>\n#elif defined(__APPLE__)\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif'
    if old_include in content:
        content = content.replace(old_include, new_include)
        print(f"Patched include in {file_path}")

    # 2. Update locale init block
    # The ahcorde branch has this specific block
    old_init = """#else
static locale_t c_locale = 0;
static once_flag c_locale_once_flag = ONCE_FLAG_INIT;

static void init_c_locale()
{
  c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);
}
#endif"""

    new_init = """#elif defined(__APPLE__)
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
    if old_init in content:
        content = content.replace(old_init, new_init)
        print(f"Patched init in {file_path}")

    # 3. Update call site
    old_call = """#else
  call_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {"""
    
    new_call = """#elif defined(__APPLE__)
  pthread_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {
#else
  call_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {"""
    if old_call in content:
        content = content.replace(old_call, new_call)
        print(f"Patched call site in {file_path}")

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
