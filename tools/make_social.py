"""Generador de piezas para redes de Mesifly.

Uso:  python3 tools/make_social.py spec.json carpeta_salida

spec.json = {"slides": [...], "video_name": "nombre.mp4"}
Tipos de slide:
  {"type":"cover","kicker":"...","title":"...","body":"...","hint":"Desliza para ver los tips"}
  {"type":"step","n":"1","label":"TIP 1 DE 5","title":"...","body":["...","..."],"example":"Línea 1\nLínea 2"}   (example opcional)
  {"type":"cta","title":"...","body":"...","button":"Prueba 14 días gratis","url":"app.mesifly.com"}
Reglas de texto: Poppins no tiene flechas (→); usa «=» o texto. Máx. ~3 viñetas cortas por slide.

Salida: feed_01.jpg… (1080x1350, carrusel IG/FB), vertical_01.jpg… (1080x1920) y el video vertical MP4 (H.264, 30 fps, audio silencioso).
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + "/"  # Poppins (licencia OFL) incluida en el repo
BOLD = FONT_DIR + "Poppins-Bold.ttf"
MED = FONT_DIR + "Poppins-Medium.ttf"
REG = FONT_DIR + "Poppins-Regular.ttf"

ORANGE = (228, 96, 49)       # #E46031
ORANGE_SOFT = (252, 228, 216)
CREAM = (255, 248, 243)
DARK = (31, 26, 23)
GRAY = (92, 84, 78)
WHITE = (255, 255, 255)

def wrap(draw, text, font, max_w):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            test = (cur + " " + w).strip()
            if draw.textlength(test, font=font) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_block(draw, x, y, text, font, fill, max_w, spacing=1.25):
    lh = int(font.size * spacing)
    for line in wrap(draw, text, font, max_w):
        draw.text((x, y), line, font=font, fill=fill)
        y += lh
    return y


def block_height(draw, text, font, max_w, spacing=1.25):
    return len(wrap(draw, text, font, max_w)) * int(font.size * spacing)


def footer(draw, W, H, idx, total, on_dark):
    f = ImageFont.truetype(BOLD, 34)
    col = WHITE if on_dark else ORANGE
    draw.text((80, H - 110), "Mesifly", font=f, fill=col)
    fs = ImageFont.truetype(MED, 30)
    page = f"{idx}/{total}"
    draw.text((W - 80 - draw.textlength(page, font=fs), H - 106), page, font=fs,
              fill=WHITE if on_dark else GRAY)


def render(slide, idx, total, W, H):
    dark = slide["type"] in ("cover", "cta")
    img = Image.new("RGB", (W, H), ORANGE if dark else CREAM)
    d = ImageDraw.Draw(img)
    M = 80
    maxw = W - 2 * M

    if slide["type"] == "cover":
        fk = ImageFont.truetype(BOLD, 34)
        ft = ImageFont.truetype(BOLD, 92)
        fb = ImageFont.truetype(REG, 44)
        fh = ImageFont.truetype(MED, 38)
        h = (int(fk.size * 1.4) + 40 + block_height(d, slide["title"], ft, maxw, 1.12)
             + 40 + block_height(d, slide["body"], fb, maxw, 1.35))
        y = (H - h) // 2 - 40
        d.text((M, y), slide["kicker"], font=fk, fill=(255, 222, 205))
        y += int(fk.size * 1.4) + 40
        y = text_block(d, M, y, slide["title"], ft, WHITE, maxw, 1.12) + 40
        text_block(d, M, y, slide["body"], fb, WHITE, maxw, 1.35)
        d.text((M, H - 200), slide["hint"], font=fh, fill=WHITE)

    elif slide["type"] == "step":
        fn = ImageFont.truetype(BOLD, 64)
        ft = ImageFont.truetype(BOLD, 72)
        fb = ImageFont.truetype(REG, 42)
        fe = ImageFont.truetype(MED, 42)
        circle = 130
        body_h = sum(block_height(d, "• " + b, fb, maxw - 30, 1.35) + 22 for b in slide["body"])
        ex_h = 0
        if slide.get("example"):
            ex_h = block_height(d, slide["example"], fe, maxw - 80, 1.35) + 80 + 40
        h = circle + 50 + block_height(d, slide["title"], ft, maxw, 1.12) + 40 + body_h + ex_h
        y = max(120, (H - h) // 2 - 30)
        d.ellipse((M, y, M + circle, y + circle), fill=ORANGE)
        tw = d.textlength(slide["n"], font=fn)
        d.text((M + (circle - tw) / 2, y + 22), slide["n"], font=fn, fill=WHITE)
        lbl = ImageFont.truetype(BOLD, 32)
        d.text((M + circle + 30, y + 46), slide.get("label", f"PASO {slide['n']}"), font=lbl, fill=ORANGE)
        y += circle + 50
        y = text_block(d, M, y, slide["title"], ft, DARK, maxw, 1.12) + 40
        for b in slide["body"]:
            lines = wrap(d, b, fb, maxw - 40)
            d.text((M, y), "•", font=fb, fill=ORANGE)
            for line in lines:
                d.text((M + 40, y), line, font=fb, fill=GRAY)
                y += int(fb.size * 1.35)
            y += 22
        if slide.get("example"):
            y += 18
            eh = block_height(d, slide["example"], fe, maxw - 80, 1.35)
            d.rounded_rectangle((M, y, W - M, y + eh + 80), radius=32, fill=ORANGE_SOFT)
            d.rectangle((M, y + 24, M + 10, y + eh + 56), fill=ORANGE)
            text_block(d, M + 50, y + 40, slide["example"], fe, DARK, maxw - 80, 1.35)

    elif slide["type"] == "cta":
        ft = ImageFont.truetype(BOLD, 80)
        fb = ImageFont.truetype(REG, 42)
        fbtn = ImageFont.truetype(BOLD, 46)
        fu = ImageFont.truetype(BOLD, 52)
        btn_h = 120
        h = (block_height(d, slide["title"], ft, maxw, 1.12) + 40 +
             block_height(d, slide["body"], fb, maxw, 1.4) + 60 + btn_h + 50 + 70)
        y = (H - h) // 2 - 30
        y = text_block(d, M, y, slide["title"], ft, WHITE, maxw, 1.12) + 40
        y = text_block(d, M, y, slide["body"], fb, WHITE, maxw, 1.4) + 60
        bw = d.textlength(slide["button"], font=fbtn) + 120
        d.rounded_rectangle((M, y, M + bw, y + btn_h), radius=60, fill=WHITE)
        d.text((M + 60, y + 30), slide["button"], font=fbtn, fill=ORANGE)
        y += btn_h + 50
        d.text((M, y), slide["url"], font=fu, fill=WHITE)

    footer(d, W, H, idx, total, dark)
    return img



def build_video(out_dir, n, name):
    import subprocess
    durs = [3.5] + [4.2] * (n - 2) + [5.0]
    xf = 0.4
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for i, d in enumerate(durs, 1):
        cmd += ["-loop", "1", "-t", str(d), "-i", os.path.join(out_dir, f"vertical_{i:02d}.jpg")]
    total = sum(durs) - xf * (n - 1)
    cmd += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    parts = [f"[{i}:v]fps=30,format=yuv420p,setsar=1[v{i}]" for i in range(n)]
    prev, off = "v0", 0.0
    for i in range(1, n):
        off += durs[i - 1] - xf
        out = "vout" if i == n - 1 else f"x{i}"
        parts.append(f"[{prev}][v{i}]xfade=transition=slideleft:duration={xf}:offset={off:.2f}[{out}]")
        prev = out
    cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", f"{n}:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
            os.path.join(out_dir, name)]
    subprocess.run(cmd, check=True)


def main(spec_path, out_dir):
    import json
    spec = json.load(open(spec_path, encoding="utf-8"))
    slides = spec["slides"]
    os.makedirs(out_dir, exist_ok=True)
    total = len(slides)
    for (W, H, tag) in [(1080, 1350, "feed"), (1080, 1920, "vertical")]:
        for i, s in enumerate(slides, 1):
            render(s, i, total, W, H).save(os.path.join(out_dir, f"{tag}_{i:02d}.jpg"), "JPEG", quality=88, optimize=True)
    build_video(out_dir, total, spec.get("video_name", "video.mp4"))
    print("OK", out_dir)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
