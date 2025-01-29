import time
from pyVinted import Vinted

VINTED_ENDPOINT = "https://www.vinted.pl/catalog?search_text=adidas&order=newest_first&page=1"
vinted = Vinted()

def fetch_items(url):
    """
    Scrapes data from Vinted and organize it in a dictionary: {'id': ['title', 'price', ''url]}
    :param url:
    :return:
    """
    response = vinted.items.search(url)
    item_data = {item.id: [item.title, item.price, item.url, item.isNewItem()] for item in response}
    return item_data

def dump_to_file(data, filename: str = "clothes.txt"):
    """
    Saves Vinted data to file
    :param data:
    :param filename:
    :return:
    """
    with open(filename, "w") as file:
        for pos in data:
            file.write(f"{pos}: {data[pos]}\n")
        file.write("\n")

def compare_data(old_dict, new_dict):
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
        if str(position) not in old_dict and new_dict[position][3]:
            new_items[position] = new_dict[position]
    return new_items

def print_new_items(new_item_list):
    if len(new_item_list) == 0:
        print('No new items in given category')
    else:
        print(f"New items added:")
        for key, item in new_item_list.items():
            print(f"{key}: {item[0]}: {item[1]} PLN ,{item[2]}")

if __name__ == "__main__":
    with open("clothes.txt", "w")as createFile:
        createFile.write("")

    while True:
        with open("clothes.txt", "r") as f:
            old_data = f.read()
        new_data = fetch_items(VINTED_ENDPOINT)
        dump_to_file(new_data)
        item_list = compare_data(old_data, new_data)
        print_new_items(item_list)

        time.sleep(10)
