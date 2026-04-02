import os
import subprocess
import sys

def git_reset(path):
    pkg_dir = os.path.dirname(path)
    while pkg_dir and not os.path.exists(os.path.join(pkg_dir, '.git')):
        next_dir = os.path.dirname(pkg_dir)
        if next_dir == pkg_dir:
            pkg_dir = None
            break
        pkg_dir = next_dir
    if pkg_dir:
        rel_path = os.path.relpath(path, pkg_dir)
        subprocess.run(["git", "checkout", "--", rel_path], cwd=pkg_dir, capture_output=True)

def patch_rcl_yaml_param_parser(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    git_reset(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update include block
    old_include = '#include <threads.h>'
    new_include = '#ifdef __APPLE__\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif'
    # We only want to replace the ONE in the #else block
    # The original is:
    # #ifdef _WIN32
    # #include <windows.h>
    # #else
    # #include <threads.h>
    # #endif
    full_old_include = '#ifdef _WIN32\n#include <windows.h>\n#else\n#include <threads.h>\n#endif'
    full_new_include = '#ifdef _WIN32\n#include <windows.h>\n#elif defined(__APPLE__)\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif'
    if full_old_include in content:
        content = content.replace(full_old_include, full_new_include)
        print("Patched include block")

    # 2. Update initialization block
    # Original:
    # #else
    # static locale_t c_locale = 0;
    # static once_flag c_locale_once_flag = ONCE_FLAG_INIT;
    #
    # static void init_c_locale()
    # {
    #   c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);
    # }
    # #endif
    
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
        print("Patched init block")

    # 3. Update call site
    # Original:
    # #else
    #   call_once(&c_locale_once_flag, init_c_locale);
    #
    #   if (0 == c_locale) {
    
    old_call = """#else
  call_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {"""

    new_call = """#elif defined(__APPLE__)
  pthread_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {
    if (NULL != endptr) {
      *endptr = (char *)nptr;
    }
    return 0.;
  }

  locale_t old_locale = uselocale(c_locale);
  double result = strtod(nptr, endptr);
  uselocale(old_locale);
  return result;
#else
  call_once(&c_locale_once_flag, init_c_locale);

  if (0 == c_locale) {"""
    
    if old_call in content:
        content = content.replace(old_call, new_call)
        print("Patched call block")

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    
    return True

if __name__ == "__main__":
    target = 'src/ros2/rcl/rcl_yaml_param_parser/src/parse.c'
    if os.path.exists(target):
        patch_rcl_yaml_param_parser(target)
    sys.exit(0)
