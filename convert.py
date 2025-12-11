
# convert_to_windows.py
# Usage: python convert_to_windows.py
# Reads /mnt/data/Stock_Sim.py and writes ./Stock_Sim_windows.py (in current directory).
# Make a backup of your original before running if you like.

import re
import io
import os
import sys

SRC = "Stock_Sim.py"   # path where you uploaded the file
DST = "Stock_Sim_windows.py"     # output file to run on Windows

if not os.path.exists(SRC):
    print(f"Source file not found: {SRC}")
    sys.exit(1)

with io.open(SRC, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

# 1) Remove Unix-only imports (tty, termios, select) and add msvcrt import + helpers
# Replace combined import lines that contain tty/termios/select
text = re.sub(r"import\s+sys\s*,\s*time\s*,\s*random\s*,\s*tty\s*,\s*termios\s*,\s*select", 
              "import sys, time, random", text)

# Remove separate imports of tty, termios, select
text = re.sub(r"^\s*import\s+tty\s*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*import\s+termios\s*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*import\s+select\s*$", "", text, flags=re.MULTILINE)

# If there is any "from select import ..." or "from tty import ..." remove those
text = re.sub(r"^\s*from\s+tty\s+import\s+.*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*from\s+termios\s+import\s+.*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*from\s+select\s+import\s+.*$", "", text, flags=re.MULTILINE)

# 2) Insert Windows imports & helper functions near top of file (after other imports).
# Find first occurrence of a large import block and append our msvcrt helpers after it.
insertion_point = None
m = re.search(r"(?:from\s+matplotlib|import\s+matplotlib|import\s+numpy|import\s+random)", text)
if m:
    insertion_point = m.end()
else:
    # fallback to start of file
    insertion_point = 0

windows_helpers = r"""

# --- WINDOWS CONSOLE ADAPTATION ---
# Replaced Unix-only terminal handling with msvcrt (Windows)
try:
    import msvcrt
except Exception:
    msvcrt = None

def windows_getch():
    if msvcrt is None:
        raise RuntimeError("msvcrt not available. This script expects to run on Windows.")
    ch = msvcrt.getwch()
    return ch

def windows_kbhit():
    if msvcrt is None:
        return False
    return msvcrt.kbhit()

def windows_readline_nonblocking(timeout=0.0):
    if msvcrt is None:
        return ""
    import time as _time
    start = _time.time()
    s = ""
    while True:
        if msvcrt.kbhit():
            c = msvcrt.getwch()
            # translate CR to newline
            if c == '\\r':
                c = '\\n'
            s += c
            # if user pressed Enter, stop
            if c == '\\n':
                break
        if timeout > 0 and (_time.time() - start) >= timeout:
            break
    return s

# End Windows helpers
"""

# Insert helpers into text
text = text[:insertion_point] + windows_helpers + text[insertion_point:]

# 3) Replace common Unix low-level terminal function calls with Windows-friendly no-ops or wrappers.
# Replace tty.setraw(...) or termios.tcgetattr(...) style calls with harmless comments or pass
text = re.sub(r"tty\.setraw\([^\)]*\)", "pass  # tty.setraw replaced for Windows", text)
text = re.sub(r"tty\.setcbreak\([^\)]*\)", "pass  # tty.setcbreak replaced for Windows", text)
text = re.sub(r"termios\.tcgetattr\([^\)]*\)", "None  # termios.tcgetattr removed for Windows", text)
text = re.sub(r"termios\.tcsetattr\([^\)]*\)", "pass  # termios.tcsetattr removed for Windows", text)

# 4) Replace select.select(...) checks on sys.stdin with msvcrt.kbhit() checks
# Common pattern: select.select([sys.stdin], [], [], timeout)
text = re.sub(r"select\.select\(\s*\[sys\.stdin\]\s*,\s*\[\]\s*,\s*\[\]\s*,\s*([^\)]+)\)",
              r"( [0] if msvcrt is None else (msvcrt.kbhit(),) )", text)

# 5) Replace uses of sys.stdin.read(1) or sys.stdin.read(...) with windows_getch()
text = re.sub(r"sys\.stdin\.read\(\s*1\s*\)", "windows_getch()", text)
text = re.sub(r"sys\.stdin\.read\(\s*([0-9]+)\s*\)", r"windows_readline_nonblocking(timeout=0.0)  # sys.stdin.read replaced", text)

# 6) Remove termios/tty variable usage lines (best-effort)
text = re.sub(r"^\s*old_settings\s*=\s*termios\.tcgetattr\(.*\)\s*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*tty\.setraw\(.*\)\s*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*tty\.setcbreak\(.*\)\s*$", "", text, flags=re.MULTILINE)

# 7) Remove leftover "import select" if any remains
text = re.sub(r"^\s*import\s+select\s*$", "", text, flags=re.MULTILINE)

# 8) Add a small OS check comment at top for clarity (if not already present)
if "WINDOWS_CONVERSION_NOTE" not in text:
    text = "# WINDOWS_CONVERSION_NOTE: This file was auto-generated from a Unix-friendly version.\n" + text

# 7) STACK’EM FIX — Replace the broken input line safely
STACKEM_LINE = r"if sys\.stdin in \( \[0\] if msvcrt is None else \(msvcrt\.kbhit\(\),\) \)\[0\]:"

# Replace broken line with a unique marker
text = re.sub(STACKEM_LINE, "###STACKEM_INPUT_PATCH###", text)

# Now insert correct Windows-safe code
STACKEM_BLOCK = (
    "if msvcrt.kbhit():"
    "    key = msvcrt.getch()"
    "    if key in (b'\r', b'\n'):"
    "        break"
)

text = text.replace("###STACKEM_INPUT_PATCH###", STACKEM_BLOCK)


# 9) Write out the converted file
with io.open(DST, "w", encoding="utf-8") as out_f:
    out_f.write(text)

print(f"Converted file written to: {DST}")
print("Please inspect the file for any remaining platform-specific calls and test it on Windows.")
print("If you run into a specific error, paste the traceback and I will patch the converter further.")
