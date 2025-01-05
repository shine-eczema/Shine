import requests
my_key = "ebc798e21a3f400b837af86b832b3a67"
# weatherbit API
def weatherbitAPI(lat, lon):
    url = "https://api.weatherbit.io/v2.0/current"
    params = {
        "lat": lat,
        "lon": lon,
        "key": my_key,
        "lang": "en",
        "units": "I",
        "include": "minutely"
    }
    response = requests.get(url, params=params)
    data = response.json()

    uv_index = data["data"][0]["uv"]
    temperature = data["data"][0]["temp"]
    humidity = data["data"][0]["rh"]

    uvtehu = []
    uvtehu.extend((uv_index, temperature, humidity))
    return uvtehu

# weatherbit API again
def pollenAPI(lat, lon):
    url = "https://api.weatherbit.io/v2.0/current/airquality"
    params = {
        "lat": lat,
        "lon": lon,
        "key": my_key
    }
    response = requests.get(url, params=params)
    data = response.json()

    treepollen = data["data"][0]["pollen_level_tree"]
    grasspollen = data["data"][0]["pollen_level_grass"]
    weedpollen = data["data"][0]["pollen_level_weed"]
    mold = data["data"][0]["mold_level"]
    mostpollen = data["data"][0]["predominant_pollen_type"]
    location = data["data"][0]["city_name"]

    facts = []
    facts.extend((treepollen, grasspollen, weedpollen, mold, mostpollen, location))
    return facts
