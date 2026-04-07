"""Generate the app favicon and logo."""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size=512):
    """Create dark blue icon with yellow STAGIONALITÀ + flags."""
    img = Image.new('RGBA', (size, size), (10, 14, 26, 255))
    draw = ImageDraw.Draw(img)
    
    # Rounded rect background
    margin = 20
    r = 60
    draw.rounded_rectangle([margin, margin, size-margin, size-margin], 
                           radius=r, fill=(10, 14, 42, 255), 
                           outline=(204, 255, 0, 80), width=3)
    
    # Italian flag stripe (left)
    flag_y = 140
    flag_h = 60
    flag_w = 70
    # Green
    draw.rectangle([60, flag_y, 60+flag_w//3, flag_y+flag_h], fill=(0, 140, 69))
    # White
    draw.rectangle([60+flag_w//3, flag_y, 60+2*flag_w//3, flag_y+flag_h], fill=(255, 255, 255))
    # Red
    draw.rectangle([60+2*flag_w//3, flag_y, 60+flag_w, flag_y+flag_h], fill=(206, 43, 55))
    
    # US flag (right) - simplified
    us_x = size - 60 - flag_w
    # Blue canton
    draw.rectangle([us_x, flag_y, us_x + flag_w//2, flag_y + flag_h//2], fill=(0, 40, 104))
    # Red and white stripes
    stripe_h = flag_h // 7
    for i in range(7):
        color = (191, 10, 48) if i % 2 == 0 else (255, 255, 255)
        draw.rectangle([us_x, flag_y + i*stripe_h, us_x + flag_w, flag_y + (i+1)*stripe_h], fill=color)
    # Blue canton overlay
    draw.rectangle([us_x, flag_y, us_x + flag_w*2//5, flag_y + flag_h*4//7], fill=(0, 40, 104))
    # Stars (dots)
    for row in range(3):
        for col in range(3):
            sx = us_x + 6 + col * 9
            sy = flag_y + 6 + row * 7
            draw.ellipse([sx, sy, sx+4, sy+4], fill=(255, 255, 255))
    
    # Chart icon in center
    cx, cy = size//2, size//2 - 20
    # Up bars
    bars = [(cx-80, 60), (cx-50, 85), (cx-20, 45), (cx+10, 95), (cx+40, 70), (cx+70, 110)]
    bar_w = 22
    for bx, bh in bars:
        color = (34, 217, 140) if bh > 70 else (204, 255, 0)
        draw.rectangle([bx, cy + 60 - bh, bx + bar_w, cy + 60], fill=color)
    
    # Trend line
    pts = [(bx + bar_w//2, cy + 60 - bh) for bx, bh in bars]
    for i in range(len(pts)-1):
        draw.line([pts[i], pts[i+1]], fill=(204, 255, 0), width=3)
    
    # Text "STAGIONALITÀ"
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_big = ImageFont.load_default()
        font_sm = ImageFont.load_default()
    
    text = "STAGIONALITÀ"
    bbox = draw.textbbox((0,0), text, font=font_big)
    tw = bbox[2] - bbox[0]
    tx = (size - tw) // 2
    ty = size - 150
    
    # Glow effect
    for offset in range(3, 0, -1):
        draw.text((tx, ty+offset), text, fill=(204, 255, 0, 40), font=font_big)
    draw.text((tx, ty), text, fill=(204, 255, 0, 255), font=font_big)
    
    # Subtitle
    sub = "MILANO · NASDAQ"
    bbox2 = draw.textbbox((0,0), sub, font=font_sm)
    sw = bbox2[2] - bbox2[0]
    draw.text(((size - sw)//2, ty + 55), sub, fill=(160, 170, 200), font=font_sm)
    
    return img

if __name__ == "__main__":
    icon = create_icon(512)
    icon.save("assets/icon.png")
    
    # Favicon 32x32
    favicon = create_icon(256).resize((32, 32), Image.LANCZOS)
    favicon.save("assets/favicon.png")
    
    # Logo for sidebar
    logo = create_icon(512)
    logo.save("assets/logo.png")
    
    print("✅ Icons generated in assets/")
