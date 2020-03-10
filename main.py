import json
import requests
import re
from json2html import json2html


SHELTER_ID = "994"


def initialize_headers():
    initialization = requests.get("https://www.petango.com/shelter_pets")
    request_verification_token = re.search(
        '__RequestVerificationToken.*value="(.*)"', initialization.text
    ).group(1)
    headers = {
        "Connection": "keep-alive",
        "TabId": "278",
        "RequestVerificationToken": request_verification_token,
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12739.87.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.128 Safari/537.36",
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Sec-Fetch-Dest": "empty",
        "X-Requested-With": "XMLHttpRequest",
        "ModuleId": "983",
        "Origin": "https://www.petango.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Referer": initialization.url,
        "Accept-Language": "en-US,en;q=0.9",
        "dnt": "1",
    }

    return headers


def get_available_cats(headers):
    available_cats = []
    data = {
        "lostAnimals": False,
        "mustHavePhoto": False,
        "mustHaveVideo": False,
        "speciesId": "2",
        "shelterId": SHELTER_ID,
        "happyTails": False,
        "goodWithDogs": False,
        "goodWithCats": False,
        "recordAmount": "100",
        "moduleId": "983",
        "goodWithChildren": False,
        "gender": "M",
        "recordOffset": "0",
    }

    for age in ["Young", "Adult"]:
        data["age"] = age
        response = requests.post(
            "https://www.petango.com/DesktopModules/Pethealth.Petango/Pethealth.Petango.DnnModules.AnimalSearchResult/API/Main/Search",
            json=data,
            headers=headers,
        )

        response_cats = response.json()["items"]
        available_cats.extend(response_cats)

    return available_cats


def extract_cat_information(available_cats):
    cats_data = {}
    for cat_item in available_cats:
        cats_data[cat_item["name"]] = {
            "id": cat_item["id"],
            "breed": cat_item["breed"],
            "age": cat_item["age"],
            "url": cat_item["url"],
            "pictures": [],
        }

    return cats_data


def get_cat_descriptions(cats, headers):
    params = {
        "moduleId": "849",
        "clientZip": "null",
    }

    headers.update(
        {"TabId": "261", "ModuleId": "849", "Content-Type": None, "Origin": None,}
    )

    for cat, cat_data in cats.items():
        cat_id = cat_data["id"]
        print("grabbing cat {cat_id}".format(cat_id=cat_id))

        params["animalId"] = cat_id
        headers["Referer"] = cat_data["url"]

        response = requests.get(
            "https://www.petango.com/DesktopModules/Pethealth.Petango/Pethealth.Petango.DnnModules.AnimalDetails/API/Main/GetAnimalDetails",
            headers=headers,
            params=params,
        )
        response_json = response.json()
        cats[cat]["description"] = response_json["memo"]

        for key, value in response_json.items():
            if "photo" in key.lower():
                if value:
                    cats[cat]["pictures"].append(value)

    return cats


def write_json_to_file(cats_json):
    with open("cat_data.json", "w") as f:
        json.dump(cats_json, f)


def write_json_to_html(cats_json):
    html = json2html.convert(cats_json)
    transformed_html = re.sub(
        "(http.*?)<", r'<img src="\1" alt=" "><a href="\1">\1</a></img><', html
    )

    with open("cat_data.html", "w") as f:
        f.write(transformed_html)


if __name__ == "__main__":
    print("initializing headers")
    headers = initialize_headers()

    print("grabbing available cats")
    available_cats = get_available_cats(headers)

    print("parsing cat data")
    cats_data = extract_cat_information(available_cats)

    print("grabbing cat descriptions")
    cats = get_cat_descriptions(cats_data, headers)

    print("writing data to file")
    write_json_to_html(cats)

    print("done")
