# ATLEAST GIVE CREDITS IF YOU STEALING :(((((((((((((((((((((((((((((((((((((
# ELSE NO FURTHER PUBLIC THUMBNAIL UPDATES

import logging
import os
import aiofiles
import aiohttp
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from py_yt import VideosSearch

logging.basicConfig(level=logging.INFO)

async def gen_thumb(videoid: str):
    try:
        if os.path.isfile(f"cache/{videoid}_v4.png"):
            return f"cache/{videoid}_v4.png"

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            thumbnail_data = result.get("thumbnails")
            if thumbnail_data:
                thumbnail = thumbnail_data[0]["url"].split("?")[0]
            else:
                thumbnail = None

        if not thumbnail:
            return None

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    filepath = f"cache/thumb{videoid}.png"
                    async with aiofiles.open(filepath, mode="wb") as f:
                        await f.write(await resp.read())
                    
        image_path = f"cache/thumb{videoid}.png"
        img = Image.open(image_path).convert("RGB")
        
        # 1. နောက်ခံအတွက် ပုံကို 1280x720 ဖြည့်ပြီး Blur (မှုန်ဝါး) လုပ်ခြင်း
        background = img.resize((1280, 720))
        background = background.filter(ImageFilter.GaussianBlur(25))
        
        # နောက်ခံကို အနည်းငယ်မှောင်စေခြင်း (စာသားနှင့် ပုံပေါ်လွင်စေရန်)
        darker = Image.new("RGB", background.size, (0, 0, 0))
        background = Image.blend(background, darker, 0.5)

        # 2. ပုံအလယ်က အဓိကပုံကို အမည်းကွက်မပေါ်စေဘဲ 1280x720 မျက်နှာပြင်ပေါ်သို့ အပြည့်အစုံ ဖြန့်ကျက်ခြင်း (Cover Mode)
        # အစင်းကြောင်းများ မပေါ်စေရန် Image.Resampling.LANCZOS ကို သုံးထားသည်
        img_resized = img.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # နောက်ခံပေါ်သို့ အပြည့်တင်ခြင်း (အမည်းကွက်လုံးဝ မရှိတော့ပါ)
        background.paste(img_resized, (0, 0))

        # ပုံပေါ်တွင် အလွှာပါးလေး ထပ်အုပ်ပေးခြင်းဖြင့် စာသားများ ပိုထင်ရှားစေခြင်း
        overlay = Image.new("RGBA", background.size, (0, 0, 0, 80))
        background = Image.alpha_composite(background.convert("RGBA"), overlay).convert("RGB")

        # 3. နာမည်ထည့်သွင်းခြင်း
        draw = ImageDraw.Draw(background)
        name_to_draw = "@HANTHAR999" 
        
        try:
            font = ImageFont.truetype('assets/font.ttf', 100)
        except Exception:
            font = ImageFont.load_default()

        try:
            bbox = draw.textbbox((0, 0), name_to_draw, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            text_width = draw.textlength(name_to_draw, font=font)
            text_height = 40

        # နာမည်ကို ညာဘက်အောက်ထောင့် (သို့မဟုတ်) ကြည့်ကောင်းမည့်နေရာတွင် ချելရန်
        name_x = 1280 - text_width - 50  # ညာဘက်စွန်းမှ ကွာဟချက်
        name_y = 720 - text_height - 40  # အောက်ခြေမှ ကွာဟချက်
        
        # စာသားနောက်ခံ ပိုပေါ်လွင်စေရန် အရိပ်သဘောမျိုး အမည်းရောင်လေးဖြင့် အစွန်းထုတ်ရေးခြင်း
        draw.text((name_x + 2, name_y + 2), name_to_draw, font=font, fill=(0, 0, 0))
        draw.text((name_x, name_y), name_to_draw, font=font, fill=(255, 255, 255))
        
        if os.path.exists(image_path):
            os.remove(image_path)
            
        background_path = f"cache/{videoid}_v4.png"
        background.save(background_path)
        
        return background_path

    except Exception as e:
        logging.error(f"Error generating thumbnail for video {videoid}: {e}")
        return None
