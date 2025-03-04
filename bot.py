import asyncio
import json

import aiofiles
import concurrent.futures
from pyVinted import Vinted

VINTED_ENDPOINTS = {
    "adidas": "https://www.vinted.pl/catalog?search_text=adidas&order=newest_first&page=1",
    "nike": "https://www.vinted.pl/catalog?search_text=nike&order=newest_first&page=1",
    "ralph": "https://www.vinted.pl/catalog?search_text=ralph%20lauren&page=1&order=newest_first"
}
vinted = Vinted()

async def fetch_items(url):
    """
    Scrapes data from Vinted and organize it in a dictionary: {'id': ['title', 'price', ''url]}
    :param url:
    :return:
    """
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(pool, vinted.items.search, url)
    item_data = {
        str(item.id): {
            "title": item.title,
            "price": item.price,
            "url": item.url,
            "is_new": item.isNewItem()
        } for item in response
    }
    return item_data

def initialize_files(brand_names):
    file_names = []
    for brand_name in brand_names:
        file_name = brand_name
        brand_name = open(f"./data/{brand_name}.txt", "w")
        brand_name.close()
        file_names.append(file_name)
    return file_names

async def read_data_from_file(file_name):
    async with aiofiles.open(f"./data/{file_name}.txt", "r") as file:
        content = await file.read()
    if content != '':
        fixed_content = json.loads(content)
    else:
        return {}
    return {file_name: fixed_content}

async def read_data_from_all_files(file_list):
    tasks = [read_data_from_file(file) for file in file_list]
    results = await asyncio.gather(*tasks)
    return {file_name: content for file_data in results for file_name, content in file_data.items()}

async def write_to_file(filename, data):
    """
    Saves Vinted data to file
    :return:
    """
    async with aiofiles.open(f"./data/{filename}.txt", "w") as file:
        await file.write(json.dumps(data))

async def write_to_all_files(data_list):
    tasks = [write_to_file(file, data) for file, data in data_list.items()]
    await asyncio.gather(*tasks)

async def compare_data_from_file(old_dict, new_dict):
    """
    Checks if any new item was added by comparing new dict keys with old dict keys
    and if these items are actually new
    :param old_dict:
    :param new_dict:
    :return:
    """
    new_items = {}
    if not old_dict:
        print("Looking for items...")
        return new_items
    for position in new_dict:
        if position not in old_dict and new_dict[position]['is_new']:
            new_items[position] = new_dict[position]
    return new_items


async def compare_data_from_all_files(old_data_list, current_data_list):
    tasks = []
    for brand in old_data_list:
        old_data = old_data_list[brand]
        new_data = current_data_list[brand]
        tasks.append(compare_data_from_file(old_data, new_data))
    results = await asyncio.gather(*tasks)
    return_value = {}
    for index, key in enumerate(old_data_list):
        return_value[key] =  results[index]
    return return_value

async def main():
    files = initialize_files(VINTED_ENDPOINTS)

    while True:
        """Reads last items data from files"""
        data = await read_data_from_all_files(files)

        """Gets latest items data"""
        async with asyncio.TaskGroup() as tg:
            tasks = {
                brand: tg.create_task(fetch_items(VINTED_ENDPOINTS[brand])) for brand in VINTED_ENDPOINTS
            }
        results = {brand: task.result() for brand, task in tasks.items()}
        await write_to_all_files(results)

        new_items = await compare_data_from_all_files(data, results)
        if any(new_items[brand] for brand in new_items):
            print("\nNew items:")
            for brand in new_items:
                if len(new_items[brand]) != 0:
                    print(f"\nBrand: {brand.capitalize()}")
                    for item_id, item_data in new_items[brand].items():
                        print(f"{item_id}: {item_data['title']}, {item_data['price']} PLN, {item_data['url']}")
        else:
            print("\nNo new items found")

        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
