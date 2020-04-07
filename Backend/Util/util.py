'This file includes helper functions that are useful for ML model'
import requests, json, datetime
from geopy.geocoders import Nominatim
import json


def get_weather_info(lattitude=None, longitude=None, date=None, time=None):
    '''expected date syntax: yyyy-mm-dd, time syntax: HH:MM:SS'''
    final_time = str(date) + "T" + str(time)
    lat = str(lattitude)
    longi = str(longitude)

    filtered_data = dict()
    query = 'https://api.darksky.net/forecast/b299af3ff2d76cdfd211d92bc24374da/' + lat + ',' + longi + ',' + final_time
    r = requests.get(
        query,
        verify=False)
    data = r.json()
    filtered_data['Temperature(F)'] = data['currently']['temperature']
    filtered_data['Pressure(in)'] = data['currently']['pressure']
    filtered_data['Humidity(%)'] = data['currently']['humidity']
    filtered_data['Wind_Direction'] = wind_deg_to_str2(data['currently']['windBearing'])
    filtered_data['Wind_Speed(mph)'] = data['currently']['windSpeed']
    filtered_data['Visibility(mi)'] = data['currently']['visibility']
    date = datetime.datetime.fromtimestamp(data['currently']['time']).strftime('%H:%M:%S')
    date = date.split(':')
    if int(date[0]) <= 7 or int(date[0]) >= 19:
        filtered_data['Sunrise_Sunset'] = 'Night'
    else:
        filtered_data['Sunrise_Sunset'] = 'Day'
    return filtered_data


def wind_deg_to_str2(deg):
    arr = ['NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']
    return arr[int(abs((deg - 11.25) % 360) / 22.5)]


def get_address_info(lat, longi):
    geolocator = Nominatim(user_agent='DVA-project')
    location = geolocator.reverse(', '.join([str(lat), str(longi)]), timeout=600000)
    result = {}
    if 'address' in location.raw:
        result['County'] = '' if 'county' not in location.raw['address'] else location.raw['address']['county'].split(" ")[0]
        result['Side'] = 'R'
        result['City'] = 'Aaronsburg' if 'city' not in location.raw['address'] else location.raw['address']['city']
        state = '' if 'state' not in location.raw['address'] else location.raw['address']['state'][0:2]
        result['State'] = state.upper()

    return result


def form_query(feature, bbox):
    overpass_query = """
    [out:json][timeout:50000];
    node
    """ + feature + bbox + """; 
    out body;
    """
    return overpass_query


def get_topology_info(latitude, longitude):

    """

    :param latitude:
    :param longitude:
    :return:dict: {"traffic_calming":True ......}
    """
    # use bbox coordinates in query . Currently giving dummy coordinates
    # bbox = "(50.6,7.0,50.8,7.3)"
    bbox = "("+str(latitude-0.2)+","+str(longitude-0.2)+","+str(latitude+0.2)+","+str(longitude+0.2)+")"
    result = {}
    overpass_query = form_query("""["traffic_calming"="yes"]""", bbox)
    result['Traffic_Calming'] = is_present(overpass_query)

    overpass_query = form_query("""["highway"="crossing"]""", bbox)
    result['Crossing'] = is_present(overpass_query)

    overpass_query = form_query("""["highway"="give_way"]""", bbox)
    result['Give_Way'] = is_present(overpass_query)

    overpass_query = form_query("""["public_transport"="station"]""", bbox)
    result['Station'] = is_present(overpass_query)

    overpass_query = form_query("""["railway"="level_crossing"]""", bbox)
    result['Railway'] = is_present(overpass_query)

    overpass_query = form_query("""["crossing"="traffic_signals"]""", bbox)
    result['Traffic_Signal'] = is_present(overpass_query)

    return result


def is_present(overpass_query):
    overpass_url = "http://overpass-api.de/api/interpreter"
    response = requests.get(overpass_url,
                            params={'data': overpass_query})
    try:
        data = response.json()
    except:
        return False
    if data and 'elements' in data and len(data['elements']) > 0:
        return True
    else:
        return False


def merge(dict1, dict2):
    dict2.update(dict1)
    return dict2


def lookup_val_in_json(json_file, key):
    if json_file == "wind_dir_map.json":
        key = key.upper()
    path = "/Users/gurleen_kaur/Documents/georgia/DVA/dva_project2/DVA-Project/Backend/Util/" + json_file
    with open(path) as f:
        loaded_json = json.load(f)
    return loaded_json[key]


def predict_input_format_wrapper(attrs_dict):
    """
        This method parses attributes from dict to a list,
        returned list can be use to predict Severity for an instance
        Argument  : dict of input attributes with same naming as in the dataset
        Return    : list of attributes to be passed to model.predict method
    """
    feature_lst=[attrs_dict['longitude'],
             attrs_dict['latitude'],
             lookup_val_in_json('side_map.json', attrs_dict['Side']),
             lookup_val_in_json('city_map.json', attrs_dict['City']),
             lookup_val_in_json('county_map.json', attrs_dict['County']),
             lookup_val_in_json('state_map.json', attrs_dict['State']),
             attrs_dict['Temperature(F)'],
             attrs_dict['Humidity(%)'],
             attrs_dict['Pressure(in)'], 
             lookup_val_in_json('wind_dir_map.json', attrs_dict['Wind_Direction']),
             attrs_dict['Wind_Speed(mph)'],
             attrs_dict['Visibility(mi)'], 
             lookup_val_in_json('sunrise_sunset_map.json', attrs_dict['Sunrise_Sunset']),
             attrs_dict['Crossing'],
             attrs_dict['Give_Way'],
             attrs_dict['Railway'],
             attrs_dict['Station'],
             attrs_dict['Traffic_Calming'],
             attrs_dict['Traffic_Signal'],
             attrs_dict['Weekday'],
             attrs_dict['Month'],
             attrs_dict['Year']] 
    return feature_lst
