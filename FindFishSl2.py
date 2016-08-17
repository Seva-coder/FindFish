import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
import struct
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
import os

POLAR_EARTH_RADIUS = 6356752.3142
STEP_HORIZ = 3
STEP_DEEP = 1
sl2_path = "/Users/test/Documents/численные/new/логи эхолота сонара/ташкуль/Chart 30_07_2016 [0].sl2"

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

#---------------MAIN!------------------#
gpx = ET.Element("gpx") # рутовый элемент XML'ки
file = open(sl2_path, mode='rb')
depth = []  #для передачи графопостроителю
step_coord = []  #пары координат с нужным рассстоянием
delta_depth = []  #список с перепадами, синхр с координатми
na_svale = False
start, stop, count1, count2, numb = 0, 0, 0, 0, 0
size = os.path.getsize(sl2_path)
for starting in range(12, size, 2064):
    depth.append(float(get_byte(starting, 60, 4, "<f")) * 0.3048)
    count1 += 1  #инкременируем номер первой точки
    valid = int(get_byte(starting, 128, 2, ">H"))  #считали битовую маску
    if not valid & 0b0001000000000000:  #позиция вруг не валидна
        continue
    for y in range(starting, size, 2064):
        count2 += 1  #смещение от первого номера (основного)
        valid = int(get_byte(y, 128, 2, ">H"))
        if not valid & 0b0001000000000000:
            continue
        lat1 = conv_lat(int(get_byte(starting, 108, 4, "<I")))
        lon1 = conv_lon(int(get_byte(starting, 104, 4, "<I")))
        lat2 = conv_lat(int(get_byte(y, 108, 4, "<I")))
        lon2 = conv_lon(int(get_byte(y, 104, 4, "<I")))
        dlin = L(lat1, lon1, lat2, lon2)
        if dlin > STEP_HORIZ:
            depth1 = float(get_byte(starting, 60, 4, "<f")) * 0.3048
            depth2 = float(get_byte(y, 60, 4, "<f")) * 0.3048
            step_coord.append(list((lat1, lon1, count1 - 1, lat2, lon2, count2 - 1)))
            delta_depth.append(abs(depth1 - depth2))
            break
    count2 = 0
print("теперь ищем")
for position in range(len(delta_depth)):
    if delta_depth[position] > STEP_DEEP:
        if not na_svale:
            start = position
            na_svale = True
    else:
        if na_svale:  #свал закончился
            stop = position
            maxx = max(delta_depth[start:stop])
            yama_index = delta_depth.index(maxx, start, stop)
            lat1 = step_coord[yama_index][0]
            lon1 = step_coord[yama_index][1]
            count1 = step_coord[yama_index][2]
            lat2 = step_coord[yama_index][3]
            lon2 = step_coord[yama_index][4]
            count2 = step_coord[yama_index][5]
            depth1 = depth[count1]
            depth2 = depth[count1 + count2]
            made_graph(depth[count1:count1 + count2:2], round(count1/2))
            write_point(lat1 * (180/math.pi), lon1 * (180/math.pi), depth1, "Garmin/images/" + str(round(count1/2)) + ".jpg")
            write_point(lat2 * (180/math.pi), lon2 * (180/math.pi), depth2, "Garmin/images/" + str(round((count1 + count2)/2)) + ".jpg")
            numb += 1
            na_svale = False

xmlstr = minidom.parseString(ET.tostring(gpx)).toprettyxml(indent="   ")
with open("map.gpx", "w") as f:
    f.write(xmlstr)
print("Усё готово! Обнаружено " + str(numb) + " рыбных мест!")
