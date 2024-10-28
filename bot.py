# 


import asyncio
import aiohttp
import aiofiles
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
import os
import time
import shutil
from functools import partial
from concurrent.futures import ProcessPoolExecutor
from merger import merger



# =========== #
itemShopFont = 'assets/BurbankBigRegular-BlackItalic.otf'  # the font you wish to use
overlayPath = "assets/overlay.png"

checkForOgItems = True  # If false, it will not generate the og items image.
ogThreshold = 200  # threshold to consider an item 'og' (isn't used if checkForOgItems is false)
# =========== #





async def download_image(session, url, filename, folder='cache'):
    try:
        os.makedirs(folder, exist_ok=True)
        fpath = f'{folder}/{filename}.png'
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(fpath, 'wb') as f:
                    await f.write(await response.read())
                return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
    return False


def process_item(item_data, overlay, font_path):
    filename = item_data['filename']
    diff = item_data['diff']
    price = item_data['price']
    name = item_data['name']

    try:
        with Image.open(f'cache/{filename}.png') as background:
            background = background.resize((512, 512))
            img = Image.new("RGBA", (512, 512))
            img.paste(background)

            img.paste(overlay, (0, 0), overlay)

            draw = ImageDraw.Draw(img)

            font = ImageFont.truetype(font_path, 35)
            draw.text((256, 420), name, font=font, fill='white', anchor='ms')

            diff_text = 'NEW!' if 'NEW!' in diff else f'LAST SEEN: {diff} day{"s" if diff != "1" else ""} ago'
            font = ImageFont.truetype(font_path, 15)
            draw.text((256, 450), diff_text, font=font, fill='white', anchor='ms')

            font = ImageFont.truetype(font_path, 40)
            draw.text((256, 505), f'{price}', font=font, fill='white', anchor='ms')

            img.save(f'cache/{filename}.png')
    except Exception as e:
        print(f"Error processing item {filename}: {e}")


def process_og_item(item, overlay, font_path):
    filename = f"OG{item['id']}"
    try:
        with Image.open(f'ogcache/{filename}.png') as background:
            background = background.resize((512, 512))
            img = Image.new("RGBA", (512, 512))
            img.paste(background)

            img.paste(overlay, (0, 0), overlay)

            draw = ImageDraw.Draw(img)

            font = ImageFont.truetype(font_path, 35)
            draw.text((256, 420), item['name'], font=font, fill='white', anchor='ms')

            last_seen_days = item['lastseen_days']
            diff_text = f'LAST SEEN: {last_seen_days} day{"s" if last_seen_days != "1" else ""} ago'
            font = ImageFont.truetype(font_path, 15)
            draw.text((256, 450), diff_text, font=font, fill='white', anchor='ms')

            price = item['price']
            font = ImageFont.truetype(font_path, 40)
            draw.text((256, 505), f'{price}', font=font, fill='white', anchor='ms')

            img.save(f'ogcache/{filename}.png')
    except Exception as e:
        print(f"Error processing OG item {filename}: {e}")


async def genshop():
    print("Generating the Fortnite Item Shop.")

    shutil.rmtree('cache', ignore_errors=True)
    os.makedirs('cache', exist_ok=True)

    start = time.time()

    async with aiohttp.ClientSession() as session:
        async with session.get('https://fortnite-api.com/v2/shop/br/combined') as resp:
            if resp.status != 200:
                return
            data = (await resp.json())['data']

        currentdate = data['date'][:10]

        print('\nFetching shop data...')
        featured = data['featured']
        item_data_list = []

        if featured:
            for entry in featured['entries']:
                i = entry

                url = None

                new_display_asset = i.get('newDisplayAsset', {})
                material_instances = new_display_asset.get('materialInstances', [])
                if material_instances:
                    images = material_instances[0].get('images', {})
                    url = images.get('Background') or images.get('OfferImage')
                else:
                    render_images = new_display_asset.get('renderImages', [])
                    if render_images:
                        url = render_images[0].get('image')

                if not url:
                    url = i['items'][0]['images']['icon']

                last_seen = i['items'][0].get('shopHistory', [])
                last_seen_date = last_seen[-2][:10] if len(last_seen) >= 2 else 'NEW!'
                price = i['finalPrice']

                if i.get('bundle'):
                    url = i['bundle']['image']
                    filename = f"zzz{i['bundle']['name']}"
                    name = i['bundle']['name']
                else:
                    filename = i['items'][0]['id']
                    name = i['items'][0]['name']

                if last_seen_date != 'NEW!':
                    diff_days = (datetime.strptime(currentdate, "%Y-%m-%d") - datetime.strptime(last_seen_date,
                                                                                                "%Y-%m-%d")).days
                    diff = str(diff_days or 1)
                else:
                    diff = 'NEW!'

                item_data = {
                    'filename': filename,
                    'url': url,
                    'i': i,
                    'diff': diff,
                    'price': price,
                    'name': name,
                    'currentdate': currentdate,
                }
                item_data_list.append(item_data)

            download_tasks = [download_image(session, item['url'], item['filename']) for item in item_data_list]
            await asyncio.gather(*download_tasks)

            overlay = Image.open(overlayPath).convert('RGBA')
            process_partial = partial(process_item, overlay=overlay, font_path=itemShopFont)

            with ProcessPoolExecutor() as executor:
                loop = asyncio.get_running_loop()
                tasks = [loop.run_in_executor(executor, process_partial, item_data) for item_data in item_data_list]
                await asyncio.gather(*tasks)

            print(f'Done generating "{len(item_data_list)}" items in the Featured section.')

            print(f'\nGenerated {len(item_data_list)} items from the {currentdate} Item Shop.')

            print('\nMerging images...')
            await asyncio.to_thread(merger, ogitems=False, currentdate=currentdate)

            end = time.time()

            print(f"IMAGE GENERATING COMPLETE - Generated image in {round(end - start, 2)} seconds!")

            img = Image.open(f'shops/shop {currentdate}.jpg')
            img.show()


async def ogitems():
    shutil.rmtree('ogcache', ignore_errors=True)
    os.makedirs('ogcache', exist_ok=True)

    start = time.time()

    async with aiohttp.ClientSession() as session:
        async with session.get('https://fortnite-api.com/v2/shop/br/combined') as resp:
            if resp.status != 200:
                return
            data = (await resp.json())['data']
            featured = data['featured']
            currentdate = data['date'][:10]

        resultlist = []
        for entry in featured['entries']:
            for i in entry['items']:
                shophistory = i.get('shopHistory', [])
                lastseen_date = shophistory[-2][:10] if len(shophistory) >= 2 else currentdate
                days_since_last_seen = (datetime.strptime(currentdate, "%Y-%m-%d") - datetime.strptime(lastseen_date,
                                                                                                       "%Y-%m-%d")).days
                if days_since_last_seen >= ogThreshold:
                    price = entry['finalPrice']
                    resultlist.append({
                        "name": i['name'],
                        "id": i['id'],
                        "lastseen_days": str(days_since_last_seen),
                        "lastseen_date": lastseen_date,
                        "type": i['type']['displayValue'],
                        "price": price,
                        "item_data": i
                    })

        if not resultlist:
            print('There are no rare items.')
            return

        print('Rare cosmetics have been found')
        rarest_item = max(resultlist, key=lambda x: int(x['lastseen_days']))
        print(f"The rarest item is the {rarest_item['name']} {rarest_item['type']}, which hasn't been seen in {rarest_item['lastseen_days']} days!")

        print("Rare items:")
        for item in resultlist:
            print(f"- {item['name']} ({item['lastseen_days']} days)\n")

        download_tasks = []
        for item in resultlist:
            filename = f"OG{item['id']}"
            fpath = f'ogcache/{filename}.png'
            if not os.path.exists(fpath):
                itm = item['item_data']
                url = None

                new_display_asset = itm.get('newDisplayAsset', {})
                material_instances = new_display_asset.get('materialInstances', [])
                if material_instances:
                    images = material_instances[0].get('images', {})
                    url = images.get('Background') or images.get('OfferImage')
                else:
                    render_images = new_display_asset.get('renderImages', [])
                    if render_images:
                        url = render_images[0].get('image')

                if not url:
                    url = itm['images']['icon']

                if url:
                    download_tasks.append(download_image(session, url, filename, folder='ogcache'))

        await asyncio.gather(*download_tasks)

        overlay = Image.open(overlayPath).convert('RGBA')
        process_partial = partial(process_og_item, overlay=overlay, font_path=itemShopFont)

        with ProcessPoolExecutor() as executor:
            loop = asyncio.get_running_loop()
            tasks = [loop.run_in_executor(executor, process_partial, item) for item in resultlist]
            await asyncio.gather(*tasks)

        await asyncio.to_thread(merger, ogitems=True, currentdate=currentdate)
        print(f"Saved in shops/og folder as 'OGitems {currentdate}.jpg'.\n")

        end = time.time()
        print(f"OG ITEMS IMAGE GENERATING COMPLETE - Generated image in {round(end - start, 2)} seconds!")


async def main():
    if checkForOgItems:
        await asyncio.gather(
            genshop(),
            ogitems()
        )
    else:
        print("Og items is disabled.")
        await genshop()


if __name__ == '__main__':
    asyncio.run(main())
