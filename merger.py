from PIL import Image, ImageFont, ImageDraw
import os
from math import ceil, sqrt
from datetime import date

# =========== #
fontPath = 'assets/BurbankBigRegular-BlackItalic.otf'  # The path to the font you want to use

shopbgPath = "assets/shopbg.png"  # Path to shop background

normalTitleText = "Item Shop"  # Title for the main item shop image
ogTitleText = "OG Items"  # Title for the OG items image

showDateNormal = True  # Should the date be shown in the normal image?
showDateOg = True  # Should the date be shown in the OG items image?
# =========== #


def merger(ogitems, datas=None, save_as='', currentdate=None):
    if not datas:
        if not ogitems:
            print("[MERGER] OG Items is false, getting files from cache")
            list_ = [os.path.join('cache', file) for file in os.listdir('cache') if
                     file.endswith('.png') and not file.startswith('temp')]
        else:
            print("[MERGER] OG Items is true, getting files from ogcache")
            list_ = [os.path.join('ogcache', file) for file in os.listdir('ogcache') if file.endswith('.png')]
        datas = [Image.open(i).convert("RGBA") for i in sorted(list_)]

    if not datas:
        print("[MERGER] No images to merge.")
        return

    if ogitems:
        title_text = ogTitleText
        showDate = showDateOg
    else:
        title_text = normalTitleText
        showDate = showDateNormal

    row_n = len(datas)
    rowslen = ceil(sqrt(row_n))
    columnslen = ceil(row_n / rowslen)

    px = 512
    title_area_height = 322
    total_width = rowslen * px
    total_height = columnslen * px + title_area_height

    bg_tile = Image.open(shopbgPath).convert("RGBA")
    bg_tile_width, bg_tile_height = bg_tile.size

    background = Image.new("RGBA", (total_width, total_height))

    for x in range(0, total_width, bg_tile_width):
        for y in range(0, total_height, bg_tile_height):
            background.paste(bg_tile, (x, y))

    draw = ImageDraw.Draw(background)

    font_size = 150
    max_font_size = 200
    min_title_font_size = 60

    def measure_text(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            text_width, text_height = draw.textsize(text, font=font)
        return text_width, text_height

    max_width = total_width - 40

    display_title_text = title_text

    while font_size >= min_title_font_size:
        font = ImageFont.truetype(fontPath, font_size)
        text_width, text_height = measure_text(display_title_text, font)
        if text_width <= max_width:
            break
        font_size -= 2
    else:
        max_chars = int(len(display_title_text) * (max_width / text_width))
        display_title_text = display_title_text[:max_chars] + '...'
        font = ImageFont.truetype(fontPath, font_size)
        text_width, text_height = measure_text(display_title_text, font)

    if showDate:
        font_date_size = max(int(font_size * 0.5), 30)
        total_text_height = text_height + font_date_size + 20
    else:
        total_text_height = text_height

    while font_size < max_font_size:
        next_font_size = font_size + 2
        font = ImageFont.truetype(fontPath, next_font_size)
        text_width, text_height = measure_text(display_title_text, font)
        if text_width > max_width:
            break
        if showDate:
            font_date_size = max(int(next_font_size * 0.5), 30)
            total_text_height = text_height + font_date_size + 20
        else:
            total_text_height = text_height
        if total_text_height > title_area_height:
            break
        font_size = next_font_size

    font = ImageFont.truetype(fontPath, font_size)
    text_width, text_height = measure_text(display_title_text, font)
    if showDate:
        font_date_size = max(int(font_size * 0.5), 30)

    start_y = (title_area_height - total_text_height) / 2

    title_y_position = start_y
    draw.text((total_width / 2, title_y_position), display_title_text, font=font, fill='white', anchor='mt')

    if showDate:
        if currentdate is None:
            date_text = date.today().strftime("%Y-%m-%d")
        else:
            date_text = currentdate

        date_y_position = title_y_position + text_height + 20
        font_date = ImageFont.truetype(fontPath, font_date_size)
        draw.text((total_width / 2, date_y_position), date_text, font=font_date, fill='white', anchor='mt')

    idx = 0
    for y in range(columnslen):
        for x in range(rowslen):
            if idx >= len(datas):
                break
            card = datas[idx]
            card = card.resize((px, px))
            background.paste(card, (x * px, y * px + title_area_height), card)
            idx += 1

    final_image = background.convert("RGB")

    if currentdate is None:
        date_text = date.today().strftime("%Y-%m-%d")
    else:
        date_text = currentdate

    if ogitems:
        os.makedirs('shops/og', exist_ok=True)
        save_as = f"shops/og/OGItems {date_text}.jpg"
    else:
        os.makedirs('shops', exist_ok=True)
        save_as = f"shops/shop {date_text}.jpg"

    final_image.save(save_as, optimize=True, quality=85)

    print(f"[MERGER] Image saved as {save_as}")
    return final_image
