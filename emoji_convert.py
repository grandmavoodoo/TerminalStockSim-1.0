# make_windows_version.py
# Usage:
#   python make_windows_version.py Stock_Sim.py
# Output:
#   Stock_Sim_windows.py  (Windows-safe, no emojis)

import sys, re, io, os

if len(sys.argv) < 2:
    print("Usage: python make_windows_version.py <input_file>")
    sys.exit(1)

src = sys.argv[1]
if not os.path.exists(src):
    print(f"File not found: {src}")
    sys.exit(1)

dst = os.path.splitext(src)[0] + "_windows.py"

# --- Step 1: Load original file ---
with io.open(src, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

# --- Step 2: Strip Linux-only imports and add msvcrt ---
text = re.sub(r"import\s+sys\s*,\s*time\s*,\s*random\s*,\s*tty\s*,\s*termios\s*,\s*select",
              "import sys, time, random", text)
text = re.sub(r"^\s*import\s+(tty|termios|select)\s*$", "", text, flags=re.MULTILINE)
text = re.sub(r"^\s*from\s+(tty|termios|select)\s+import\s+.*$", "", text, flags=re.MULTILINE)

# --- Step 3: Add Windows helper functions ---
helpers = r'''

# --- WINDOWS CONSOLE COMPATIBILITY ---
try:
    import msvcrt
except ImportError:
    msvcrt = None

def windows_getch():
    """Get a single character from keyboard (Windows only)."""
    if msvcrt is None:
        return input("> ")
    return msvcrt.getwch()

def windows_kbhit():
    return msvcrt.kbhit() if msvcrt else False

def windows_readline_nonblocking(timeout=0.0):
    """Try to read user input without blocking."""
    import time
    if msvcrt is None:
        return ""
    start = time.time()
    s = ""
    while True:
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch == "\r":
                ch = "\n"
            s += ch
            if ch == "\n":
                break
        if timeout > 0 and (time.time() - start) >= timeout:
            break
    return s
# -------------------------------------

'''
text = text.replace("SAVE_FILE = ", helpers + "SAVE_FILE = ")

# --- Step 4: Replace termios/tty/select usage ---
text = re.sub(r"tty\.setraw\([^\)]*\)", "pass  # removed for Windows", text)
text = re.sub(r"termios\.tcgetattr\([^\)]*\)", "None  # removed for Windows", text)
text = re.sub(r"termios\.tcsetattr\([^\)]*\)", "pass  # removed for Windows", text)
text = re.sub(r"select\.select\([^\)]*\)", "windows_kbhit()", text)
text = re.sub(r"sys\.stdin\.read\(\s*1\s*\)", "windows_getch()", text)

# --- Step 5: Replace emojis / fancy Unicode ---
emoji_map = {
    "🚀": "[Rocket]",
    "💰": "(Money)",
    "💲": "(Dollar)",
    "🏦": "(Bank)",
    "💼": "(Portfolio)",
    "🏛️": "(Bank)",
    "📈": "(Up)",
    "📉": "(Down)",
    "➖": "-",
    "✅": "[OK]",
    "🆕": "[NEW]",
    "🎉": "[Congrats]",
    "💳": "(Card)",
    "🪪": "(ID)",
    "📊": "(Chart)",
    "🧩": "(DLC)",
    "🌿": "(Weed)",
    "🚬": "(Smoke)",
    "🌌": "(LSD)",
    "🌅": "(Sunrise)",
    "🍚": "(Cocaine)",
    "🧪": "(Chem)",
    "🧊": "(Ice)",
    "👑": "(Crown)",
    "⌚": "(Watch)",
    "💍": "(Ring)",
    "📦": "(Box)",
    "💊": "(Pill)",
    "⚠️": "[Warn]",
    "🗓️": "(Day)",
    "🏇🏻": "(Horse)",
    "🎰": "(Slots)",
    "🧾": "(Note)",
    "🔥": "(Hot)",
    "❌": "(X)",
    "⭐": "*",
    "🆓": "(Free)",
    "🧠": "(Brain)",
    "🎯": "(Target)",
    "💻": "(Laptop)",
    "🧨": "(Boom)",
    "🏆": "(Trophy)",
    "💎": "(Gem)",
}
for emoji, replacement in emoji_map.items():
    text = text.replace(emoji, replacement)
# remove any leftover emojis (unicode range 1F000–1FFFF)
text = re.sub(r"[\U0001F000-\U0001FFFF]", "", text)

# --- Step 6: Add note header ---
if "WINDOWS_VERSION_NOTE" not in text:
    text = "# WINDOWS_VERSION_NOTE: Auto-converted from Linux version.\n" + text

# --- Step 7: Write file ---
with io.open(dst, "w", encoding="utf-8") as f:
    f.write(text)

print(f"✅ Windows-compatible, emoji-free version saved as: {dst}")
print("You can now run it using:  python " + dst)
