import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
import struct
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
import os

POLAR_EARTH_RADIUS = 6356752.3142
STEP_HORIZ = 4
STEP_DEEP = 1
sl2_path = "/Users/test/Documents/численные/new/логи эхолота сонара/ташкуль/Chart 29_07_2016 [0].sl2"

def L(lat1, lon1, lat2, lon2):
    #rad - радиус сферы (Земли)
    rad = 6372795
    #косинусы и синусы широт и разницы долгот
    cl1 = math.cos(lat1)
    cl2 = math.cos(lat2)
    sl1 = math.sin(lat1)
    sl2 = math.sin(lat2)
    delta = lon2 - lon1
    cdelta = math.cos(delta)
    sdelta = math.sin(delta)
    #вычисления длины большого круга
    y = math.sqrt(math.pow(cl2 * sdelta, 2)
                  + math.pow(cl1 * sl2 - sl1 * cl2 * cdelta, 2))
    x = sl1 * sl2 + cl1 * cl2 * cdelta
    ad = math.atan2(y, x)
    dist = ad * rad
    return dist

def conv_lon(lon):
    longitude = lon / POLAR_EARTH_RADIUS # * (180/math.pi)
    return longitude

def conv_lat(lat):
    temp = lat / POLAR_EARTH_RADIUS
    temp = math.exp(temp)
    temp = (2 * math.atan(temp)) - (math.pi / 2)
    latitude = temp # * (180/math.pi)
    return latitude   #координаты в радианах

def write_point(lat,lon,deep,path):
    wpt = ET.SubElement(gpx, "wpt") # добавляем дочерний элемент к gpx
    wpt.set("lat", str(lat)) # устанавливаем аттрибут
    wpt.set("lon", str(lon)) # устанавливаем еще один аттрибут
    name = ET.SubElement(wpt, "name")
    name.text = str(round(deep, 1)) + "m"
    sym = ET.SubElement(wpt, "sym")
    sym.text = "Fishing Hot Spot Facility"
    link = ET.SubElement(wpt, "link")
    path = path.strip(" ")
    link.set("href", path)

def made_graph(deepth, number):
    deepth = [-x for x in deepth]

    plt.figure(figsize=(3.2, 4.8)) #размер картинки 320х480
    plt.axis([0, len(deepth)-1, min(deepth),0]) #автонастройка осей

    plt.fill_between(range(len(deepth)), deepth, y2=min(deepth),
                     facecolor=(0.302, 0.212, 0.196), edgecolor="red")

    ax = plt.gca()
    ax.set_axis_bgcolor((0.573, 0.757, 0.992)) #синий фон

    # Создаем форматер
    formatter = mpl.ticker.NullFormatter()
    # Установка форматера для оси X
    ax.xaxis.set_major_formatter (formatter) #уборка нижней оси
    locator = mpl.ticker.NullLocator()
    ax.xaxis.set_major_locator (locator) #уборка нижних тиков
    plt.savefig("example.png")
    Image.open('example.png').save(str(number) + ".jpg", 'JPEG')
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'example.png')
    os.remove(path)  #убрали png

def get_byte(start, shifting, quantity, forma): #вытащить из бинаря
    file.seek(start + shifting)
    temp = file.read(quantity)
    return struct.unpack(forma, temp)[0]

#-------------MAIN!------------------#
gpx = ET.Element("gpx") # рутовый элемент XML'ки
file = open(sl2_path, mode='rb')
starting = 12

lon1 = conv_lon(int(get_byte(starting, 104, 4, "<I")))
lat1 = conv_lat(int(get_byte(starting, 108, 4, "<I")))
depth1 = float(get_byte(starting, 60, 4, "<f")) * 0.3048

counter = 0
depth = []
full_count = 0
for starting in range(12, os.path.getsize(sl2_path), 2064):
    depth.append(float(get_byte(starting, 60, 4, "<f")) * 0.3048) #глубины для картинки
    full_count += 1
    valid = int(get_byte(starting, 128, 2, ">H"))  #считали битовую маску
    if valid & 0b0001000000000000: #позиция валидна
        lat2 = conv_lat(int(get_byte(starting, 108, 4, "<I")))
        lon2 = conv_lon(int(get_byte(starting, 104, 4, "<I")))
        depth2 = float(get_byte(starting, 60, 4, "<f")) * 0.3048  #перевели в метры
        dlin = L(lat1, lon1, lat2, lon2)
        if dlin > STEP_HORIZ and abs(depth1 - depth2) > STEP_DEEP:
            counter += 1  #счётчик перепадов
            write_point(lat1 * (180/math.pi), lon1 * (180/math.pi), depth1,
                        "Garmin/images/" + str(round(full_count / 2)) + ".jpg")
            write_point(lat2 * (180/math.pi), lon2 * (180/math.pi), depth2,
                        "Garmin/images/" + str(round(full_count / 2)) + ".jpg")
            lat1, lon1, depth1 = lat2, lon2, depth2
            #передаём глубины через одну и делим имя, тк значения повторяются
            made_graph(depth[0::2], round(full_count / 2))
            depth.clear()
        elif dlin > STEP_HORIZ:
            lat1, lon1, depth1 = lat2, lon2, depth2
            depth.clear()

xmlstr = minidom.parseString(ET.tostring(gpx)).toprettyxml(indent="   ")
with open("map.gpx", "w") as f:
    f.write(xmlstr)
print("Усё готово! Обнаружено " + str(counter) + " рыбных мест!")
