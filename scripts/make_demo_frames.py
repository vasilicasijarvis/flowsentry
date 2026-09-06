#!/usr/bin/env python3
"""Render FlowSentry demo GIF frames with Pillow (terminal-style)."""

from PIL import Image, ImageDraw, ImageFont

W, H = 960, 540
BG = (10, 14, 26)
FG = (226, 232, 240)
DIM = (100, 116, 139)
CYAN = (34, 211, 238)
INDIGO = (129, 140, 248)
RED = (248, 113, 113)
YELLOW = (250, 204, 21)
GREEN = (74, 222, 128)
BAR = (17, 24, 39)

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def load_font(size):
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_TITLE = load_font(22)
F_TEXT = load_font(15)
F_SMALL = load_font(13)
F_LOGO = load_font(30)

frames = []


def new_frame():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # title bar
    d.rectangle([0, 0, W, 36], fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([14 + i * 22, 12, 26 + i * 22, 24], fill=c)
    d.text((W // 2 - 130, 8), "mihai@homelab: ~/workflows", font=F_SMALL, fill=DIM)
    d.line([0, 36, W, 36], fill=(51, 65, 85), width=1)
    return img, d


def typed(cmd, prefix="$ "):
    """Frames for a command being typed char by char."""
    out = []
    for i in range(1, len(cmd) + 1):
        img, d = new_frame()
        d.text((30, 60), prefix + cmd[:i], font=F_TEXT, fill=FG)
        d.text((30 + len(prefix + cmd[:i]) * 9 + 12, 60), "_", font=F_TEXT, fill=CYAN)
        out.append(img)
    return out


frames = []
frames += typed("flowsentry scan ./workflows --fail-on high", "mihai@homelab:~$ ")
# pause frames while 'scanning'
for _ in range(6):
    img, d = new_frame()
    d.text((30, 60), "mihai@homelab:~$ flowsentry scan ./workflows --fail-on high", font=F_TEXT, fill=FG)
    dots = "." * ((_ // 2) % 4 + 1)
    d.text((30, 90), "scanning 10 workflow files " + dots, font=F_TEXT, fill=DIM)
    frames.append(img)

# banner + results frame 1
img, d = new_frame()
d.text((30, 60), "mihai@homelab:~$ flowsentry scan ./workflows --fail-on high", font=F_TEXT, fill=FG)
d.text((30, 96), "+----------------------------------------------------+", font=F_TEXT, fill=CYAN)
d.text((30, 118), "|   FlowSentry v0.1.0  -  n8n security scan          |", font=F_TEXT, fill=CYAN)
d.text((30, 140), "+----------------------------------------------------+", font=F_TEXT, fill=CYAN)
d.text((30, 174), "Scanned: 10 workflow file(s)", font=F_TEXT, fill=FG)
d.text((30, 200), "workflows/AI_Bot.json", font=F_TITLE, fill=FG)
lines = [
    ("[!] CRITICAL  FS001  Webhook endpoint without authentication", RED),
    ("    node: Webhook WhatsApp  (n8n-nodes-base.webhook)", DIM),
    ("", FG),
    ("[~] MEDIUM    FS017  Webhook response mode exposes internals", YELLOW),
    ("    node: Webhook WhatsApp", DIM),
]
y = 236
for text, color in lines:
    d.text((30, y), text, font=F_TEXT, fill=color)
    y += 22
d.text((W - 24, 40), "", font=F_SMALL, fill=FG)
frames.append(img)

# results frame 2
img, d = new_frame()
d.text((30, 60), "mihai@homelab:~$ flowsentry scan ./workflows --fail-on high", font=F_TEXT, fill=FG)
d.text((30, 96), "workflows/00485-library-install.json", font=F_TITLE, fill=FG)
lines = [
    ("[!] CRITICAL  FS005  Execute Command node without guardrails", RED),
    ("    node: library_install  (n8n-nodes-base.executeCommand)", DIM),
    ("[!] CRITICAL  FS009  Expression-based command injection", RED),
    ("    evidence: LIBRARY_NAME=\"{{$json.library}}\"", DIM),
    ("", FG),
    ("[~] MEDIUM    FS010  Missing error handling on workflow", YELLOW),
]
y = 136
for text, color in lines:
    d.text((30, y), text, font=F_TEXT, fill=color)
    y += 22
frames.append(img)

# results frame 3: more files flash
for k, fname in enumerate(["workflows/n8n/w1.json",
                           "workflows/subagente-citas.json",
                           "workflows/nl2sql.json"]):
    img, d = new_frame()
    d.text((30, 60), "mihai@homelab:~$ flowsentry scan ./workflows --fail-on high", font=F_TEXT, fill=FG)
    d.text((30, 96), fname, font=F_TITLE, fill=FG)
    lines = [
        ("[!] CRITICAL  FS001  Webhook endpoint without authentication", RED),
        ("    node: HTTP Trigger / Webhook", DIM),
        ("[~] MEDIUM    FS010  Missing error handling on workflow", YELLOW),
        ("[~] MEDIUM    FS017  Webhook response mode exposes internals", YELLOW),
    ]
    y = 146
    for text, color in lines:
        d.text((30, y), text, font=F_TEXT, fill=color)
        y += 22
    frames.append(img)

# summary frame
img, d = new_frame()
d.text((30, 60), "mihai@homelab:~$ flowsentry scan ./workflows --fail-on high", font=F_TEXT, fill=FG)
d.text((30, 110), "Summary", font=F_TITLE, fill=FG)
d.text((30, 150), "critical: 11   high: 0   medium: 39", font=F_TITLE, fill=RED)
d.text((30, 186), "Result: FAIL - fix critical/high findings before production.", font=F_TEXT, fill=RED)
d.text((30, 230), "", font=F_TEXT, fill=FG)
d.text((30, 250), "exit code: 1  ->  CI gate blocks the merge", font=F_TEXT, fill=YELLOW)
d.text((30, 290), "$ flowsentry rules   # 18 rules, OWASP Agentic mapped", font=F_TEXT, fill=CYAN)
d.text((30, 330), "github.com/vasilicasijarvis/flowsentry", font=F_TEXT, fill=INDIGO)
frames.append(img)

# outro frame
img, d = new_frame()
d.text((W // 2 - 190, 180), "FlowSentry", font=load_font(48), fill=CYAN)
d.text((W // 2 - 235, 240), "Security scanner for n8n workflows", font=F_TITLE, fill=FG)
d.text((W // 2 - 200, 290), "18 rules - zero deps - CI ready", font=F_TEXT, fill=DIM)
d.text((W // 2 - 180, 330), "github.com/vasilicasijarvis/flowsentry", font=F_TEXT, fill=INDIGO)
frames.append(img)

# loop hold: repeat last 2 frames longer by duplicating
frames += [frames[-1]] * 8
frames += [frames[-9]] * 6

import os
os.makedirs("docs", exist_ok=True)
for i, f in enumerate(frames):
    f.save(f"/tmp/fs_frame_{i:03d}.png")
print(f"{len(frames)} frames rendered")
