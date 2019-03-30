import random
import numpy
import collections

class CROSS(object):
    def __init__(self, id):
        self.id = id
        self.north = None
        self.north_road = -1
        self.east = None
        self.east_road = -1
        self.south = None
        self.south_road = -1
        self.west = None
        self.west_road = -1

    def __str__(self):
        return '<Cross id: %s, north_id: %s, east_id: %s, south_id: %s, west_id: %s, north_road: %s, east_road: %s, south_road: %s, west_road: %s>\n' \
               %(self.id, self.north, self.east, self.south, self.west, self.north_road, self.east_road, self.south_road, self.west_road)
    def __repr__(self):
        return '<Cross id: %s, north_id: %s, east_id: %s, south_id: %s, west_id: %s, north_road: %s, east_road: %s, south_road: %s, west_road: %s>\n' \
               %(self.id, self.north, self.east, self.south, self.west, self.north_road, self.east_road, self.south_road, self.west_road)


class ROAD(object):
    def __init__(self, id, from_, to):
        self.id = id
        self.length = 20 + int(random.random()*20)
        self.speed = 10 + int(random.random()*10)
        self.channel = int(random.random()*5)+1
        self.from_ = from_
        self.to = to
        self.isDuplex = 1 if random.random()>0.05 else 0
    def __repr__(self):
        return '<Road id: %s, from_: %s, to: %s, length: %s, speed: %s, channel: %s, isDuplex: %s>\n' \
               %(self.id, self.from_, self.to, self.length, self.speed, self.channel, self.isDuplex)
cross_number = 144
sqrt = int(numpy.sqrt(cross_number))

cross_object_dict = collections.OrderedDict() # dictionary remains sorted based on insertion sequence
cross_id_list = [i+1 for i in range(cross_number)]

for cross_id in cross_id_list:
    cross = CROSS(cross_id)
    cross_object_dict[cross_id] = cross

for cross_id in cross_id_list:
    if not (cross_id) % sqrt == 0:
        # adjacent edge roads must be connected, inner roads are likely to be connected
        if 0 < cross_id <= sqrt or cross_number-sqrt < cross_id <= cross_number \
                or random.random() > 0.1:
            cross_object_dict[cross_id].north = cross_id + 1
            cross_object_dict[cross_id + 1].south = cross_id
    if not cross_number-sqrt < (cross_id) <= cross_number:
        # adjacent edge roads must be connected, inner roads are likely to be connected
        if cross_id % sqrt == 0 or cross_id % sqrt == 1 \
                or random.random() > 0.1:
            cross_object_dict[cross_id].east = cross_id + sqrt
            cross_object_dict[cross_id+sqrt].west = cross_id


road_object_dict = collections.OrderedDict() # dictionary remains sorted based on insertion sequence
road_index = 5000 # because u don't know how many roads are in the map
for cross_id in cross_id_list:
    cross = cross_object_dict[cross_id]
    if cross.north is not None:
        road = ROAD(road_index, cross.id, cross.north)
        cross.north_road = road.id
        north_cross = cross_object_dict[cross_id + 1]
        north_cross.south_road = road.id
        road_object_dict[road_index] = road
        road_index +=1
    if cross.east is not None:
        road = ROAD(road_index, cross.id, cross.east)
        cross.east_road = road.id
        east_cross = cross_object_dict[cross_id + sqrt]
        east_cross.west_road = road.id
        road_object_dict[road_index] = road
        road_index +=1


print(cross_object_dict)
print(road_object_dict)


cross_path = '../DIY/cross.txt'
road_path = '../DIY/road.txt'
car_path = '../DIY/car.txt'

with open(cross_path, 'w') as cross_file:
    cross_file.write('# (id,roadId,roadId,roadId,roadId)\n')
    for cross_id, cross_object in cross_object_dict.items():
        if cross_id == cross_number:
            cross_file.write('(' + str(cross_id) + ', ' + str(cross_object.north_road) + ', ' +
                         str(cross_object.east_road) + ', ' + str(cross_object.south_road) + ', ' +
                         str(cross_object.west_road) + ')')
        else:
            cross_file.write('(' + str(cross_id) + ', ' + str(cross_object.north_road) + ', ' +
                         str(cross_object.east_road) + ', ' + str(cross_object.south_road) + ', ' +
                         str(cross_object.west_road) + ')\n')
with open(road_path, 'w') as road_file:
    road_file.write('#(id,length,speed,channel,from,to,isDuplex)\n')
    for road_id, road_object in road_object_dict.items():
        if road_id == road_index - 1:
            road_file.write('(' + str(road_id) + ', ' + str(road_object.length) + ', ' +
                        str(road_object.speed) + ', ' + str(road_object.channel) + ', ' +
                        str(road_object.from_) + ', ' + str(road_object.to) + ', ' +
                        str(road_object.isDuplex) + ')')
        else:
            road_file.write('(' + str(road_id) + ', ' + str(road_object.length) + ', ' +
                        str(road_object.speed) + ', ' + str(road_object.channel) + ', ' +
                        str(road_object.from_) + ', ' + str(road_object.to) + ', ' +
                        str(road_object.isDuplex) + ')\n')
with open(car_path, 'w') as car_file:
    car_file.write('#(id,from,to,speed,planTime)\n')
    for car_id in range(10000, 91920):
        from_ = int(random.random() * 100) + 1
        to = int(random.random() * 100) + 1
        while to == from_:
            to = int(random.random() * 100) + 1
        speed = 2*(int(random.random() * 3) + 2)
        planTime = int(random.random() * 100) + 1
        if car_id == 91919:
            car_file.write('(' + str(car_id) + ', ' + str(from_) + ', ' +
                        str(to) + ', ' + str(speed) + ', ' +
                        str(planTime) + ')')
        else:
            car_file.write('(' + str(car_id) + ', ' + str(from_) + ', ' +
                        str(to) + ', ' + str(speed) + ', ' +
                        str(planTime) + ')\n')