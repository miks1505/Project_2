from flask import Flask, jsonify, request, render_template
import requests

app = Flask(__name__)

API_KEY = 'LsAvC0smtQ9KjegqbHHsGlwaGcLwNzRS'
BASE_URL = 'http://dataservice.accuweather.com'

def is_bad_weather(temperature, wind_speed, precipitation_probability):
    if temperature < 0 or temperature > 35:
        return True
    if wind_speed > 50:
        return True
    if type(precipitation_probability) != str:
        if precipitation_probability > 70:
            return True
    return False

def get_coordinates(city):
    try:
        url = f"{BASE_URL}/locations/v1/cities/search"
        params = {"apikey": API_KEY, "q": city, "language": "ru-ru"}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise requests.exceptions.RequestException(response.text)
        data = response.json()
        if not data:
            return None, f"Город {city} не найден в базе данных."
        for location in data:
            if location.get("Country", {}).get("ID") == "RU":
                return (
                    location['Key'],
                    location['GeoPosition']['Latitude'],
                    location['GeoPosition']['Longitude'],
                ), None
        return None, f"Координаты для {city} не найдены."
    except requests.exceptions.RequestException as e:
        return None, f"Ошибка подключения к API: {e}"

def get_weather_data(location_key):
    try:
        url = f"{BASE_URL}/forecasts/v1/daily/1day/{location_key}"
        params = {"apikey": API_KEY, "details": "true", "metric": "true", "language": "ru-ru"}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise requests.exceptions.RequestException(response.text)
        data = response.json()
        if not data:
            return None, "Данные о погоде отсутствуют."
        print(data)
        weather = data["DailyForecasts"][0]
        print(weather)
        def average_temperature(weather):
            return (int(weather['Temperature']['Minimum']['Value']) + int(weather['Temperature']['Minimum']['Value'])) / 2
        return {
            "temperature": average_temperature(weather),
            "humidity": int(weather["Day"]["RelativeHumidity"]["Average"]),
            "wind_speed": int(weather["Day"]['Wind']['Speed']['Value']),
            "precipitation_probability": int(weather["Day"]["PrecipitationProbability"]),
        }, None
    except requests.exceptions.RequestException as e:
        return None, f"Ошибка подключения к API: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check-weather', methods=['POST'])
def check_weather_route():
    start_city = request.form.get('start')
    end_city = request.form.get('end')

    if not start_city or not end_city:
        return render_template('index.html', error="Не указаны начальный или конечный города")

    start_data, error = get_coordinates(start_city)
    if error:
        return render_template('index.html', error=f"{start_city}: {error}")
    start_key, start_lat, start_lon = start_data

    end_data, error = get_coordinates(end_city)
    if error:
        return render_template('index.html', error=f"{end_city}: {error}")
    end_key, end_lat, end_lon = end_data

    start_weather, error = get_weather_data(start_key)
    if error:
        return render_template('index.html', error=f"Ошибка получения погоды для {start_city}: {error}")

    end_weather, error = get_weather_data(end_key)
    if error:
        return render_template('index.html', error=f"Ошибка получения погоды для {end_city}: {error}")

    result = {
        'start': {
            'city': start_city,
            'coordinates': (start_lat, start_lon),
            'weather': start_weather,
            'is_bad_weather': is_bad_weather(
                start_weather['temperature'],
                start_weather['wind_speed'],
                start_weather['precipitation_probability'],
            )
        },
        'end': {
            'city': end_city,
            'coordinates': (end_lat, end_lon),
            'weather': end_weather,
            'is_bad_weather': is_bad_weather(
                end_weather['temperature'],
                end_weather['wind_speed'],
                end_weather['precipitation_probability'],
            )
        }
    }

    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)