import argparse, json, os
from pathlib import Path
from PIL import Image, ImageOps


ICO_SIZES   = [16, 32, 48]  
PNG_SIZES   = [16, 32, 180, 192, 256, 384, 512]  
MS_TILE     = 150  

def square_image(im: Image.Image, mode: str = "pad", bg=(0,0,0,0)) -> Image.Image:
    """
    mode = 'pad' (letterbox with background) or 'crop' (center-crop to square)
    """
    w, h = im.size
    if w == h:
        return im

    if mode == "crop":
        side = min(w, h)
        left = (w - side) // 2
        top  = (h - side) // 2
        return im.crop((left, top, left + side, top + side))
    else:
        side = max(w, h)
        canvas = Image.new("RGBA", (side, side), bg)
        off = ((side - w)//2, (side - h)//2)
        canvas.paste(im, off)
        return canvas

def save_png(im: Image.Image, size: int, out: Path, name: str):
    im.resize((size, size), Image.LANCZOS).save(out / f"{name}.png")

def main():
    p = argparse.ArgumentParser(description="Generate favicons from a JPG/PNG.")
    p.add_argument("input", help="Path to source image (jpg/png).")
    p.add_argument("-o", "--out", default="dist_favicon", help="Output folder (default: dist_favicon)")
    p.add_argument("--mode", choices=["pad","crop"], default="pad",
                   help="Square mode: pad (default) or crop.")
    p.add_argument("--bg", default="#00000000",
                   help="Padding background color hex RGBA (default: transparent '#00000000').")
    p.add_argument("--brand", default="Curelith", help="App/site name for manifests.")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    src = Path(args.input)
    im = Image.open(src).convert("RGBA")
    bg = args.bg.lstrip("#")
    if len(bg) in (6,8):
        r = int(bg[0:2], 16); g = int(bg[2:4], 16); b = int(bg[4:6], 16)
        a = int(bg[6:8], 16) if len(bg) == 8 else 255
    else:
        r,g,b,a = 0,0,0,0
    im_sq = square_image(im, mode=args.mode, bg=(r,g,b,a))

    ico_sizes = [(s, s) for s in ICO_SIZES]
    im_sq.save(out / "favicon.ico", format="ICO", sizes=ico_sizes)

    save_png(im_sq, 16,  out, "favicon-16x16")
    save_png(im_sq, 32,  out, "favicon-32x32")
    save_png(im_sq, 180, out, "apple-touch-icon")
    save_png(im_sq, 192, out, "android-chrome-192x192")
    save_png(im_sq, 512, out, "android-chrome-512x512")
    save_png(im_sq, MS_TILE, out, f"mstile-{MS_TILE}x{MS_TILE}")

    for s in [256, 384]:
        save_png(im_sq, s, out, f"icon-{s}x{s}")

    # site.webmanifest
    manifest = {
        "name": args.brand,
        "short_name": args.brand,
        "icons": [
            {"src": "android-chrome-192x192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "android-chrome-512x512.png", "sizes": "512x512", "type": "image/png"},
        ],
        "theme_color": "#000000",
        "background_color": "#000000",
        "display": "standalone"
    }
    (out / "site.webmanifest").write_text(json.dumps(manifest, indent=2))

    browserconfig = f"""<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
  <msapplication>
    <tile>
      <square150x150logo src="/mstile-{MS_TILE}x{MS_TILE}.png"/>
      <TileColor>#000000</TileColor>
    </tile>
  </msapplication>
</browserconfig>
"""
    (out / "browserconfig.xml").write_text(browserconfig)

    html = f"""<!-- Favicon & app icons -->
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="msapplication-TileColor" content="#000000">
<meta name="msapplication-config" content="/browserconfig.xml">
<meta name="theme-color" content="#000000">
"""
    (out / "html_snippet.txt").write_text(html)

    print(f"✅ Done! Files written to: {out.resolve()}")
    print("\nAdd these tags to <head> of your site (also saved as html_snippet.txt):\n")
    print(html)

if __name__ == "__main__":
    main()

