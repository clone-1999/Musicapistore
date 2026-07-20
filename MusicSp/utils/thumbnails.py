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
        
        # -----------------------------------------------------------------------
        # ပုံစံအသစ်: မှုန်ဝါးဝါး နောက်ခံ + မူရင်းပုံအလယ် + သင့်နာမည်
        # -----------------------------------------------------------------------
        img = Image.open(image_path).convert("RGB")
        
        # 1. နောက်ခံအတွက် ပုံကို 1280x720 ဆွဲချဲ့ပြီး Blur (မှုန်ဝါး) လုပ်ခြင်း
        background = img.resize((1280, 720))
        background = background.filter(ImageFilter.GaussianBlur(20))
        
        # ပုံပိုမိုမှောင်ပြီး ပေါ်လွင်စေရန် အမည်းစက္ကူပါးလေး အုပ်ခြင်း
        darker = Image.new("RGB", background.size, (0, 0, 0))
        background = Image.blend(background, darker, 0.4)

        # 2. မူရင်းပုံကို အချိုးအစားမပျက်ဘဲ အရွယ်အစားချိန်ခြင်း
        img.thumbnail((700, 700))
        
        # 3. နောက်ခံပေါ်တွင် မူရင်းပုံကို အလယ်တည့်တည့်သို့ တင်ခြင်း
        w, h = img.size
        x_offset = (1280 - w) // 2
        y_offset = (720 - h) // 2
        background.paste(img, (x_offset, y_offset))
        
        # -----------------------------------------------------------------------
        # 4. 
        # ----------------------------------------------------
        draw = ImageDraw.Draw(background)
        
        # 
        name_to_draw = "@HANTHAR999" 
        
        # Font သတ်မှတ်ခြင်း (Load default ကိုသုံးထားသောကြောင့် အင်္ဂလိပ်စာအတွက် အဆင်ပြေသည်)
        # မြန်မာစာ လိုအပ်ပါက အောက်တွင်ဖော်ပြထားသော .ttf လမ်းကြောင်းကို သုံးရပါမည်
        try:
            # အကယ်၍ သင့်စက်တွင် မြန်မာဖောင့်ဖိုင်ရှိပါက ဤလိုင်းကိုသုံးပါ (ဥပမာ: 'assets/font.ttf')
            # font = ImageFont.truetype('path/to/your/MyanmarFont.ttf', 36)
            
            # လက်ရှိ Font မရှိသေးလျှင် default font သုံးသည် (မြန်မာစာ ပျက်နိုင်သည်)
            font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # နာမည်ရဲ့ အတိုင်းအတာကို တိုင်းတာခြင်း (အလယ်ဗဟိုထားရန်)
        # (Load Default Font အတွက် textlength မရနိုင်ပါက အောက်ပါအတိုင်း hardcode တန်ဖိုးသုံးနိုင်သည်)
        try:
            bbox = draw.textbbox((0, 0), name_to_draw, font=font)
            text_width = bbox[2] - bbox[0]
            # text_height = bbox[3] - bbox[1]
        except AttributeError:
            # Pillow version အဟောင်းများအတွက်
            text_width = draw.textlength(name_to_draw, font=font)

        # 
        name_x = (1280 - text_width) // 2
        name_y = 630 
        
        
        draw.text((name_x, name_y), name_to_draw, font=font, fill=(255, 255, 255))
        
        # -----------------------------------------------------------------------

        if os.path.exists(image_path):
            os.remove(image_path)
            
        background_path = f"cache/{videoid}_v4.png"
        background.save(background_path)
        
        return background_path

    except Exception as e:
        logging.error(f"Error generating thumbnail for video {videoid}: {e}")
        return None
