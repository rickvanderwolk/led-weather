import datetime
import time
import random
import requests
from rpi_ws281x import Adafruit_NeoPixel, Color

LED_STRIP_LED_COUNT = 120
LED_STRIP_DATA_PIN = 18
LED_STRIP_FREQ_HZ = 800000
LED_STRIP_DMA = 10
LED_STRIP_DEFAULT_BRIGHTNESS = 255
LED_STRIP_INVERT = False
OPEN_WEATHER_API_KEY = '<your-open-weather-api-key>'
OPEN_WEATHER_API_CITY = '<your-city>'
OPEN_WEATHER_API_BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
TEST_MODE_IS_ON = False
WEATHER_UPDATE_INTERVAL = 300

strip = Adafruit_NeoPixel(LED_STRIP_LED_COUNT, LED_STRIP_DATA_PIN, LED_STRIP_FREQ_HZ, LED_STRIP_DMA, LED_STRIP_INVERT, LED_STRIP_DEFAULT_BRIGHTNESS)
strip.begin()

def clear_strip():
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def fade_led(current_color, target_color, step, total_steps):
    r_step = (target_color[0] - current_color[0]) / total_steps
    g_step = (target_color[1] - current_color[1]) / total_steps
    b_step = (target_color[2] - current_color[2]) / total_steps

    new_color = (
        int(current_color[0] + (r_step * step)),
        int(current_color[1] + (g_step * step)),
        int(current_color[2] + (b_step * step))
    )
    return new_color

def fade_strip(current_colors, target_colors):
    steps_in_range = 500
    for step in range(steps_in_range):
        for i in range(strip.numPixels()):
            new_color = fade_led(current_colors[i], target_colors[i], step, steps_in_range)
            strip.setPixelColor(i, Color(*new_color))
        strip.show()
        time.sleep(0.025)

def get_strip_current_colors():
    return [get_rgb_from_color(strip.getPixelColor(i)) for i in range(strip.numPixels())]

def get_rgb_from_color(color_int):
    red = (color_int >> 16) & 255
    green = (color_int >> 8) & 255
    blue = color_int & 255
    return (red, green, blue)

def get_test_data():
    sunrise = datetime.datetime.strptime('2024-08-30 07:54:04',  '%Y-%m-%d %H:%M:%S')
    sunset = datetime.datetime.strptime('2024-08-30 23:49:39',  '%Y-%m-%d %H:%M:%S')
    weather_condition = 'Sun'
    cloud_percentage = 75
    return sunrise, sunset, weather_condition, cloud_percentage

def get_weather_data():
    url = OPEN_WEATHER_API_BASE_URL + "q=" + OPEN_WEATHER_API_CITY + "&appid=" + OPEN_WEATHER_API_KEY
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        sunrise = datetime.datetime.fromtimestamp(weather_data['sys']['sunrise'])
        sunset = datetime.datetime.fromtimestamp(weather_data['sys']['sunset'])
        weather_condition = weather_data['weather'][0]['main']
        cloud_percentage = weather_data['clouds']['all']
        return sunrise, sunset, weather_condition, cloud_percentage
    else:
        raise RuntimeError(f"Unable to load weather data. Status code: {response.status_code}")

def simulate_error():
    color = Color(255, 0, 0)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()

def simulate_night(cloudiness_percentage):
    sun_color = (255, 255, 0)
    current_colors = get_strip_current_colors()
    target_colors = current_colors.copy()
    leds = list(range(strip.numPixels()))
    random.shuffle(leds)
    number_of_cloudy_leds = int(cloudiness_percentage / 100 * strip.numPixels())

    for i in leds[:number_of_cloudy_leds]:
        target_colors[i] = (0, 0, 0)
    for i in leds[number_of_cloudy_leds:]:
        if random.randint(1, 25) <= 1:
            target_colors[i] = (20, 20, 100)
        elif random.randint(1, 10) <= 1:
            target_colors[i] = (50, 0, 50)
        else:
            blue_shade = random.randint(10, 50)
            target_colors[i] = (0, 0, blue_shade)

    fade_strip(current_colors, target_colors)
    time.sleep(random.randint(30, 60))

def simulate_rain(intensity="medium"):
    if intensity == "hard":
        led_count = 40
        delay = 0.1
    if intensity == "soft":
        led_count = 10
        delay = 0.3
    else:
        led_count = 25
        delay = 0.2

    for _ in range(10):
        for _ in range(led_count):
            i = random.randint(0, strip.numPixels()-1)
            blue_shade = random.randint(100, 255)
            strip.setPixelColor(i, Color(0, 0, blue_shade))
        strip.show()
        time.sleep(delay)
        clear_strip()

def simulate_sunlight(cloudiness_percentage):
    cloud_color = (50, 50, 50)
    sun_color = (255, 255, 0)
    current_colors = get_strip_current_colors()
    target_colors = current_colors.copy()
    leds = list(range(strip.numPixels()))
    random.shuffle(leds)
    number_of_cloudy_leds = int(cloudiness_percentage / 100 * strip.numPixels())

    for i in leds[:number_of_cloudy_leds]:
        target_colors[i] = cloud_color
    for i in leds[number_of_cloudy_leds:]:
        target_colors[i] = sun_color

    fade_strip(current_colors, target_colors)
    time.sleep(random.randint(30, 60))

def simulate_thunderstorm():
    if random.randint(1, 30) == 1:
        for _ in range(random.randint(3, 7)):
            for i in range(strip.numPixels()):
                if random.choice([True, False]):
                    strip.setPixelColor(i, Color(255, 255, 255))
                else:
                    strip.setPixelColor(i, Color(0, 0, 0))
            strip.show()
            time.sleep(random.uniform(0.05, 0.2))
            clear_strip()
            time.sleep(random.uniform(0.1, 0.5))
    else:
        simulate_rain('hard')

last_weather_update = 0
sunrise, sunset, weather_condition, cloud_percentage = None, None, None, None

try:
    while True:
        current_time = time.time()
        if current_time - last_weather_update > WEATHER_UPDATE_INTERVAL:
            if TEST_MODE_IS_ON:
                sunrise, sunset, weather_condition, cloud_percentage = get_test_data()
            else:
                sunrise, sunset, weather_condition, cloud_percentage = get_weather_data()

            print(f"Testmode: {TEST_MODE_IS_ON}, Timestamp: {current_time}, Sunrise: {sunrise}, Sunset: {sunset}, Weather condition: {weather_condition}, Cloud percentage: {cloud_percentage}")
            last_weather_update = current_time

        if weather_condition and sunrise and sunset and cloud_percentage:
            now = datetime.datetime.now()

            is_daytime = sunrise <= now <= sunset
            strip.setBrightness(LED_STRIP_DEFAULT_BRIGHTNESS if is_daytime else round(LED_STRIP_DEFAULT_BRIGHTNESS / 10))

            if weather_condition == 'Drizzle':
                simulate_rain('soft')
            elif weather_condition == 'Rain':
                simulate_rain()
            elif weather_condition == 'Rainbow':
                simulate_rainbow()
            elif weather_condition == 'Thunderstorm':
                simulate_thunderstorm()
            else:
                if is_daytime:
                    simulate_sunlight(cloud_percentage)
                else:
                    # always show some light
                    if cloud_percentage == 100:
                        cloud_percentage = 99
                    simulate_night(cloud_percentage)
        else:
            clear_strip()

except KeyboardInterrupt:
    clear_strip()

except BaseException as e:
    simulate_error()
    print(e)
