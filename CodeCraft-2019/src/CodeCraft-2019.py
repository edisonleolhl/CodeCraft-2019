import logging
import sys
from altgraph import GraphError
from altgraph.Graph import Graph
from collections import deque
from collections import defaultdict
from Algorithms import Algorithms
from Scheduler import *

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

    penaltyFactor = 80
    departure_rate = 38
    acc_departure_rate = 40
    queue_length = 100

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
    car_list = chooseDepartTimeForNonPresetCar(car_list, departure_rate, acc_departure_rate)

    # with open('non_preset_depart_time.txt', 'w') as f:
    #     for car in car_list:
    #         f.writelines(str(car) + '\n')

    # merge non-preset cars and preset cars into car_list
    car_list.extend(preset)
    # sort car_list in ascending depart_time, so that dynamic penalty works
    car_list = sorted(car_list, key=lambda x: x[4])

    # with open('all_depart_time.txt', 'w') as f:
    #     for car in car_list:
    #         f.writelines(str(car) + '\n')

    graph = Graph()
    graph = initMap(graph, road_list, cross_list)
    route_dict = findRouteForCar(graph, car_list, cross_list, preset_answer_list, penaltyFactor, queue_length)

    answer_info = generateAnswer(route_dict, car_list)
    writeFiles(answer_info, answer_path)


    # ATTENTION: comments code below before submit to online judgement
    carInfo = open(car_path,  'r').read().split('\n')[1:]
    roadInfo = open(road_path, 'r').read().split('\n')[1:]
    crossInfo = open(cross_path, 'r').read().split('\n')[1:]
    preset_answer_info = generatePresetAnswer(preset_answer_path)
    scheduler = Scheduler(carInfo, roadInfo, crossInfo, answer_info, preset_answer_info)
    time = scheduler.schedule()
    print('Current schedule time: %d' %time)

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

def chooseDepartTimeForNonPresetCar(car_list, departure_rate, acc_departure_rate):
    non_preset_index = 0

    interval = 5 # preset car departure interval, for 2-map-training-1&2, interval = 5
    max_token = departure_rate // (interval - 1)
    previous_depart_time = None
    for i in range(car_list.__len__()):
        if car_list[i][-1] == 0:
            depart_time = car_list[i][4] # depart_time = planTime
            # print("No.%d car, No.%d non-preset car, depart_time=%d" %(i, non_preset_index, depart_time))
            # preset route may be overload among some roads, when preset cars finish trip, speed up departure

            # if (non_preset_index // departure_rate) < 850:
            #     depart_time += non_preset_index // departure_rate
            # else:
            #     depart_time += 850 + (non_preset_index-850*departure_rate) // 76

            if (non_preset_index // departure_rate) < 850:
                if non_preset_index // departure_rate >= depart_time:
                    depart_time = non_preset_index // departure_rate
                # depart_time = planTime
                else:
                    pass
                # seperate the depart_time distribution with preset cars depart_time
                # in 2-map-training-1&2, preset cars depart at 1 or 6
                if depart_time % interval == 1:
                    if depart_time != previous_depart_time:
                        previous_depart_time = depart_time
                        slot_index = 0
                        average_flag = False # token has been put into all slots averagely
                        depart_time += slot_index + 1
                        slot = [0 for x in range(interval - 1)]
                        slot[slot_index] += 1
                    elif not average_flag:
                        depart_time += slot_index + 1
                        slot[slot_index] += 1
                        if slot[slot_index] == max_token:
                            slot_index += 1
                        if slot_index == slot.__len__():
                            average_flag = True
                    else:
                        depart_time += interval//2

            else:
                depart_time = 850 + (non_preset_index-850*departure_rate) // acc_departure_rate
            # depart_time += non_preset_index // departure_rate
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


# This func uses dynamic penalty, using Auto Regressive model.
#
# Return: non-preset car's route
def findRouteForCar(graph, car_list, cross_list, preset_answer_list, penaltyFactor, queue_length):
    # FOR DEBUG
    # road_count = {}
    # for edge_id in graph.edge_list():
    #     road_id = graph.edge_data(edge_id)[0]
    #     road_count.setdefault(road_id, 0)

    # {car_id: [5001, 5002, ...]}
    preset_route_dict = {}
    for preset_answer in preset_answer_list:
        preset_route_dict[preset_answer[0]] = preset_answer[2:]

    # {road_id: edge_id} is wrong, because edge_id is unique, road_id is not unique (duplex road)
    # key in dictionary is unique, so set {edge_id: road:id}
    edge2road_dict = {}
    for edge_id in graph.edge_list():
        road_id = graph.edge_data(edge_id)[0]
        edge2road_dict[edge_id] = road_id

    # find key(s) by value in dictionary
    def dicReverseLookup(dic, value):
        keys = []
        for k, v in dic.items():
            if v == value:
                keys.append(k)
        return keys

    def findCrossByTwoRoad(cross_list, road_id_1, road_id_2):
        for cross in cross_list:
            if road_id_1 in cross and road_id_2 in cross:
                return cross[0]
        return None

    # 4.12 update: Auto Regressive model !!!
    # Penalty becomes failure when the car get the destination, so 'release' the 'penalty' along the road!
    # ar_deque keeps all the penalty information, its length indicating continuous timeslice remains constant
    # ar_deque when append to the last, delete the first
    # ar_deque = {defaultdict(<class 'int'>, {edge_id: penalty}), defaultdict(<class 'int'>, {edge_id: penalty}), ...}
    ar_deque = deque([defaultdict(int) for x in range(queue_length)])
    previous_depart_time = None

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
        ar_flag = False
        depart_time = car[4]
        if depart_time != previous_depart_time:
            # new timeslice
            ar_flag = True # start auto regressive
            present_penalty = defaultdict(int) # defaultdict(<class 'int'>, {edge_id: penalty})

            # 'Release' penalty of the timeslice 'queue_length' ago, subtract penalty value
            release_penalty = ar_deque.popleft() # release_penalty = {edge_id: penalty, ...}
            for edge_id, p_value in release_penalty.items():
                new_length = graph.edge_data(edge_id)[1] - p_value
                new_edge_data = (graph.edge_data(edge_id)[0], new_length,
                                 graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                graph.update_edge_data(edge_id, new_edge_data)

            # average factor 0.2 0.4 0.6 0.8 1.0
            # init all edges
            # for edge_id in graph.edge_list():
            #     new_edge_data = (graph.edge_data(edge_id)[0], 0,
            #                      graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
            #     graph.update_edge_data(edge_id, new_edge_data)
            # # previous states have less effect on present state
            # for i, temp_penalty in enumerate(ar_deque):
            #     for edge_id, p_value in temp_penalty.items():
            #         new_length = graph.edge_data(edge_id)[1]
            #         # eg: q=200, divided into 5 groups, each multiplied by 0.2, 0.4, 0.6, 0.8, 1.0
            #         new_length += p_value * 0.2 * (i//(queue_length//5)+1)
            #         new_edge_data = (graph.edge_data(edge_id)[0], new_length,
            #                          graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
            #         graph.update_edge_data(edge_id, new_edge_data)

            if depart_time % 200 == 0:
                print('Present depart_time=%s, release depart_time=%s penalty '
                      %(depart_time, int(depart_time)-queue_length))

        else:
            # additive
            present_penalty = ar_deque[-1] # present_penalty = {edge_id: penalty(already increment length), ...}

        # non preset car
        if car[-1] == 0:
            path = algo.shortest_path(graph, car[1], car[2], car[3]) # path = [node1(cross1_id), node2, ...]
            path_len = len(path)
            if path_len > 1:
                route = [] # route = [road_id, road_id, ...]
                for i in range(path_len-1):
                    edge_id = graph.edge_by_node(path[i], path[i+1])
                    road_id = graph.edge_data(edge_id)[0]
                    new_length = graph.edge_data(edge_id)[1] + penaltyFactor # PENALTY
                    present_penalty[edge_id] += penaltyFactor # record in present_penalty
                    new_edge_data = (road_id, new_length,
                                     graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                    graph.update_edge_data(edge_id, new_edge_data)

                    # 4.11 update: punish other road of passing cross along the route
                    # eg: four edge(road): 5000, 5001, 5002, 5003 going to the cross(node):100
                    # edge_id (or road_id) = 5000, next edge_id = 5002,
                    # Therefore, other road = 5001, 5003, PUNISH these two edges
                    # Tips: doesn't punsh the destination cross's other road
                    # (considering get to the destination refering to go_straight which has higher priority
                    inc_edge_list = graph.inc_edges(path[i+1])
                    inc_edge_list.remove(edge_id)
                    if i != (path_len-2):
                        oppo_inc_edge_id = graph.edge_by_node(path[i+2], path[i+1])
                        if oppo_inc_edge_id is not None:
                            inc_edge_list.remove(oppo_inc_edge_id)
                    # at this time, inc_edge_list = [5001, 5003]
                    for edge_id in inc_edge_list:
                        new_length = graph.edge_data(edge_id)[1] + penaltyFactor//2
                        present_penalty[edge_id] += penaltyFactor//2  # record in present_penalty
                        new_edge_data = (graph.edge_data(edge_id)[0], new_length,
                                         graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                        graph.update_edge_data(edge_id, new_edge_data)

                    # FOR DEBUG
                    # road_count[road_id] += 1
                    route.append(road_id)
            route_dict[car[0]] = route
        # preset car
        else:
            preset_route = preset_route_dict[car[0]] # preset_route = [road_id, road_id, ...]
            # don't punish only the route with only one road
            if preset_route.__len__() == 1:
                continue
            # preset_route' length must >= 2, so that codes below won't throw exceptions
            for i, road_id in enumerate(preset_route):
                edge_id_list = dicReverseLookup(edge2road_dict, road_id) # edge_id_list may including forward and backward edges
                forward_edge = None
                if i != (preset_route.__len__() - 1):
                    next_road_id = preset_route[i + 1]
                    next_cross_id = findCrossByTwoRoad(cross_list, road_id, next_road_id)
                    for edge_id in edge_id_list:
                        if edge_id in graph.inc_edges(next_cross_id):
                            forward_edge = edge_id
                    # punish other road of the passing cross along the preset_route
                    inc_edge_list = graph.inc_edges(next_cross_id)
                    inc_edge_list.remove(forward_edge)
                    oppo_inc_edge_id = None
                    oppo_inc_edge_id_list = dicReverseLookup(edge2road_dict, next_road_id) # may including forward and backward edges
                    for edge_id in oppo_inc_edge_id_list:
                        if edge_id in graph.inc_edges(next_cross_id):
                            oppo_inc_edge_id = edge_id
                            inc_edge_list.remove(oppo_inc_edge_id)
                            break
                    # at this time, inc_edge_list = [5001, 5003], punish them
                    for edge_id in inc_edge_list:
                        new_length = graph.edge_data(edge_id)[1] + penaltyFactor // 2
                        present_penalty[edge_id] += penaltyFactor//2  # record in present_penalty
                        new_edge_data = (graph.edge_data(edge_id)[0], new_length,
                                         graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                        graph.update_edge_data(edge_id, new_edge_data)
                else:
                    previous_road_id = preset_route[i - 1]
                    previous_cross_id = findCrossByTwoRoad(cross_list, previous_road_id, road_id)
                    for edge_id in edge_id_list:
                        if edge_id in graph.out_edges(previous_cross_id):
                            forward_edge = edge_id
                new_length = graph.edge_data(forward_edge)[1] + penaltyFactor*2  # PENALTY
                present_penalty[forward_edge] += penaltyFactor*2  # record in present_penalty
                new_edge_data = (graph.edge_data(forward_edge)[0], new_length,
                                 graph.edge_data(forward_edge)[2], graph.edge_data(forward_edge)[3])
                graph.update_edge_data(forward_edge, new_edge_data)

        if ar_flag:
            # ar_deque.popleft()
            # ar_deque already popleft, so append present_penalty to the last to maintain ar_deque length
            ar_deque.append(present_penalty)
        else:
            # update present penalty
            ar_deque[-1] = present_penalty

        previous_depart_time = car[4]

    # FOR DEBUG
    # print(road_count)
    return route_dict


# generate answerInfo
def generateAnswer(route_dict, car_list):
    answer_info = []
    # i = 0
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
        # car_depart_time += i // departure_rate
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