import random
import numpy

class CROSS(object):
    def __init__(self, id):
        self.id = id
        self.north = None
        self.north_road = None
        self.east = None
        self.east_road = None
        self.south = None
        self.south_road = None
        self.west = None
        self.west_road = None

    def __str__(self):
        return '<Cross id: %s, north_road: %s, east_road: %s, south_road: %s, west_road: %s>\n' \
               %(self.id, self.north_road, self.east_road, self.south_road, self.west_road)
    def __repr__(self):
        return '<Cross id: %s, north_road: %s, east_road: %s, south_road: %s, west_road: %s>\n' \
               % (self.id, self.north_road, self.east_road, self.south_road, self.west_road)


class ROAD(object):
    def __init__(self, id, from_, to):
        self.id = id
        self.length = 20 + int(random.random()*20)
        self.speed = 10 + int(random.random()*10)
        self.channel = int(random.random()*5)+1
        self.from_ = from_
        self.to = to
        self.isDuplex = 1 if random.random()>0.01 else 0
    def __repr__(self):
        return '<Road id: %s, from_: %s, to: %s, length: %s, speed: %s, channel: %s, isDuplex: %s>\n' \
               %(self.id, self.from_, self.to, self.length, self.speed, self.channel, self.isDuplex)
cross_number = 100
sqrt = int(numpy.sqrt(cross_number))
cross_object_dict = {}

# cross id generator
cross_id_list = [i+1 for i in range(cross_number)]

for cross_id in cross_id_list:
    cross = CROSS(cross_id)
    cross_object_dict[cross_id] = cross

for cross_id in cross_id_list:
    if not (cross_id) % sqrt == 0:
        if random.random() > 0.1:
            cross_object_dict[cross_id].north = cross_id + 1
            cross_object_dict[cross_id + 1].south = cross_id
    if not cross_number-sqrt < (cross_id) <= cross_number:
        if random.random() > 0.1:
            cross_object_dict[cross_id].east = cross_id + sqrt
            cross_object_dict[cross_id+sqrt].west = cross_id

    # if not (i+1) % sqrt == 1:
    #     cross_object_list[i].south = cross_object_list[i - 1].id
    # if not 0 < (i+1) <= sqrt:
    #     cross_object_list[i].west = cross_object_list[i - sqrt].id

road_object_list = []
road_index = 1
for cross_id in cross_id_list:
    cross = cross_object_dict[cross_id]
    if cross.north is not None:
        road = ROAD(road_index, cross.id, cross.north)
        road_index +=1
        cross.north_road = road.id
        north_cross = cross_object_dict[cross_id + 1]
        north_cross.south_road = road.id
        road_object_list.append(road)
    if cross.east is not None:
        road = ROAD(road_index, cross.id, cross.east)
        road_index +=1
        cross.east_road = road.id
        east_cross = cross_object_dict[cross_id + sqrt]
        east_cross.west_road = road.id
        road_object_list.append(road)

print(cross_object_dict)
print(road_object_list)


# cross_path = 'MapGenerator/cross.txt'
#
# with open(cross_path, 'w') as cross_file:
#
#         if cross_id == 1 or 8 or 57 or 64:
#             cross.north =
