import requests

api_key = "NZGT32-V7K4RJ-ZVKGQE-5HV3"
#man hat nur 1k anfragen/stunde

def getAPI_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Löst eine Exception bei HTTP-Fehlern aus
        data = response.json()
        return data
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP-Fehler: {http_err}")
    except Exception as err:
        print(f"Anderer Fehler: {err}")



def position():
    seconds = 1 #Hier können wir die anzahl an positionen die wir haben wollen eingeben (ich glaube 2 heißt standort für jetzt und in 1s)
    url = f"https://api.n2yo.com/rest/v1/satellite/positions/{id}/{lat}/{lng}/{alt}/{seconds}/&apiKey={api_key}"
    data = getAPI_data(url)             #ganzes dict. brauchen ja nicht alles
    az = data["positions"][0]["azimuth"]
    ev = data["positions"][0]["elevation"]
    return az, ev


def scanner():          #diese beiden zeilen könnte man auch noch unten bzw in der web dingens einbinden
    category_id = 3     #das hier müsste wetter satellit sein                                       
    search_radius = 70  #wieviel vom himmel gescannt wird (90 wäre waagrecht -> alles was möglich wäre) #nein, 90 ist alles sichtbare
    url = f"https://api.n2yo.com/rest/v1/satellite/above/{lat}/{lng}/{alt}/{search_radius}/{category_id}/&apiKey={api_key}"
    data = getAPI_data(url)
    anzahl = data["info"]["satcount"]
    sateliten = data["above"]   #hier sind alle sateliten drin mit allem. kann ich aber auch noch anders machen. ist ein array!
    return anzahl, sateliten




#GPS data:
lat = 54.321358
lng = 10.134532
alt = 0

#Satelit id:
id = 25544


#das sind die beiden funktionen. bel. erweiterbar mit coolen sachen!

#print(position())
#print(scanner())



#für weiteres infos falls wir brauchen ist das hier crazy geil dokumentiert: https://www.n2yo.com/api/#positions