# ATLEAST GIVE CREDITS IF YOU STEALING :(((((((((((((((((((((((((((((((((((((
# ELSE NO FURTHER PUBLIC THUMBNAIL UPDATES

import logging
import os
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from py_yt import VideosSearch

logging.basicConfig(level=logging.INFO)

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight), Image.Resampling.LANCZOS)
    return newImage

async def gen_thumb(videoid: str, decode: str = "999_CORES"):
    try:
        cache_path = f"cache/{videoid}_v4.png"
        if os.path.isfile(cache_path):
            return cache_path

        os.makedirs("cache", exist_ok=True)

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        thumbnail = None
        
        search_results = await results.next()
        if search_results and "result" in search_results and len(search_results["result"]) > 0:
            for result in search_results["result"]:
                thumbnail_data = result.get("thumbnails")
                if thumbnail_data:
                    thumbnail = thumbnail_data[0]["url"].split("?")[0]
                    break

        if not thumbnail:
            return None

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    filepath = f"cache/thumb{videoid}.png"
                    async with aiofiles.open(filepath, mode="wb") as f:
                        await f.write(await resp.read())
                    
        image_path = f"cache/thumb{videoid}.png"
        if not os.path.exists(image_path):
            return None
            
        youtube = Image.open(image_path).convert("RGB")
        
        # 1. Background (Blur & Darken)
        bg_img = changeImageSize(1280, 720, youtube)
        background = bg_img.filter(ImageFilter.GaussianBlur(35))
        darken = Image.new("RGBA", (1280, 720), (10, 10, 15, 210))
        background = Image.alpha_composite(background.convert("RGBA"), darken).convert("RGB")

        # 2. Apple Music Player Card Box
        card_w, card_h = 1060, 560
        card_x = (1280 - card_w) // 2
        card_y = (720 - card_h) // 2
        
        card_layer = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_layer)
        
        card_draw.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=35,
            fill=(25, 25, 30, 245),
            outline=(255, 255, 255, 35),
            width=2
        )
        
        # 3. Square Album Art (Thumbnail)
        thumb_size = 440
        thumb_x = card_x + 50
        thumb_y = card_y + 60
        
        orig_w, orig_h = youtube.size
        min_dim = min(orig_w, orig_h)
        left = (orig_w - min_dim) // 2
        top = (orig_h - min_dim) // 2
        square_img = youtube.crop((left, top, left + min_dim, top + min_dim))
        album_art = square_img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (thumb_size, thumb_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, thumb_size, thumb_size], radius=16, fill=255)
        
        card_layer.paste(album_art, (thumb_x, thumb_y), mask)
        
        background = Image.alpha_composite(background.convert("RGBA"), card_layer).convert("RGB")
        draw = ImageDraw.Draw(background)

        # Fonts
        try:
            font_title = ImageFont.truetype('assets/font.ttf', 36)
            font_sub = ImageFont.truetype('assets/font.ttf', 24)
            font_time = ImageFont.truetype('assets/font.ttf', 20)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            font_time = ImageFont.load_default()

        # 4. Text & Controls Layout
        text_x = thumb_x + thumb_size + 50
        text_area_w = card_x + card_w - text_x - 50
        
        # Device Header & decode / 999_CORES info
        header_text = f"iPhone ( {decode} ) 🎧"
        draw.text((text_x, card_y + 65), header_text, font=font_sub, fill=(150, 150, 160))
        
        # Title (သို့ 999_CORES ဖော်ပြချက်)
        draw.text((text_x, card_y + 105), "Playing Audio", font=font_title, fill=(255, 255, 255))
        
        # Artist / 999_CORES
        draw.text((text_x, card_y + 155), f"Core: {999_CORES}", font=font_sub, fill=(160, 160, 170))

        # 5. Progress Bar
        bar_y = card_y + 225
        bar_w = text_area_w
        bar_h = 6
        
        draw.rounded_rectangle([text_x, bar_y, text_x + bar_w, bar_y + bar_h], radius=3, fill=(70, 70, 80))
        progress_w = int(bar_w * 0.4)
        draw.rounded_rectangle([text_x, bar_y, text_x + progress_w, bar_y + bar_h], radius=3, fill=(240, 240, 240))
        
        draw.text((text_x, bar_y + 15), "1:27", font=font_time, fill=(150, 150, 160))
        draw.text((text_x + bar_w - 45, bar_y + 15), "-0:55", font=font_time, fill=(150, 150, 160))

        # 6. Media Control Buttons
        ctrl_y = card_y + 350
        center_ctrl_x = text_x + (text_area_w // 2) - 20
        
        # Backward (◀◀)
        draw.polygon([(center_ctrl_x - 60, ctrl_y + 18), (center_ctrl_x - 35, ctrl_y + 5), (center_ctrl_x - 35, ctrl_y + 31)], fill=(220, 220, 220))
        draw.polygon([(center_ctrl_x - 35, ctrl_y + 18), (center_ctrl_x - 10, ctrl_y + 5), (center_ctrl_x - 10, ctrl_y + 31)], fill=(220, 220, 220))

        # Pause ( || )
        draw.rounded_rectangle([center_ctrl_x + 10, ctrl_y + 4, center_ctrl_x + 22, ctrl_y + 32], radius=3, fill=(255, 255, 255))
        draw.rounded_rectangle([center_ctrl_x + 30, ctrl_y + 4, center_ctrl_x + 42, ctrl_y + 32], radius=3, fill=(255, 255, 255))

        # Forward (▶▶)
        draw.polygon([(center_ctrl_x + 70, ctrl_y + 5), (center_ctrl_x + 70, ctrl_y + 31), (center_ctrl_x + 95, ctrl_y + 18)], fill=(220, 220, 220))
        draw.polygon([(center_ctrl_x + 95, ctrl_y + 5), (center_ctrl_x + 95, ctrl_y + 31), (center_ctrl_x + 120, ctrl_y + 18)], fill=(220, 220, 220))

        if os.path.exists(image_path):
            os.remove(image_path)
            
        background_path = f"cache/{videoid}_v4.png"
        background.save(background_path, quality=95)
        
        return background_path

    except Exception as e:
        logging.error(f"Error generating thumbnail for video {videoid}: {e}")
        return None
