import logging
import os
import aiofiles
import aiohttp
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from py_yt import VideosSearch

logging.basicConfig(level=logging.INFO)

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_v5.png"
        if os.path.isfile(cache_path):
            return cache_path

        # Cache folder ရှိမရှိ စစ်ဆေးပြီး ဖန်တီးပေးခြင်း
        os.makedirs("cache", exist_ok=True)

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        thumbnail = None
        for result in (await results.next())["result"]:
            thumbnail_data = result.get("thumbnails")
            if thumbnail_data:
                thumbnail = thumbnail_data[0]["url"].split("?")[0]

        if not thumbnail:
            return None

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    filepath = f"cache/thumb_{videoid}.png"
                    async with aiofiles.open(filepath, mode="wb") as f:
                        await f.write(await resp.read())
                    
        image_path = f"cache/thumb_{videoid}.png"
        img = Image.open(image_path).convert("RGB")
        
        # 1. နောက်ခံ (Background): ကို Blur လှလှလေးလုပ်ပြီး အနည်းငယ် မှောင်ပေးခြင်း
        background = img.resize((1280, 720), Image.Resampling.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(25))
        
        # အရောင်တောက်တောက်နဲ့ ဇိမ်ကျကျဖြစ်အောင် Gradient/Dark Overlay အနည်းငယ်သုံးခြင်း
        darker = Image.new("RGB", background.size, (10, 10, 15))
        background = Image.blend(background, darker, 0.45)

        # 2. ပင်မပုံ (Foreground Image): အလယ်တွင် 1280x720 အზომအဆနဲ့ အလှဆုံး ပေါ်လာစေရန်
        # (အကယ်၍ ပုံအပြည့်မဟုတ်ဘဲ Frame လေးနဲ့ လိုချင်ရင် ဒီနေရာမှာ Size လျှော့လို့ရပါတယ်)
        img_resized = img.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # ပုံပေါ်မှာ Gradient Vignette ပုံစံလေးဖြစ်စေရန် (အစွန်းတွေက အမည်းရောင်စပ်သွားအောင်)
        background.paste(img_resized, (0, 0))

        # 3. Modern Watermark / Channel Name Badge (ညာဘက်အောက်ထောင့်)
        draw = ImageDraw.Draw(background)
        name_to_draw = "@HANTHAR999" 
        
        font_size = 48
        try:
            font = ImageFont.truetype('assets/font.ttf', font_size)
        except Exception:
            font = ImageFont.load_default()

        # Text Size တိုင်းတာခြင်း
        try:
            bbox = draw.textbbox((0, 0), name_to_draw, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            text_width = draw.textlength(name_to_draw, font=font)
            text_height = font_size

        # Badge Padding & Position
        padding_x = 30
        padding_y = 18
        box_x2 = 1280 - 50
        box_y2 = 720 - 50
        box_x1 = box_x2 - text_width - (padding_x * 2)
        box_y1 = box_y2 - text_height - (padding_y * 2)

        # Semi-transparent Glass Box (ဖန်သားပြင်ကဲ့သို့ နောက်ခံလေး)
        box_layer = Image.new("RGBA", background.size, (0, 0, 0, 0))
        box_draw = ImageDraw.Draw(box_layer)
        
        # Rounded Box ဆွဲခြင်း (Background အမည်းရောင် ပိုစိုပြီး အနားကွပ်လေးပါ ထည့်ခြင်း)
        box_draw.rounded_rectangle(
            [box_x1, box_y1, box_x2, box_y2], 
            radius=12, 
            fill=(15, 15, 20, 210), 
            outline=(255, 255, 255, 60), 
            width=2
        )
        background = Image.alpha_composite(background.convert("RGBA"), box_layer).convert("RGB")

        # စာသားကို Shadow လေးနဲ့အတူ ပိုပေါ်လွင်အောင် ရေးဆွဲခြင်း
        draw = ImageDraw.Draw(background)
        text_x = box_x1 + padding_x
        text_y = box_y1 + padding_y - 2
        
        # Text Shadow (အရိပ်လေးထိုးပေးခြင်း)
        draw.text((text_x + 2, text_y + 2), name_to_draw, font=font, fill=(0, 0, 0))
        # Main Text (အဖြူရောင် တောက်တောက်)
        draw.text((text_x, text_y), name_to_draw, font=font, fill=(255, 255, 255))
        
        # ပုံဟောင်းဖယ်ရှားခြင်း
        if os.path.exists(image_path):
            os.remove(image_path)
            
        background.save(cache_path, quality=95)
        return cache_path

    except Exception as e:
        logging.error(f"Error generating thumbnail for video {videoid}: {e}")
        return None
