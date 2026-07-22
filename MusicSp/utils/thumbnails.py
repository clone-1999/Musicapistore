import logging
import os
import aiofiles
import aiohttp
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import textwrap

logging.basicConfig(level=logging.INFO)

async def gen_thumb(videoid: str, song_title: str, artist_name: str = "@HANTHAR999"):
    try:
        cache_path = f"cache/{videoid}_apple_music.png"
        if os.path.isfile(cache_path):
            return cache_path

        os.makedirs("cache", exist_ok=True)

        # YouTube Thumbnail Direct URL
        thumbnail_url = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    thumbnail_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
                    async with session.get(thumbnail_url) as resp2:
                        if resp2.status != 200:
                            return None
                        image_data = await resp2.read()
                else:
                    image_data = await resp.read()
                    
                filepath = f"cache/thumb_{videoid}.png"
                async with aiofiles.open(filepath, mode="wb") as f:
                    await f.write(image_data)
                    
        image_path = f"cache/thumb_{videoid}.png"
        original_img = Image.open(image_path).convert("RGB")
        
        # 1. အပြင်ဘက် နောက်ခံအထွေထွေ (Blur Background)
        bg_width, bg_height = 1280, 720
        scaled_bg = original_img.resize((bg_width, bg_height), Image.Resampling.LANCZOS)
        background = scaled_bg.filter(ImageFilter.GaussianBlur(35))
        darken = Image.new("RGBA", (bg_width, bg_height), (10, 10, 15, 200))
        background = Image.alpha_composite(background.convert("RGBA"), darken).convert("RGB")

        # 2. ပုံစံတူ Apple Music Player Card (အဓိက အမည်းရောင် Box ကြီး)
        # Card Size: 1060 x 560 (အလယ်တည့်တည့်မှာ ထားမည်)
        card_w, card_h = 1060, 560
        card_x = (bg_width - card_w) // 2
        card_y = (bg_height - card_h) // 2
        
        card_layer = Image.new("RGBA", (bg_width, bg_height), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_layer)
        
        # Apple Music Player လိုမျိုး ထောင့်ဝိုင်းဝိုင်းနဲ့ အမည်းရောင် Card
        card_draw.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=35,
            fill=(25, 25, 30, 240),
            outline=(255, 255, 255, 30),
            width=2
        )
        
        # 3. ဘယ်ဘက်ခြမ်း Square Thumbnail (Album Art)
        # Size: 440 x 440
        thumb_size = 440
        thumb_x = card_x + 50
        thumb_y = card_y + 60
        
        orig_w, orig_h = original_img.size
        min_dim = min(orig_w, orig_h)
        left = (orig_w - min_dim) // 2
        top = (orig_h - min_dim) // 2
        square_img = original_img.crop((left, top, left + min_dim, top + min_dim))
        album_art = square_img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        
        # Album Art ကို ထောင့်အနည်းငယ်ဝိုင်းစေရန် Mask လုပ်ခြင်း
        mask = Image.new("L", (thumb_size, thumb_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, thumb_size, thumb_size], radius=16, fill=255)
        
        card_layer.paste(album_art, (thumb_x, thumb_y), mask)
        
        background = Image.alpha_composite(background.convert("RGBA"), card_layer).convert("RGB")
        draw = ImageDraw.Draw(background)

        # Fonts ချိန်ညှိခြင်း
        try:
            font_title = ImageFont.truetype('assets/font.ttf', 36)
            font_sub = ImageFont.truetype('assets/font.ttf', 24)
            font_time = ImageFont.truetype('assets/font.ttf', 20)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            font_time = ImageFont.load_default()

        # 4. ညာဘက်ခြမ်း Text များနှင့် Media Controls
        text_x = thumb_x + thumb_size + 50
        text_area_w = card_x + card_w - text_x - 50
        
        # Device Header (ဥပမာ - iPhone 🎧)
        draw.text((text_x, card_y + 65), "iPhone  🎧", font=font_sub, fill=(150, 150, 160))
        
        # သီချင်းနာမည်
        draw.text((text_x, card_y + 105), song_title[:32], font=font_title, fill=(255, 255, 255))
        
        # Artist / Channel Name
        draw.text((text_x, card_y + 155), artist_name, font=font_sub, fill=(160, 160, 170))

        # 5. Progress Bar (အလယ်ဗဟို မျဉ်းကြောင်း)
        bar_y = card_y + 225
        bar_w = text_area_w
        bar_h = 6
        
        # နောက်ခံမီးခိုးရောင်မျဉ်း
        draw.rounded_rectangle([text_x, bar_y, text_x + bar_w, bar_y + bar_h], radius=3, fill=(70, 70, 80))
        # လက်ရှိသွားနေသော အဖြူရောင်မျဉ်း (ဥပမာ - 40% ခန့်)
        progress_w = int(bar_w * 0.4)
        draw.rounded_rectangle([text_x, bar_y, text_x + progress_w, bar_y + bar_h], radius=3, fill=(240, 240, 240))
        
        # အချိန်စာသားများ (1:27 နှင့် -0:55)
        draw.text((text_x, bar_y + 15), "1:27", font=font_time, fill=(150, 150, 160))
        draw.text((text_x + bar_w - 45, bar_y + 15), "-0:55", font=font_time, fill=(150, 150, 160))

        # 6. Media Control Buttons (Backward, Play/Pause, Forward လေးများ ကိုယ်တိုင်ဆွဲခြင်း)
        ctrl_y = card_y + 350
        # ခလုတ်များရှိမည့် နေရာကို ညာဘက်ခြမ်း Text Area ထဲတွင် အလယ်တည့်တည့် ပုံစံဖော်မည်
        center_ctrl_x = text_x + (text_area_w // 2) - 20
        
        # Backward Button (◀◀)
        draw.polygon([(center_ctrl_x - 60, ctrl_y + 18), (center_ctrl_x - 35, ctrl_y + 5), (center_ctrl_x - 35, ctrl_y + 31)], fill=(220, 220, 220))
        draw.polygon([(center_ctrl_x - 35, ctrl_y + 18), (center_ctrl_x - 10, ctrl_y + 5), (center_ctrl_x - 10, ctrl_y + 31)], fill=(220, 220, 220))

        # Pause / Play Button ( || အစား ဒေါင်လိုက်တိုင်နှစ်ခု - Pause ပုံစံ)
        draw.rounded_rectangle([center_ctrl_x + 10, ctrl_y + 4, center_ctrl_x + 22, ctrl_y + 32], radius=3, fill=(255, 255, 255))
        draw.rounded_rectangle([center_ctrl_x + 30, ctrl_y + 4, center_ctrl_x + 42, ctrl_y + 32], radius=3, fill=(255, 255, 255))

        # Forward Button (▶▶)
        draw.polygon([(center_ctrl_x + 70, ctrl_y + 5), (center_ctrl_x + 70, ctrl_y + 31), (center_ctrl_x + 95, ctrl_y + 18)], fill=(220, 220, 220))
        draw.polygon([(center_ctrl_x + 95, ctrl_y + 5), (center_ctrl_x + 95, ctrl_y + 31), (center_ctrl_x + 120, ctrl_y + 18)], fill=(220, 220, 220))

        # ပုံဟောင်းဖယ်ရှားပြီး သိမ်းဆည်းခြင်း
        if os.path.exists(image_path):
            os.remove(image_path)
            
        background.save(cache_path, quality=95)
        return cache_path

    except Exception as e:
        logging.error(f"Error generating Apple Music style thumbnail for {videoid}: {e}")
        return None
