import json
from os import getenv

import requests
import vk_api
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("ACCESS_TOKEN")
GROUP_ID = getenv("GROUP_ID")
DOMAIN = getenv("DOMAIN")


def get_vk_data(group_id: str, api_method) -> dict:
    """Получение информации о товарах в группе VK"""
    print("Начинаю собирать информацию о товарах с VK...")
    response = api_method.market.get(owner_id=-int(group_id), count=200)
    products = response["items"]
    data = {}
    value_count = 0
    for i in products:
        data[i["title"].lower()] = i["id"]
        value_count += 1
    print(f"Всего из VK получено {value_count} значений")
    return data


def get_site_data(urls: list):
    """Получение информации о товарах с сайта"""
    print(f"Начинаю сбор информации с сайта {DOMAIN}...")
    data = {}
    total_count = 0
    for url in urls:
        url_count = 0
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        for product in soup.find_all("div", class_="eventCart"):
            name = product.find("a", class_="t1").text.strip()
            delivery_price = (
                product.find("div", class_="price1")
                .find("div", class_="price")
                .text.strip()
                .split()[0]
            )
            pickup_price = (
                product.find("div", class_="price2")
                .find("div", class_="price")
                .text.strip()
                .split()[0]
            )
            data[name] = [delivery_price, pickup_price]
            url_count += 1
        total_count += url_count
        print(f"Из {url} получено {url_count} позиций")
    print(f"Всего с сайта {DOMAIN} получено {total_count} позиций")

    return data


def merge_data(vk_data, site_data):
    """Добавляем к ID продуктов из VK цены с сайта"""
    print("Начинаю соединять таблицы...")
    result = {}
    unmatch = []

    for data in site_data.items():
        title = data[0]
        numbers = data[1]
        if title.lower() in vk_data:
            result[title] = [vk_data[title.lower()]] + numbers
        else:
            unmatch.append(title)

    print(f"Всего соединено {len(result)} позиций")
    if len(unmatch) > 0:
        print(f"В VK не найдено {len(unmatch)} позиций")
        with open("unmatch.json", "w", encoding="utf-8") as json_file:
            json.dump(unmatch, json_file, ensure_ascii=False, indent=4)
        print(f"Создан файл 'unmatch.json'")
    return result


def update_data(data, group_id, api_method):
    """Обновляем цены и описание в VK"""
    print("Начинаю обновлять позиции в VK...")
    value_count = 0
    for id, delivery_price, pickup_price in data.values():
        address = f"-{group_id}_{id}"
        response = api_method.market.getById(item_ids=address)
        desc = response["items"][0]["description"].split("\n")[2:]
        text_price1 = f"Стоимость на доставку: {delivery_price} ₽\n"
        text_price2 = f"Стоимость на самовывоз: {pickup_price} ₽\n"
        desc = text_price1 + text_price2 + "\n".join(desc)
        api_method.market.edit(
            owner_id=-int(group_id), item_id=id, description=desc, price=pickup_price
        )
        value_count += 1
    print(f"Всего обновлено {value_count} позиций")


def start():
    urls = [
        f"https://{DOMAIN}/products/sushi/",
        f"https://{DOMAIN}/products/rolly/",
        f"https://{DOMAIN}/products/goryachie-rolly/",
        f"https://{DOMAIN}/products/sety/",
        f"https://{DOMAIN}/products/mini-sety/",
        f"https://{DOMAIN}/products/sousy/",
        f"https://{DOMAIN}/products/napitki/",
        f"https://{DOMAIN}/products/dopolnitelno/",
    ]
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    vk_data = get_vk_data(GROUP_ID, vk)
    site_data = get_site_data(urls)
    merged_data = merge_data(vk_data, site_data)

    update_data(merged_data, GROUP_ID, vk)


if __name__ == "__main__":
    start()
