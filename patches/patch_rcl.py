import os
import re
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

    # 1. Include block
    old_include = '#ifdef _WIN32\n#include <windows.h>\n#else\n#include <threads.h>\n#endif'
    new_include = '#ifdef _WIN32\n#include <windows.h>\n#elif defined(__APPLE__)\n#include <pthread.h>\n#else\n#include <threads.h>\n#endif'
    if old_include in content:
        content = content.replace(old_include, new_include)

    # 2. Locale init block
    # Match the static block precisely
    pattern_init = r"static void init_c_locale\(\)\s*\{(?:.|\n)*?newlocale\(LC_NUMERIC_MASK, \"C\", 0\);\s*\}"
    new_init_full = """#elif defined(__APPLE__)
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

    # We need to replace the variables and the function
    var_pattern = r"static locale_t c_locale = 0;\s*static once_flag c_locale_once_flag = ONCE_FLAG_INIT;"
    content = re.sub(var_pattern, "", content)
    content = re.sub(pattern_init, new_init_full, content)

    # 3. Function body for strtod_locale_independent
    func_pattern = r"double\s+strtod_locale_independent\((?:.|\n)*?#else\s+call_once\(&c_locale_once_flag, init_c_locale\);(?:.|\n)*?return result;\s+#endif\s+\}"
    
    new_func = """double
strtod_locale_independent(const char * nptr, char ** endptr)
{
#ifdef _WIN32
  static _locale_t c_locale = _create_locale(LC_NUMERIC, "C");
  return _strtod_l(nptr, endptr, c_locale);
#elif defined(__APPLE__)
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
#endif
}"""
    content = re.sub(func_pattern, new_func, content)

    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))
    
    print(f"Patched {file_path}")
    return True

if __name__ == "__main__":
    target = 'src/ros2/rcl/rcl_yaml_param_parser/src/parse.c'
    if os.path.exists(target):
        patch_rcl_yaml_param_parser(target)
    else:
        print(f"Target not found: {target}")
    sys.exit(0)
