import flask
import requests
from flask import request
from skyfield.toposlib import wgs84

from src.python import calculation, geocoding, satnogs, tle, appConfig
from src.python.appConfig import app


@app.route(f'{appConfig.apiBaseUrl}/heartbeat', methods=['GET'])
def getResponse():
    return flask.jsonify(requests.get(satnogs.TLE_URL).json())


@app.route(f'{appConfig.apiBaseUrl}/tle', methods=['GET'])
def getPayload():
    return flask.jsonify(tle.loadTLE())


@app.route(f'{appConfig.apiBaseUrl}/geocoding', methods=['POST'])
def getLatLong():
    addressLine = request.get_json().get('address')
    city = request.get_json().get('city')
    postalCode = request.get_json().get('postalCode')
    country = request.get_json().get('country')
    adminDistrict = request.get_json().get('adminDistrict')

    return flask.jsonify(geocoding.getLatLong(addressLine, city, adminDistrict, postalCode, country)[0])


@app.route(f'{appConfig.apiBaseUrl}/available_satellite', methods=['GET'])
def getAvailableSatellite():
    return flask.jsonify(list(tle.loadTLE().keys()))


@app.route(f'{appConfig.apiBaseUrl}/satellite_state', methods=['GET'])
def getSatelliteState():
    name = request.args.get("name", default="AmicalSat", type=str).upper()
    data = tle.loadTLE()

    try:
        satellite_tle = data[name] if name in data.keys() else data[f'0 {name}']
    except KeyError:
        return flask.jsonify(None)

    response = calculation.getSphericalPath(satellite_tle, 1.0, 60.0 / 60.0)
    currLatLng: tuple = response["origin"]
    currLatPath: list = response["latArray"]
    currLngPath: list = response["longArray"]
    return flask.jsonify({"latLng": {"lat": currLatLng[0], "lng": currLatLng[1]},
                          "latPath": list(currLatPath),
                          "lngPath": list(currLngPath)
                          })


@app.route(f'{appConfig.apiBaseUrl}/prediction', methods=['POST'])
def getHorizon():
    selectedSatellite = request.get_json().get('satellite')
    rxLatLng = request.get_json().get('rxLatLng')
    rxLat = rxLatLng['lat']
    rxLong = rxLatLng['lng']
    rxElevation = 0
    predictionDuration = 1 * 24 * 3600

    predictedPass, predictedDict = calculation.findHorizonTime(tle.loadTLE()[selectedSatellite], predictionDuration,
                                                               wgs84.latlon(rxLat, rxLong,
                                                                            elevation_m=rxElevation))

    return predictedPass


if __name__ == '__main__':
    app.run(debug=True)
