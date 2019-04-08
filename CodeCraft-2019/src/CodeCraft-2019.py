import logging
import sys
from altgraph import GraphError
from altgraph.Graph import Graph
from Algorithms import Algorithms
# from Scheduler import *
# logging.basicConfig(level=logging.DEBUG,
#                     filename='../logs/CodeCraft-2019.log',
#                     format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S',
#                     filemode='a')

def main():
    if len(sys.argv) != 6:
        logging.info('please input args: car_path, road_path, cross_path, answerPath')
        exit(1)

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    preset_answer_path = sys.argv[4]
    answer_path = sys.argv[5]

    logging.info("car_path is %s" % (car_path))
    logging.info("road_path is %s" % (road_path))
    logging.info("cross_path is %s" % (cross_path))
    logging.info("preset_answer_path is %s" % (preset_answer_path))
    logging.info("answer_path is %s" % (answer_path))
    # print("answer_path is %s" % (answer_path))

    penaltyFactor = 40
    interval = 20

    car_list, road_list, cross_list, preset_answer_list= readFiles(car_path, road_path, cross_path, preset_answer_path)
    # car_list = sorted(car_list, key=lambda x: x[4]) # first car scheduled first for non-preset cars
    preset = [x for x in car_list if x[6] == 1]
    car_list = replaceDepartTimeForPresetCar(car_list, preset_answer_list)

    # priority cars depart first, then non-priority cars depart
    priority_non_preset = [x for x in car_list if x[5] == 1 and x[6] == 0]
    non_priority_non_preset = [x for x in car_list if x[5] == 0 and x[6] == 0]
    priority_non_preset = sorted(priority_non_preset, key=lambda x: x[4])
    non_priority_non_preset = sorted(non_priority_non_preset, key=lambda x: x[4])
    car_list = priority_non_preset + non_priority_non_preset #
    car_list = chooseDepartTimeForNonPresetCar(car_list, interval)

    with open('non_preset_depart_time.txt', 'w') as f:
        for car in car_list:
            f.writelines(str(car) + '\n')

    # merge non-preset cars and preset cars into car_list
    car_list.extend(preset)
    # sort car_list in ascending depart_time, so that dynamic penalty works
    car_list = sorted(car_list, key=lambda x: x[4])

    with open('all_depart_time.txt', 'w') as f:
        for car in car_list:
            f.writelines(str(car) + '\n')

    graph = Graph()
    graph = initMap(graph, road_list, cross_list)
    graph = changeWeightByPreset(graph, preset_answer_list, penaltyFactor)
    route_dict = findRouteForCar(graph, car_list, preset_answer_list, penaltyFactor)
    # route_list = chooseRouteForCar(graph, car_list)

    carInfo = open(car_path,  'r').read().split('\n')[1:]
    roadInfo = open(road_path, 'r').read().split('\n')[1:]
    crossInfo = open(cross_path, 'r').read().split('\n')[1:]

    answer_info = generateAnswer(route_dict, car_list, interval)
    # preset_answer_info = generatePresetAnswer(preset_answer_path)
    writeFiles(answer_info, answer_path)

    # scheduler = Scheduler(carInfo, roadInfo, crossInfo, answer_info, preset_answer_info)
    # time = scheduler.schedule()
    # print('Current schedule time: %d' %time)

#
# to read input file
# elements are 'int' type:
# road_list = [[5000, 10, 5, 1, 1, 2, 1],
#               ...
#               [5059, 10, 5, 1, 35, 36, 1]]

def readFiles(car_path, road_path, cross_path, preset_answer_path):
    car_list = []
    road_list = []
    cross_list = []
    preset_answer_list = []
    with open(car_path, 'r') as cars_file:
        for car_line in cars_file.readlines():
            if car_line.startswith('#'):
                continue
            car_line = car_line.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            car_line = [int(x) for x in car_line]
            car_list.append(car_line)

    with open(road_path, 'r') as road_file:
        for road_line in road_file.readlines():
            if road_line.startswith('#'):
                continue
            road_line = road_line.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            road_line = [int(x) for x in road_line]
            road_list.append(road_line)

    with open(cross_path, 'r') as cross_file:
        for cross_line in cross_file.readlines():
            if cross_line.startswith('#'):
                continue
            cross_line = cross_line.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            cross_line = [int(x) for x in cross_line]
            cross_list.append(cross_line)
    with open(preset_answer_path, 'r') as preset_answer_file:
        for preset_answer_line in preset_answer_file.readlines():
            if preset_answer_line.startswith('#'):
                continue
            preset_answer_line = preset_answer_line.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            preset_answer_line = [int(x) for x in preset_answer_line]
            preset_answer_list.append(preset_answer_line)
    return car_list, road_list, cross_list, preset_answer_list


# process
# init map using Graph class in altgraph module
# can not guarantee the graph is connected,
# which means not every node can be reached from every other node
def initMap(graph, road_list, cross_list):
    # init graph nodes
    for cross in cross_list:
        graph.add_node(cross[0], (cross[1], cross[2], cross[3], cross[4]))
    for road in road_list:
        # default edge data = 1, which is used for edge weight/distance
        # modify GraphAlgo.py to GraphAlgorithms, default weight = 1, so edge data could keep info like 'id' and 'length'
        graph.add_edge(int(road[4]), int(road[5]), (int(road[0]), int(road[1]), int(road[2]), int(road[3])))
        # duplex road, add reverse edge
        if road[-1] == 1:
            graph.add_edge(road[5], road[4], (int(road[0]), int(road[1]), int(road[2]), int(road[3])))
    return graph

def chooseDepartTimeForNonPresetCar(car_list, interval):
    non_preset_index = 0
    for i in range(car_list.__len__()):
        if car_list[i][-1] == 0:
            depart_time = car_list[i][4] # depart_time = planTime
            # print("No.%d car, No.%d non-preset car, depart_time=%d" %(i, non_preset_index, depart_time))
            # preset route may be overload among some roads, when preset cars finish trip, speed up departure
            # if (non_preset_index // interval) < 850:
            #     depart_time += non_preset_index // interval
            # else:
            #     depart_time += 850 + (non_preset_index-850*interval) // 76

            if (non_preset_index // interval) < 850:
                if non_preset_index // interval >= depart_time:
                    depart_time = non_preset_index // interval
                # depart_time = planTime
                else:
                    pass
                # seperate the depart_time distribution with preset cars depart_time
                # in 2-map-training-1&2, preset cars depart at 1 or 6
                if depart_time % 5 == 1:
                    depart_time += 2

            else:
                depart_time = 850 + (non_preset_index-850*interval) // 60
            # depart_time += non_preset_index // interval
            # print("depart_time=%d" %(depart_time))
            car_list[i][4] = depart_time
            non_preset_index += 1
    print(car_list[i])
    return car_list

# 'planTime' of the preset car in car.txt is replaced by the preset 'time' in presetAnswer.txt
def replaceDepartTimeForPresetCar(car_list, preset_answer_list):
    # {car_id: time}
    preset_time_dict = {}
    for preset_answer in preset_answer_list:
        preset_time_dict[preset_answer[0]] = preset_answer[1]
    for i in range(car_list.__len__()):
        if car_list[i][-1] == 1:
            car_list[i][4] = preset_time_dict[car_list[i][0]]
    return car_list

# search ALL route of graph,
# def searchRoute(graph):
#     # FOR DEBUG
#     # road_count = {}
#     # for edge_id in graph.edge_list():
#     #     road_id = graph.edge_data(edge_id)[0]
#     #     road_count.setdefault(road_id, 0)
#     algo = Algorithms()
#     all_route_list = {}
#     node_list = graph.node_list()
#     for start in node_list:
#         for end in node_list:
#             if start == end:
#                 continue
#             # K SHORTEST PATH && SIMPLE PATH ARE SLOWER
#             # path1 = algo.ksp_yen(graph, start, end, 2)[0]['path']
#             # path2 = algo.ksp_yen(graph, start, end, 2)[1]['path']
#             # path3 = algo.simple_path(graph, start, end)
#             # path2 = algo.simple_path(graph, start, end)
#             # rand = random.random()
#             # if rand > 0.1:
#             #     path = path1
#             # else:
#             #     path = path1
#             # elif rand > 0.1:
#             #     path = path2
#             # else:
#             #     path = path3
#             path = algo.shortest_path(graph, start, end)
#             if not path:
#                 continue
#             path_len = len(path)
#             if path_len > 1:
#                 route = []
#                 for i in range(path_len-1):
#                     edge_id = graph.edge_by_node(path[i], path[i+1])
#                     road_id = graph.edge_data(edge_id)[0]
#                     new_length = graph.edge_data(edge_id)[1] + 35
#                     new_edge_data = (road_id, new_length, graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
#                     graph.update_edge_data(edge_id, new_edge_data)
#                     # road_count[road_id] +=1
#                     route.append(road_id)
#                 all_route_list[(start, end)] = route
#     # FOR DEBUG
#     # print(road_count)
#     return all_route_list

# if car number > node^2 (approximataly), calling chooseRouteForCar func is faster than findRouteForCar
# def chooseRouteForCar(graph, car_list):
#     route_list = []
#     all_route_list = searchRoute(graph)
#     for car in car_list:
#         s = (car[1], car[2])
#         route_list.append(all_route_list[s])
#     return route_list


# This func uses dynamic penalty!
# NOTE:
#   if car number < node^2 (approximataly), calling findRouteForCar func is faster than chooseRouteForCar
#   BUT, this is real penalty, which means this func could return more 'average' results
def findRouteForCar(graph, car_list, preset_answer_list, penaltyFactor):
    # FOR DEBUG
    # road_count = {}
    # for edge_id in graph.edge_list():
    #     road_id = graph.edge_data(edge_id)[0]
    #     road_count.setdefault(road_id, 0)

    # {car_id: [5001, 5002, ...]}
    preset_route_dict = {}
    for preset_answer in preset_answer_list:
        preset_route_dict[preset_answer[0]] = preset_answer[2:]

    # {road_id: edge_id}
    edge_data_dict = {}
    for edge in graph.edge_list():
        road_id = graph.edge_data(edge)[0]
        edge_data_dict[road_id] = edge

    algo = Algorithms()
    route_dict = {}
    for car in car_list:

        # K SHORTEST PATH && SIMPLE PATH ARE SLOWER
        # path1 = algo.ksp_yen(graph, car[1], car[2], 2, car[-2])[0]['path']
        # path2 = algo.ksp_yen(graph, car[1], car[2], 2, car[-2])[1]['path']
        # path2 = algo.simple_path(graph, car[1], car[2])
        # if random.random()>0.01:
        #     path = path1
        # else:
        #     path = path2

        # non preset car
        if car[-1] == 0:
            path = algo.shortest_path(graph, car[1], car[2], car[3])
            path_len = len(path)
            if path_len > 1:
                route = []
                for i in range(path_len-1):
                    edge_id = graph.edge_by_node(path[i], path[i+1])
                    road_id = graph.edge_data(edge_id)[0]
                    new_length = graph.edge_data(edge_id)[1] + penaltyFactor # PENALTY
                    new_edge_data = (road_id, new_length, graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                    graph.update_edge_data(edge_id, new_edge_data)
                    # FOR DEBUG
                    # road_count[road_id] += 1
                    route.append(road_id)
            route_dict[car[0]] = route
        # preset car
        else:
            preset_route = preset_route_dict[car[0]]
            for road_id in preset_route:
                edge_id = edge_data_dict[road_id]
                new_length = graph.edge_data(edge_id)[1] + penaltyFactor*2  # PENALTY
                new_edge_data = (road_id, new_length, graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                graph.update_edge_data(edge_id, new_edge_data)
    # FOR DEBUG
    # print(road_count)
    return route_dict

# change edge weight according to preset answer
# but this is not dynamic penalty
# DEPRECATED !!!
def changeWeightByPreset(graph, preset_answer_list, penaltyFactor):
    # {road_id: edge_id}
    edge_data_dict = {}
    for edge in graph.edge_list():
        road_id = graph.edge_data(edge)[0]
        edge_data_dict[road_id] = edge
    for preset_answer in preset_answer_list:
        route = preset_answer[2:]
        for road_id in route:
            edge_id = edge_data_dict[road_id]
            new_length = graph.edge_data(edge_id)[1] + penaltyFactor  # PENALTY
            new_edge_data = (road_id, new_length, graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
            graph.update_edge_data(edge_id, new_edge_data)
    return graph

# generate answerInfo
def generateAnswer(route_dict, car_list, interval):
    answer_info = []
    # i = 0
    # for i in range(len(car_list)):
    for car in car_list:
        if car[-1] == 1:
            # i += 1
            continue
        route = route_dict[car[0]]
        route = str(route).strip('[').strip(']')
        car_id = car[0]
        plan_time = car[4]
        # speed = car[-2]
        depart_time = plan_time
        # if speed == 2:
        #     car_depart_time = plan_time
        # elif speed == 4:
        #     car_depart_time = plan_time
        # elif speed == 6:
        #     car_depart_time = plan_time
        # elif speed == 8:
        #     car_depart_time = plan_time
        # car_depart_time += i // interval
        # i += 1
        answer_info.append('(' + str(car_id) + ', ' + str(depart_time) + ', ' + str(route) + ')')
    return answer_info


def generatePresetAnswer(preset_answer_path):
    preset_answer_info = []
    with open(preset_answer_path, 'r') as preset_answer_file:
        for preset_answer in preset_answer_file.readlines():
            if preset_answer.startswith('#'):
                continue
            preset_answer = preset_answer.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            preset_answer = [int(x) for x in preset_answer]
            preset_answer_info.append(preset_answer)
    return preset_answer_info

# to write output file
def writeFiles(answerInfo, answer_path):
    with open(answer_path, 'w') as answer_file:
        for ans in answerInfo:
            answer_file.write(ans + '\n')

if __name__ == "__main__":
    main()