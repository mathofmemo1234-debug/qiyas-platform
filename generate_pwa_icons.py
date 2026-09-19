import os
import math
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

def create_gradient_icon(size, is_maskable=False, is_rounded=True):
    # Create base image
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Margin for maskable icons (must be within 80% safe zone)
    margin = int(size * 0.1) if is_maskable else 0
    bg_box = [margin, margin, size - margin, size - margin]
    radius = 0 if is_maskable else int(size * 0.22) if is_rounded else 0

    # Draw gradient background (Sky-600 #0284c7 to Indigo-700 #4338ca)
    gradient = Image.new("RGBA", (size, size))
    g_draw = ImageDraw.Draw(gradient)
    
    c1 = (2, 132, 199)   # Sky-600
    c2 = (67, 56, 202)   # Indigo-700
    
    for y in range(size):
        ratio = y / float(size)
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        g_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Add subtle radial glow at top-right
    center_x, center_y = int(size * 0.75), int(size * 0.25)
    max_dist = size * 0.6
    for dy in range(-int(max_dist), int(max_dist)):
        y = center_y + dy
        if 0 <= y < size:
            for dx in range(-int(max_dist), int(max_dist)):
                x = center_x + dx
                if 0 <= x < size:
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < max_dist:
                        alpha = int(60 * (1 - dist / max_dist))
                        current_c = gradient.getpixel((x, y))
                        new_r = min(255, current_c[0] + alpha)
                        new_g = min(255, current_c[1] + alpha)
                        new_b = min(255, current_c[2] + alpha)
                        gradient.putpixel((x, y), (new_r, new_g, new_b, 255))

    # Mask for rounded rectangle if not maskable
    if is_maskable:
        mask = Image.new("L", (size, size), 255)
    else:
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)

    img.paste(gradient, (0, 0), mask)
    icon_draw = ImageDraw.Draw(img)

    # Draw Open Book / Academic Emblem in Center
    center = size / 2.0
    scale = size / 512.0

    # Book dimensions
    book_w = 230 * scale
    book_h = 130 * scale
    book_bottom_y = center + 55 * scale
    book_top_y = book_bottom_y - book_h

    # Page points
    left_top_outer = (center - book_w / 2, book_top_y + 15 * scale)
    left_top_inner = (center - 10 * scale, book_top_y)
    left_bottom_inner = (center - 10 * scale, book_bottom_y)
    left_bottom_outer = (center - book_w / 2, book_bottom_y + 15 * scale)
    left_page = [left_top_outer, left_top_inner, left_bottom_inner, left_bottom_outer]

    right_top_inner = (center + 10 * scale, book_top_y)
    right_top_outer = (center + book_w / 2, book_top_y + 15 * scale)
    right_bottom_outer = (center + book_w / 2, book_bottom_y + 15 * scale)
    right_bottom_inner = (center + 10 * scale, book_bottom_y)
    right_page = [right_top_inner, right_top_outer, right_bottom_outer, right_bottom_inner]

    # Draw book shadow
    shadow_offset = 6 * scale
    icon_draw.polygon(
        [(p[0], p[1] + shadow_offset) for p in left_page],
        fill=(0, 20, 60, 90)
    )
    icon_draw.polygon(
        [(p[0], p[1] + shadow_offset) for p in right_page],
        fill=(0, 20, 60, 90)
    )

    # Draw Pages with crisp white
    icon_draw.polygon(left_page, fill=(255, 255, 255, 245), outline=(224, 242, 254, 255), width=max(1, int(3 * scale)))
    icon_draw.polygon(right_page, fill=(255, 255, 255, 245), outline=(224, 242, 254, 255), width=max(1, int(3 * scale)))

    # Book lines (simulating text/equations)
    line_col = (186, 230, 253, 220)
    for i in range(3):
        ly = book_top_y + (35 + i * 26) * scale
        # left lines
        icon_draw.line(
            [(center - book_w / 2 + 25 * scale, ly + 6 * scale), (center - 30 * scale, ly)],
            fill=line_col,
            width=max(1, int(4 * scale))
        )
        # right lines
        icon_draw.line(
            [(center + 30 * scale, ly), (center + book_w / 2 - 25 * scale, ly + 6 * scale)],
            fill=line_col,
            width=max(1, int(4 * scale))
        )

    # Graduation Cap / Academic Diamond Star above book
    star_cy = center - 80 * scale
    star_w = 40 * scale
    star_h = 40 * scale
    diamond = [
        (center, star_cy - star_h),
        (center + star_w, star_cy),
        (center, star_cy + star_h),
        (center - star_w, star_cy)
    ]
    glow_diamond = [
        (center, star_cy - star_h - 4 * scale),
        (center + star_w + 4 * scale, star_cy),
        (center, star_cy + star_h + 4 * scale),
        (center - star_w - 4 * scale, star_cy)
    ]
    icon_draw.polygon(glow_diamond, fill=(254, 240, 138, 120))
    icon_draw.polygon(diamond, fill=(253, 224, 71, 255), outline=(255, 255, 255, 240), width=max(1, int(2 * scale)))

    # Sparkle stars
    def draw_sparkle(cx, cy, s):
        pts = [
            (cx, cy - s), (cx + s * 0.3, cy - s * 0.3),
            (cx + s, cy), (cx + s * 0.3, cy + s * 0.3),
            (cx, cy + s), (cx - s * 0.3, cy + s * 0.3),
            (cx - s, cy), (cx - s * 0.3, cy - s * 0.3)
        ]
        icon_draw.polygon(pts, fill=(255, 255, 255, 230))

    draw_sparkle(center - 110 * scale, star_cy + 10 * scale, 16 * scale)
    draw_sparkle(center + 110 * scale, star_cy - 10 * scale, 14 * scale)

    # Stylized Arabic Text "نبيه" badge at bottom
    badge_w = 160 * scale
    badge_h = 42 * scale
    badge_y = center + 115 * scale
    badge_box = [center - badge_w / 2, badge_y, center + badge_w / 2, badge_y + badge_h]
    icon_draw.rounded_rectangle(badge_box, radius=int(badge_h / 2), fill=(255, 255, 255, 240))

    # Dot of "ن" and "ي" represented with small circular accents
    accent_col = (2, 132, 199, 255)
    icon_draw.ellipse(
        [center - 16 * scale, badge_y + 14 * scale, center - 6 * scale, badge_y + 24 * scale],
        fill=accent_col
    )
    icon_draw.ellipse(
        [center + 6 * scale, badge_y + 14 * scale, center + 16 * scale, badge_y + 24 * scale],
        fill=accent_col
    )

    return img

def main():
    icons_to_generate = [
        ("icon-192.png", 192, False, True),
        ("icon-512.png", 512, False, True),
        ("icon-maskable-192.png", 192, True, False),
        ("icon-maskable-512.png", 512, True, False),
        ("apple-touch-icon.png", 180, False, False),
        ("favicon.png", 64, False, True)
    ]

    for filename, size, maskable, rounded in icons_to_generate:
        out_path = os.path.join(ICONS_DIR, filename)
        img = create_gradient_icon(size, is_maskable=maskable, is_rounded=rounded)
        img.save(out_path, "PNG")
        print(f"Generated {filename} ({size}x{size}) -> {out_path}")

    print("All PWA icons generated successfully!")

if __name__ == "__main__":
    main()
