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
        content = content.replace(
            '#ifdef _WIN32\n#include <windows.h>\n#else\n#include <threads.h>\n#endif',
            '#ifdef _WIN32\n#include <windows.h>\n#elif defined(__APPLE__)\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif'
        )
        print(f"Patched include block in {file_path}")

    # 2. Update locale initialization block
    # We'll replace the whole block from #ifdef _WIN32 to the end of the locale init
    locale_init_pattern = r'#ifdef _WIN32.*?static void init_c_locale\(.*?\n\{.*?\n\}.*?#else.*?static void init_c_locale\(.*?\n\{.*?\n\}.*?#endif'
    # That's too complex for regex. Let's use markers.
    
    if 'static pthread_once_t c_locale_once_flag' not in content:
        # Find the start of the locale block
        # We know it starts with #ifdef _WIN32 and has c_locale
        # Let's just do a direct replacement of the POSIX part which is the problem
        posix_part = """#else
static locale_t c_locale = 0;
static once_flag c_locale_once_flag = ONCE_FLAG_INIT;

static void init_c_locale()
{
  c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);
}
#endif"""
        
        posix_replacement = """#elif defined(__APPLE__)
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
        if posix_part in content:
            content = content.replace(posix_part, posix_replacement)
            print(f"Patched locale block in {file_path}")

    # 3. Update call site in strtod_locale_independent
    if 'pthread_once(&c_locale_once_flag' not in content:
        call_site_old = """#else
  call_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {"""
        
        call_site_new = """#elif defined(__APPLE__)
  pthread_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {
#else
  call_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {"""
        
        if call_site_old in content:
            content = content.replace(call_site_old, call_site_new)
            print(f"Patched call site in {file_path}")

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    
    return True

if __name__ == "__main__":
    target = 'src/ros2/rcl/rcl_yaml_param_parser/src/parse.c'
    if os.path.exists(target):
        # First reset the file to be sure
        os.system(f"git checkout {target}")
        patch_rcl_yaml_param_parser(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
