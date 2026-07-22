import logging
import os
import aiofiles
import aiohttp
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import textwrap

logging.basicConfig(level=logging.INFO)

async def gen_thumb(videoid: str, song_title: str):
    try:
        cache_path = f"cache/{videoid}_v9.png"
        if os.path.isfile(cache_path):
            return cache_path

        os.makedirs("cache", exist_ok=True)

        # YouTube Thumbnail Direct URL (py_yt မလိုတော့ပါ)
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
        
        # 1. နောက်ခံ (Background): Blur & Dark Gradient
        bg_width, bg_height = 1280, 720
        orig_w, orig_h = original_img.size
        aspect = orig_w / orig_h
        
        if aspect > bg_width / bg_height:
            new_w = bg_width
            new_h = int(new_w / aspect)
        else:
            new_h = bg_height
            new_w = int(new_h * aspect)
            
        scaled_bg = original_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        background = Image.new("RGB", (bg_width, bg_height), (10, 10, 15))
        background.paste(scaled_bg, ((bg_width - new_w) // 2, (bg_height - new_h) // 2))
        
        background = background.filter(ImageFilter.GaussianBlur(20))
        dark_overlay = Image.new("RGBA", (bg_width, bg_height), (0, 0, 0, 150))
        background = Image.alpha_composite(background.convert("RGBA"), dark_overlay).convert("RGB")

        # 2. ပင်မပုံ (Foreground Image) - ဘောင်အဖြူနှင့် ထည့်သွင်းခြင်း
        target_w, target_h = 640, 360
        
        if orig_w / orig_h > target_w / target_h:
            w_crop = int(orig_h * (target_w / target_h))
            img_cropped = original_img.crop(((orig_w - w_crop) // 2, 0, (orig_w + w_crop) // 2, orig_h))
        else:
            h_crop = int(orig_w * (target_h / target_w))
            img_cropped = original_img.crop((0, (orig_h - h_crop) // 2, orig_w, (orig_h + h_crop) // 2))
            
        foreground = img_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        border_size = 10
        bordered_img = Image.new("RGB", (target_w + border_size * 2, target_h + border_size * 2), (255, 255, 255))
        bordered_img.paste(foreground, (border_size, border_size))
        
        pos_x = (1280 - bordered_img.size[0]) // 2
        pos_y = 150 
        background.paste(bordered_img, (pos_x, pos_y))

        # 3. အောက်ခြေ Music Bar & Text
        bar_height = 140
        bar_y = 720 - bar_height
        gradient_layer = Image.new("RGBA", (1280, bar_height), (0, 0, 0, 0))
        gr_draw = ImageDraw.Draw(gradient_layer)
        for y in range(bar_height):
            alpha = int((y / bar_height) * 200) 
            gr_draw.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))
        
        background = Image.alpha_composite(background.convert("RGBA"), gradient_layer).convert("RGB")
        draw = ImageDraw.Draw(background)

        try:
            font_title = ImageFont.truetype('assets/font.ttf', 50)
            font_channel = ImageFont.truetype('assets/font.ttf', 30)
        except Exception:
            font_title = ImageFont.load_default()
            font_channel = ImageFont.load_default()

        # ဘယ်ဘက်တွင် အဝိုင်းလေးခံပြီး Play Button (Triangle) ကို ကိုယ်တိုင်ဆွဲပေးခြင်း (Icon ပုံပျောက်တာမရှိစေရန်)
        icon_box_size = 65
        icon_x = 50
        icon_y = bar_y + (bar_height - icon_box_size) // 2
        
        # အဝိုင်းနောက်ခံလေးခံခြင်း
        icon_layer = Image.new("RGBA", background.size, (0, 0, 0, 0))
        icon_draw = ImageDraw.Draw(icon_layer)
        icon_draw.ellipse([icon_x, icon_y, icon_x + icon_box_size, icon_y + icon_box_size], fill=(255, 255, 255, 40), outline=(255, 255, 255, 100), width=2)
        
        # Play Triangle ဆွဲခြင်း
        tri_x1 = icon_x + 24
        tri_y1 = icon_y + 20
        tri_x2 = icon_x + 24
        tri_y2 = icon_y + 45
        tri_x3 = icon_x + 45
        tri_y3 = icon_y + 32
        icon_draw.polygon([(tri_x1, tri_y1), (tri_x2, tri_y2), (tri_x3, tri_y3)], fill=(255, 255, 255))
        
        background = Image.alpha_composite(background.convert("RGBA"), icon_layer).convert("RGB")
        draw = ImageDraw.Draw(background)

        text_start_x = icon_x + icon_box_size + 25

        channel_name = "@HANTHAR999"
        try:
            chan_bbox = draw.textbbox((0, 0), channel_name, font=font_channel)
            chan_w = chan_bbox[2] - chan_bbox[0]
        except:
            chan_w = 150 

        wrapped_text = textwrap.fill(song_title, width=38) 
        
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (10,10)))
        text_h = 0
        lines = wrapped_text.split('\n')
        for line in lines:
            bbox = dummy_draw.textbbox((0, 0), line, font=font_title)
            text_h += (bbox[3] - bbox[1]) + 5 

        text_y = bar_y + (bar_height - text_h) // 2

        shadow_color = (0, 0, 0, 200)
        current_y = text_y
        for line in lines:
            line_bbox = draw.textbbox((0, 0), line, font=font_title)
            text_x = text_start_x 
            
            draw.text((text_x + 2, current_y + 2), line, font=font_title, fill=shadow_color)
            draw.text((text_x, current_y), line, font=font_title, fill=(255, 255, 255))
            current_y += (line_bbox[3] - line_bbox[1]) + 5

        chan_x = 1280 - chan_w - 40
        chan_y = bar_y + (bar_height - 30) // 2 - 5 
        
        draw.text((chan_x + 2, chan_y + 2), channel_name, font=font_channel, fill=shadow_color)
        draw.text((chan_x, chan_y), channel_name, font=font_channel, fill=(200, 200, 200))

        if os.path.exists(image_path):
            os.remove(image_path)
            
        background.save(cache_path, quality=95)
        return cache_path

    except Exception as e:
        logging.error(f"Error generating music thumbnail for {videoid}: {e}")
        return None
