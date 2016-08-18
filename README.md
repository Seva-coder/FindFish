# FindFish
Резкие изменения дна водоёма представляют интерес для рыбаков, поэтому написал этот скрипт. Используются логи эхолота (sl2, lowrance).
Идея состоит в том, что скрипт проходит по точкам трека "окном" с заданным шагом (в метрах), при этом вычисляя разности глубин. Если перепад превышает заданный, и при этом определениы координаты и глубина, то координаты начала/конца заносятся в GPX файл и строится картинка "свала". Потом, загрузив их на навик, можно на месте представить рельеф в нужной точке (у меня garmin, соответственно формирование GPX подстраивал под него). Ссылка на картинку добавляется в GPX.
