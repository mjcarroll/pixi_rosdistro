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
    # We find the specific pattern and replace the entire if/else/endif block
    include_pattern = r'#ifdef _WIN32\s+#include <windows\.h>\s+#else\s+#include <threads\.h>\s+#endif'
    include_replacement = """#ifdef _WIN32
#include <windows.h>
#elif defined(__APPLE__)
#include <pthread.h>
#else
#include <threads.h>
#endif"""
    if re.search(include_pattern, content):
        content = re.sub(include_pattern, include_replacement, content)
        print(f"Patched include block in {file_path}")

    # 2. Update locale initialization block
    # This block is larger and has more variation. We'll target the #else...#endif part of the _WIN32 check.
    # The original looks like:
    # #else
    # static locale_t c_locale = 0;
    # static once_flag c_locale_once_flag = ONCE_FLAG_INIT;
    # 
    # static void init_c_locale()
    # {
    #   c_locale = newlocale(LC_NUMERIC_MASK, "C", 0);
    # }
    # #endif
    
    locale_block_pattern = r'#else\s+static locale_t c_locale = 0;\s+static once_flag c_locale_once_flag = ONCE_FLAG_INIT;\s+static void init_c_locale\(\)\s+\{\s+c_locale = newlocale\(LC_NUMERIC_MASK, "C", 0\);\s+\}\s+#endif'
    
    locale_block_replacement = """#elif defined(__APPLE__)
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

    if re.search(locale_block_pattern, content):
        content = re.sub(locale_block_pattern, locale_block_replacement, content)
        print(f"Patched locale block in {file_path}")
    else:
        # Try a slightly different pattern if the above fails (e.g. extra newlines)
        # We'll just look for the static once_flag line and the surrounding context
        if 'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;' in content and 'pthread_once_t' not in content:
             # Find the #else before it and the #endif after it
             # This is risky but we can try to be specific
             content = content.replace(
                 'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;',
                 'static once_flag c_locale_once_flag = ONCE_FLAG_INIT;' # No-op just to find it
             )
             # Let's use a very targeted replacement for the lines we know are there
             content = content.replace(
                 '#else\nstatic locale_t c_locale = 0;\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;',
                 '#elif defined(__APPLE__)\nstatic locale_t c_locale = 0;\nstatic pthread_once_t c_locale_once_flag = PTHREAD_ONCE_INIT;\n#else\nstatic locale_t c_locale = 0;\nstatic once_flag c_locale_once_flag = ONCE_FLAG_INIT;'
             )
             print(f"Patched locale block (fallback) in {file_path}")

    # 3. Update call_once usage
    # Original:
    # #else
    #   call_once(&c_locale_once_flag, init_c_locale);
    # #endif
    call_once_pattern = r'#else\s+call_once\(&c_locale_once_flag, init_c_locale\);\s+#endif'
    call_once_replacement = """#elif defined(__APPLE__)
  pthread_once(&c_locale_once_flag, init_c_locale);
#else
  call_once(&c_locale_once_flag, init_c_locale);
#endif"""

    if re.search(call_once_pattern, content):
        content = re.sub(call_once_pattern, call_once_replacement, content)
        print(f"Patched call_once usage in {file_path}")
    else:
        # Targeted string replacement
        if 'call_once(&c_locale_once_flag, init_c_locale);' in content and 'pthread_once' not in content:
            content = content.replace(
                '#else\n  call_once(&c_locale_once_flag, init_c_locale);\n#endif',
                call_once_replacement
            )
            print(f"Patched call_once usage (fallback) in {file_path}")

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
