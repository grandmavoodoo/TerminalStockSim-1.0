# remove_emojis_windows_safe.py
# Usage:
#   python remove_emojis_windows_safe.py Stock_Sim.py
# Output:
#   Stock_Sim_noemoji.py (Windows-safe version)
import sys, re, io, os

if len(sys.argv) < 2:
    print("Usage: python remove_emojis_windows_safe.py <input_file>")
    sys.exit(1)

src = sys.argv[1]
if not os.path.exists(src):
    print(f"File not found: {src}")
    sys.exit(1)

dst = os.path.splitext(src)[0] + "_noemoji.py"

# Basic replacements (you can add more if needed)
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
    "💲": "$",
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
    "📉": "(Loss)",
    "📈": "(Gain)",
    "💵": "(Cash)",
    "🏇🏻": "(Horse)",
    "🎰": "(Slots)",
    "🧾": "(Note)",
    "📉": "(Down)",
    "📈": "(Up)",
    "🌌": "(Sky)",
    "🌅": "(Morning)",
    "🍀": "(Luck)",
    "💸": "(Cash)",
    "🪙": "(Coin)",
    "🔥": "(Hot)",
    "❌": "(X)",
    "🟩": "[+]",
    "🟥": "[-]",
    "⭐": "*",
    "🆓": "(Free)",
    "🧠": "(Brain)",
    "🎯": "(Target)",
    "🕵️": "(Spy)",
    "💻": "(Laptop)",
    "🧨": "(Boom)",
    "📦": "(Box)",
    "🥇": "(Gold)",
    "🥈": "(Silver)",
    "🥉": "(Bronze)",
    "🪙": "(Coin)",
    "🕹️": "(Game)",
    "🏆": "(Trophy)",
    "💎": "(Gem)",
}

# --- read and replace ---
with io.open(src, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# Replace each emoji
for emoji, replacement in emoji_map.items():
    content = content.replace(emoji, replacement)

# Remove stray emojis or symbols not listed
content = re.sub(r"[\U0001F000-\U0001FFFF]", "", content)  # remove remaining emojis

with io.open(dst, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Done! Wrote Windows-safe file: {dst}")
