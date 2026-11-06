import json

def jsonToDict(myDict):
    print("Saving to district.json")
    with open("JSONs/district.json", "w") as f:
        json.dump(myDict, f, indent=4)

    return "Saved Successfully"