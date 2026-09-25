"""
generate_qr.py
Generates high-resolution, branded QR asset stickers for laptop identification.
Creates both raw QR codes and stylized printable asset label badges (with laptop ID, model, and institution name).
"""

import sys
from pathlib import Path
from typing import Optional
import qrcode
from PIL import Image, ImageDraw, ImageFont

import database as db

QR_DIR = Path(__file__).parent / "qr_codes"


def generate_styled_qr_badge(
    laptop_id: str,
    model_name: str = "",
    institution: str = "ASSET TRACKER",
    box_size: int = 10,
    border: int = 2
) -> Image.Image:
    """
    Generates a stylized printable asset sticker badge containing:
    - Top header bar with institution tag
    - High-density QR code for instant webcam/laser scanning
    - Bold Laptop ID string
    - Subtitle Model string
    """
    # 1. Create Base QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(laptop_id)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGBA")

    qr_w, qr_h = qr_img.size

    # Badge Dimensions
    badge_w = qr_w + 60
    header_h = 44
    footer_h = 75
    badge_h = header_h + qr_h + footer_h

    # 2. Create Canvas
    badge = Image.new("RGBA", (badge_w, badge_h), color="#FFFFFF")
    draw = ImageDraw.Draw(badge)

    # 3. Outer Rounded Border
    border_color = "#005C9E"
    draw.rectangle([0, 0, badge_w - 1, badge_h - 1], outline=border_color, width=3)

    # 4. Header Bar
    header_bg = "#0B2545"
    draw.rectangle([3, 3, badge_w - 4, header_h], fill=header_bg)

    # Try loading system font or fallback to default
    try:
        font_header = ImageFont.truetype("arialbd.ttf", 16)
        font_id = ImageFont.truetype("arialbd.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font_header = ImageFont.load_default()
        font_id = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Draw Header Text
    draw.text((badge_w // 2, header_h // 2 + 2), institution.upper(), fill="#FFFFFF", font=font_header, anchor="mm")

    # 5. Paste QR Image
    qr_x = (badge_w - qr_w) // 2
    qr_y = header_h + 10
    badge.paste(qr_img, (qr_x, qr_y), qr_img)

    # 6. Draw Laptop ID & Model
    id_y = qr_y + qr_h + 20
    draw.text((badge_w // 2, id_y), laptop_id, fill="#0F172A", font=font_id, anchor="mm")

    if model_name:
        sub_y = id_y + 24
        truncated_model = (model_name[:28] + "...") if len(model_name) > 28 else model_name
        draw.text((badge_w // 2, sub_y), truncated_model, fill="#64748B", font=font_sub, anchor="mm")

    return badge.convert("RGB")


def generate_qr_for_laptop(laptop_id: str, model: str = "") -> Path:
    QR_DIR.mkdir(exist_ok=True)
    inst = db.get_setting("institution_name", "ASSET TRACKER")
    badge_img = generate_styled_qr_badge(laptop_id, model, inst)
    path = QR_DIR / f"{laptop_id}_sticker.png"
    badge_img.save(path)
    print(f"Generated asset tag sticker: {path}")
    return path


def generate_all_fleet_qrs():
    """Generates QR stickers for every laptop registered in the database."""
    db.init_db()
    laptops = db.get_all_laptops()
    if not laptops:
        print("No laptops in database.")
        return
    for l in laptops:
        generate_qr_for_laptop(l["laptop_id"], f"{l['brand']} {l['model']}")


if __name__ == "__main__":
    ids = sys.argv[1:]
    if not ids:
        print("Generating stickers for all laptops in DB...")
        generate_all_fleet_qrs()
    else:
        for l_id in ids:
            generate_qr_for_laptop(l_id)