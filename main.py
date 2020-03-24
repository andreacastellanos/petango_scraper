import json
import requests
import re
import os
import webbrowser
from json2html import json2html


SHELTER_ID = "994"
FILENAME = "cat_data"


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
    data = {}
    for item in available_cats:
        identifier = "{name} - {id_number}".format(
            name=item["name"], id_number=item["id"]
        )
        data[identifier] = {
            "breed": item["breed"],
            "age": item["age"],
            "url": item["url"],
            "pictures": [],
        }

    return data


def get_cat_descriptions(cats, headers):
    params = {
        "moduleId": "849",
        "clientZip": "null",
    }

    headers.update(
        {"TabId": "261", "ModuleId": "849", "Content-Type": None, "Origin": None,}
    )

    for identifier, data in cats.items():
        print("grabbing cat {identifier}".format(identifier=identifier))

        name, id_number = identifier.split(" - ")
        params["animalId"] = id_number
        headers["Referer"] = data["url"]

        response = requests.get(
            "https://www.petango.com/DesktopModules/Pethealth.Petango/Pethealth.Petango.DnnModules.AnimalDetails/API/Main/GetAnimalDetails",
            headers=headers,
            params=params,
        )
        response_json = response.json()
        cats[identifier]["description"] = response_json["memo"]

        for key, value in response_json.items():
            if "photo" in key.lower():
                if value:
                    cats[identifier]["pictures"].append(value)

    return cats


def get_differences(old_cats, current_cats):
    new_cats = current_cats.copy()

    for current_identifier, current_data in current_cats.items():
        if not old_cats.get(current_identifier):
            new_identifier = "{identifier} - NEW".format(identifier=current_identifier)
            new_cats[new_identifier] = new_cats.pop(current_identifier)
            print("new cat: {new_identifier}".format(new_identifier=new_identifier))

    return new_cats


def open_json_file_to_json():
    filename = "{filename}.json".format(filename=FILENAME)

    if not os.path.isfile(filename) or os.stat(filename).st_size == 0:
        return {}

    with open(filename, "r") as f:
        cats = json.load(f) or {}

    return cats


def write_json_to_json_file(cats_json):
    filename = "{filename}.json".format(filename=FILENAME)

    cats_dumped = json.dumps(cats_json)
    cats_dumped = cats_dumped.replace(" - NEW", "")
    cats_json = json.loads(cats_dumped)

    with open(filename, "w") as f:
        json.dump(cats_json, f)


def write_json_to_html_file(cats_json):
    filename = "{filename}.html".format(filename=FILENAME)

    html = json2html.convert(cats_json)
    transformed_html = re.sub(
        "(http.*?)<", r'<img src="\1" alt=" "><a href="\1">\1</a></img><', html
    )

    with open(filename, "w") as f:
        f.write(transformed_html)


def open_file_in_browser():
    filename = "{filename}.html".format(filename=FILENAME)
    webbrowser.open_new_tab("file://" + os.path.realpath(filename))


if __name__ == "__main__":
    print("initializing headers")
    headers = initialize_headers()

    print("grabbing available cats")
    available_cats = get_available_cats(headers)

    print("parsing cat data")
    data = extract_cat_information(available_cats)

    print("grabbing cat descriptions")
    cats = get_cat_descriptions(data, headers)

    old_cats = open_json_file_to_json()
    if cats == old_cats:
        print("no new cats")
    else:
        print("writing data to file")
        cats = get_differences(old_cats, cats)

    write_json_to_json_file(cats)
    write_json_to_html_file(cats)

    open_file_in_browser()
    print("done")
