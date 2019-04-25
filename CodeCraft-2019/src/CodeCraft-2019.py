import logging
import sys
from altgraph import GraphError
from altgraph.Graph import Graph
from collections import deque
from collections import defaultdict
import copy
from Algorithms import Algorithms
# from Scheduler import *
from NodeadlockScheduler import *


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

    car_list, road_list, cross_list, preset_answer_list = readFiles(car_path, road_path, cross_path, preset_answer_path)
    carInfo = open(car_path, 'r').read().split('\n')[1:]  # ['(61838, 1716, 800, 4, 72, 0, 0)', ...]
    roadInfo = open(road_path, 'r').read().split('\n')[1:]
    crossInfo = open(cross_path, 'r').read().split('\n')[1:]
    preset_answer_info = generatePresetAnswer(preset_answer_path)

    graph = Graph()
    graph = initMap(graph, road_list, cross_list)

    queue_length = 100

    # car_list = sorted(car_list, key=lambda x: x[4]) # first car scheduled first for non-preset cars
    preset = [x for x in car_list if x[6] == 1]
    car_list = replaceDepartTimeForPresetCar(car_list, preset_answer_list)
    last_preset_depart_time = max([x[4] for x in preset])
    split_time = (last_preset_depart_time + 100) // 100 * 100
    print("last_preset_depart_time: %s, split_time: %s" % (last_preset_depart_time, split_time))

    # priority cars depart first, then non-priority cars depart
    priority_non_preset = [x for x in car_list if x[5] == 1 and x[6] == 0]
    non_priority_non_preset = [x for x in car_list if x[5] == 0 and x[6] == 0]
    priority_non_preset = sorted(priority_non_preset, key=lambda x: x[4])
    non_priority_non_preset = sorted(non_priority_non_preset, key=lambda x: x[4])
    car_list = priority_non_preset + non_priority_non_preset
    ori_car_list = copy.deepcopy(car_list)

    if len(cross_list) > 140:
        # for training map 1 cross=142
        penaltyFactor = 80
        departure_rate = 56
        acc_departure_rate = 60
        last_d = 500

    else:
        # for training map 2 cross=134
        penaltyFactor = 140
        departure_rate = 50
        acc_departure_rate = 55
        last_d = 100


    # TODO 3: to avoid 'program runs too long'
    #  After realtime test, successful scheduling(including route calculation) cannot be over 2 times
    loop = 4
    JudgeTime_list = [999999 for x in range(loop)]
    answer_info_list = [None for x in range(loop)]
    garanteeFlag = False
    last_deadlock = True
    step = 10
    for i in range(loop):
        print("current departure rate: %s, acc departure rate: %s" % (departure_rate, acc_departure_rate))
        # car_list = ori_car_list # This is totally wrong! because car_list refer to ori_car_list, not copy the value from ori_car_list !!!
        car_list = copy.deepcopy(ori_car_list)
        car_list = chooseDepartTimeForNonPresetCar(car_list, departure_rate, acc_departure_rate, split_time, last_d)
        # merge non-preset cars and preset cars into car_list
        car_list.extend(preset)
        # sort car_list in ascending depart_time, so that dynamic penalty works
        car_list = sorted(car_list, key=lambda x: x[4])

        # TODO 2: static change(pre-decide) preset route, to enable this, not to comment line below
        # changed_route_dict = changePresetRoute(car_list, road_list, preset_answer_list)
        # print('change preset car number: %s' % changed_route_dict.__len__())
        changed_route_dict = {}  # TODO 2: comment this to enable pre-decide preset car

        route_dict = findRouteForCar(graph, car_list, cross_list, road_list, preset_answer_list, penaltyFactor,
                                     queue_length, changed_route_dict)
        # print('find route number: %s' % route_dict.__len__())
        answer_info = generateAnswer(route_dict, car_list)
        if garanteeFlag is False:
            scheduler = NodeadlockScheduler(carInfo, roadInfo, crossInfo, answer_info, preset_answer_info)
            isDeadLock, time, JudgeTime = scheduler.schedule()
            print('current JudgeTime: %s, isDeadLock: %s\n' % (JudgeTime, isDeadLock))
        else:
            # last time, the depart rate is very slow, don't schedule to save time
            JudgeTime_list[i] = 1
            answer_info_list[i] = answer_info
            break
        if isDeadLock:
            if last_deadlock:
                if i != 0 and answer_info_list.count(None) == loop:  # previous scheduling are all deadlock
                    step = step * 2
                    print('sequent deadlock, double step, current step: %s' % step)
                elif i == 2 and answer_info_list.count(None) != loop:
                    step = step // 2
                departure_rate -= step
                acc_departure_rate -= step
                print('depart rate - step=%s, now departure rate=%s, acc departure rate=%s' % (
                step, departure_rate, acc_departure_rate))
            else:
                step = step // 2
                departure_rate -= step
                acc_departure_rate -= step
                print(
                    'last time ok, this time deadlock, step half to -%s, now departure rate=%s, acc departure rate=%s' % (
                    step, departure_rate, acc_departure_rate))
            last_deadlock = True
        else:
            JudgeTime_list[i] = JudgeTime
            answer_info_list[i] = answer_info
            if last_deadlock:
                if i == 0:
                    # first time is ok, then try a big departure rate to reduce running time and to get a deadlock(so that optimal is between first schedule and second schedule
                    step = step * 2
                    departure_rate += step
                    acc_departure_rate += step
                    print('first time ok, try big, +step=%s, departure rate=%s, acc departure rate=%s' % (
                    step, departure_rate, acc_departure_rate))
                else:
                    step = step // 2
                    departure_rate += step
                    acc_departure_rate += step
                    print(
                        'last time (true) deadlock, this time ok, step half to +%s, now departure rate=%s, acc departure rate=%s' % (
                            step, departure_rate, acc_departure_rate))
            last_deadlock = False
        if i == loop - 3 and answer_info_list.count(None) == 2:
            print('runs ok 2 times in first %s time, skip the last schedule' % (loop - 2))
            break
        if i == loop - 2:
            if answer_info_list.count(None) == loop:
                # garantee the last calculation have a feasible solution
                departure_rate = 20
                acc_departure_rate = 25
                garanteeFlag = True  # don't have to call scheduler program
            elif answer_info_list.count(None) <= 2:
                # no running time for the last scheduling, get the current optimal answer info
                print('runs ok 2 times in first %s time, skip the last schedule' % (loop - 1))
                break
        del graph
        graph = Graph()
        graph = initMap(graph, road_list, cross_list)

    i = JudgeTime_list.index(min(JudgeTime_list))
    print('optimal judge time: %d' % min(JudgeTime_list))
    answer_info = answer_info_list[i]
    writeFiles(answer_info, answer_path)


def chooseDepartTimeForNonPresetCar(car_list, departure_rate, acc_departure_rate, split_time, last_d):
    non_preset_index = 0
    for i in range(car_list.__len__()):
        if car_list[i][-1] == 0:
            depart_time = car_list[i][4]  # depart_time = planTime
            # print("No.%d car, No.%d non-preset car, depart_time=%d" %(i, non_preset_index, depart_time))
            # preset route may be overload among some roads, when preset cars finish trip, speed up departure
            if (non_preset_index // departure_rate) < split_time:
                if non_preset_index // departure_rate >= depart_time:
                    depart_time = non_preset_index // departure_rate
                else:
                    # depart_time = planTime
                    pass
            else:
                depart_time = split_time + (non_preset_index - split_time * departure_rate) // acc_departure_rate
                if i >= (car_list.__len__() - last_d):
                    depart_time -= 1
            car_list[i][4] = depart_time
            non_preset_index += 1
    print(car_list[i])
    return car_list


# This func uses dynamic penalty, using Auto Regressive model.
# Return: car's route
def findRouteForCar(graph, car_list, cross_list, road_list, preset_answer_list, penaltyFactor, queue_length,
                    changed_route_dict):
    # {car_id: [5001, 5002, ...]}
    preset_route_dict = {}
    for preset_answer in preset_answer_list:
        preset_route_dict[preset_answer[0]] = preset_answer[2:]

    road_dict = {}
    for road in road_list:
        road_dict[road[0]] = road[1:]

    # {road_id: edge_id} is wrong, because edge_id is unique, road_id is not unique (duplex road)
    # key in dictionary is unique, so set {edge_id: road:id}
    edge2road_dict = {}
    for edge_id in graph.edge_list():
        road_id = graph.edge_data(edge_id)[0]
        edge2road_dict[edge_id] = road_id

    # TODO 2: dynamic preset route change
    max_change = preset_answer_list.__len__() // 10
    changed_cnt = 0

    # 4.12 update: Auto Regressive model !!!
    # Penalty becomes failure when the car get the destination, so 'release' the 'penalty' along the road!
    # ar_deque keeps all the penalty information, its length indicating continuous timeslice remains constant
    # ar_deque when append to the last, delete the first
    # ar_deque = {defaultdict(<class 'int'>, {edge_id: penalty}), defaultdict(<class 'int'>, {edge_id: penalty}), ...}
    ar_deque = deque([defaultdict(int) for x in range(queue_length)])
    previous_depart_time = None

    algo = Algorithms()
    route_dict = {}
    penalty_flag = False
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

        # punish severely for those cars whose depart_time is greater than 1000
        if not penalty_flag and depart_time >= 1100:
            penaltyFactor = int(penaltyFactor * 1.5)
            penalty_flag = True

        if depart_time != previous_depart_time:
            # new timeslice
            ar_flag = True  # start auto regressive
            present_penalty = defaultdict(int)  # defaultdict(<class 'int'>, {edge_id: penalty})

            # TODO 1: AR model without factor
            # 'Release' penalty of the timeslice 'queue_length' ago, subtract penalty value
            release_penalty = ar_deque.popleft()  # release_penalty = {edge_id: penalty, ...}
            for edge_id, p_value in release_penalty.items():
                new_length = graph.edge_data(edge_id)[1] - p_value
                new_edge_data = (graph.edge_data(edge_id)[0], new_length,
                                 graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                graph.update_edge_data(edge_id, new_edge_data)

            # TODO 1: AR model with factor
            # average factor 0.2 0.4 0.6 0.8 1.0
            # init all edges
            # for edge_id in graph.edge_list():
            #     road_id = edge2road_dict[edge_id]
            #     origin_length = road_dict[road_id][0]
            #     new_edge_data = (graph.edge_data(edge_id)[0], origin_length,
            #                      graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
            #     graph.update_edge_data(edge_id, new_edge_data)
            # # previous states have less effect on present state
            # for i, temp_penalty in enumerate(ar_deque):
            #     for edge_id, p_value in temp_penalty.items():
            #         new_length = graph.edge_data(edge_id)[1]
            #         # eg: q=200, divided into 5 groups, each multiplied by 0.2, 0.4, 0.6, 0.8, 1.0
            #         # new_length += p_value * 0.2 * (i//(queue_length//5)+1)
            #         # eg: q=150, divided into 3 groups, each multiplied by 0.3, 0.6, 0.9
            #         new_length += p_value * 0.3 * (i//(queue_length//3)+1)
            #         new_edge_data = (graph.edge_data(edge_id)[0], new_length,
            #                          graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
            #         graph.update_edge_data(edge_id, new_edge_data)

            if depart_time % 200 == 0:
                print('Present depart_time=%s, release depart_time=%s penalty '
                      % (depart_time, int(depart_time) - queue_length))
        else:
            # additive
            present_penalty = ar_deque[-1]  # present_penalty = {edge_id: penalty(already increment length), ...}

        # non preset car
        if car[-1] == 0:
            path = algo.shortest_path(graph, car[1], car[2])  # path = [node1(cross1_id), node2, ...]
            if path.__len__() > 2:  # don't punish only one road route
                route, present_penalty = penalty(graph, present_penalty, penaltyFactor, path=path)
            else:
                road_id = graph.edge_by_node(path[0], path[1])
                route = [road_id]
            route_dict[car[0]] = route

        # ----------------------------DON'T change preset route------------------------------------
        # TODO 2: choose one way in three choices
        # else:
        #     preset_route = preset_route_dict[car[0]]
        #     if preset_route.__len__() > 1:  # don't punish only one road route
        #         present_penalty = penalty(graph, present_penalty, penaltyFactor, edge2road_dict=edge2road_dict,
        #                                   cross_list=cross_list, preset_route=preset_route)

        # ----------------------------static change preset route------------------------------------
        # TODO 2: choose one way in three choices
        # preset car not changing route
        # elif car[0] not in changed_route_dict.keys():
        #     preset_route = preset_route_dict[car[0]] # preset_route = [road_id, road_id, ...]
        #     if preset_route.__len__() > 1: # don't punish only one road route
        #         present_penalty = penalty(graph, present_penalty, penaltyFactor, edge2road_dict=edge2road_dict,
        #                                      cross_list=cross_list, preset_route=preset_route)
        # # preset car changing route
        # else:
        #     path = algo.shortest_path(graph, car[1], car[2]) # path = [node1(cross1_id), node2, ...]
        #     if path.__len__() > 2: # don't punish only one road route
        #         route, present_penalty = penalty(graph, present_penalty, penaltyFactor, path=path)
        #     else:
        #         road_id = graph.edge_by_node(path[0], path[1])
        #         route = [road_id]
        #     print('preset car: %s planTime(=depart_time): %s change route to %s'%(car[0], car[4], route))
        #     route_dict[car[0]] = route

        # -------------------------dynamic change preset route-----------------------------------
        # TODO 2: choose one way in three choices
        else:
            preset_route = preset_route_dict[car[0]]
            dij_path = algo.shortest_path(graph, car[1], car[2])
            dij_route_weight = 0
            for i in range(dij_path.__len__()-1):
                edge_id = graph.edge_by_node(dij_path[i], dij_path[i+1])
                dij_route_weight += graph.edge_data(edge_id)[1] / graph.edge_data(edge_id)[3]
            preset_route_weight = 0
            for i, road_id in enumerate(preset_route):
                edge_id_list = dicReverseLookup(edge2road_dict,
                                                road_id)  # edge_id_list may including forward and backward edges
                forward_edge = None
                if i != (preset_route.__len__() - 1):
                    next_road_id = preset_route[i + 1]
                    next_cross_id = findCrossByTwoRoad(cross_list, road_id, next_road_id)
                    for edge_id in edge_id_list:
                        if edge_id in graph.inc_edges(next_cross_id):
                            forward_edge = edge_id
                    preset_route_weight += graph.edge_data(forward_edge)[1] / graph.edge_data(forward_edge)[3]
                else:
                    previous_road_id = preset_route[i - 1]
                    previous_cross_id = findCrossByTwoRoad(cross_list, previous_road_id, road_id)
                    for edge_id in edge_id_list:
                        if edge_id in graph.out_edges(previous_cross_id):
                            forward_edge = edge_id
                    preset_route_weight += graph.edge_data(forward_edge)[1] / graph.edge_data(forward_edge)[3]
            # check the route weight difference between dij path and preset path
            if (changed_cnt < max_change) and (preset_route_weight - dij_route_weight > 0.2 * dij_route_weight):
                # print('No.%s change preset car: %s route, preset_route_weight: %s, dij_route_weight: %s,'%(changed_cnt, car[0], preset_route_weight, dij_route_weight))
                route = []  # route = [road_id, road_id, ...]
                for i in range(dij_path.__len__() - 1):
                    edge_id = graph.edge_by_node(dij_path[i], dij_path[i + 1])
                    road_id = graph.edge_data(edge_id)[0]
                    new_length = graph.edge_data(edge_id)[1] + penaltyFactor  # PENALTY
                    present_penalty[edge_id] += penaltyFactor  # record in present_penalty
                    new_edge_data = (road_id, new_length,
                                     graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                    graph.update_edge_data(edge_id, new_edge_data)
                    inc_edge_list = graph.inc_edges(dij_path[i + 1])
                    inc_edge_list.remove(edge_id)
                    if i != (dij_path.__len__() - 2):
                        oppo_inc_edge_id = graph.edge_by_node(dij_path[i + 2], dij_path[i + 1])
                        if oppo_inc_edge_id is not None:
                            inc_edge_list.remove(oppo_inc_edge_id)
                    # at this time, inc_edge_list = [5001, 5003]
                    for edge_id in inc_edge_list:
                        new_length = graph.edge_data(edge_id)[1] + penaltyFactor // 2
                        present_penalty[edge_id] += penaltyFactor // 2  # record in present_penalty
                        new_edge_data = (graph.edge_data(edge_id)[0], new_length,
                                         graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                        graph.update_edge_data(edge_id, new_edge_data)
                    route.append(road_id)
                route_dict[car[0]] = route
                changed_cnt += 1
            else:
                for i, road_id in enumerate(preset_route):
                    edge_id_list = dicReverseLookup(edge2road_dict,
                                                    road_id)  # edge_id_list may including forward and backward edges
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
                        oppo_inc_edge_id_list = dicReverseLookup(edge2road_dict,
                                                                 next_road_id)  # may including forward and backward edges
                        for edge_id in oppo_inc_edge_id_list:
                            if edge_id in graph.inc_edges(next_cross_id):
                                oppo_inc_edge_id = edge_id
                                inc_edge_list.remove(oppo_inc_edge_id)
                                break
                        # at this time, inc_edge_list = [5001, 5003], punish them
                        for edge_id in inc_edge_list:
                            new_length = graph.edge_data(edge_id)[1] + penaltyFactor // 2
                            present_penalty[edge_id] += penaltyFactor // 2  # record in present_penalty
                            new_edge_data = (graph.edge_data(edge_id)[0], new_length,
                                             graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                            graph.update_edge_data(edge_id, new_edge_data)
                    else:
                        previous_road_id = preset_route[i - 1]
                        previous_cross_id = findCrossByTwoRoad(cross_list, previous_road_id, road_id)
                        for edge_id in edge_id_list:
                            if edge_id in graph.out_edges(previous_cross_id):
                                forward_edge = edge_id
                    new_length = graph.edge_data(forward_edge)[1] + penaltyFactor * 2  # PENALTY
                    present_penalty[forward_edge] += penaltyFactor * 2  # record in present_penalty
                    new_edge_data = (graph.edge_data(forward_edge)[0], new_length,
                                     graph.edge_data(forward_edge)[2], graph.edge_data(forward_edge)[3])
                    graph.update_edge_data(forward_edge, new_edge_data)

        if ar_flag:
            # ar_deque.popleft() # TODO 1: not comment this line to enable AR model with factor
            # ar_deque already popleft, so append present_penalty to the last to maintain ar_deque length
            ar_deque.append(present_penalty)
        else:
            # update present penalty
            ar_deque[-1] = present_penalty

        previous_depart_time = car[4]

    return route_dict


# path for non-preset cars, path = [cross_id, cross_id, ...]
# route for preset cars, route = [road_id, road_id, ...]
def penalty(graph, present_penalty, penaltyFactor, edge2road_dict=None, cross_list=None, path=None, preset_route=None):
    # for non preset car
    if path is not None:
        route = []  # route = [road_id, road_id, ...]
        for i in range(path.__len__() - 1):
            edge_id = graph.edge_by_node(path[i], path[i + 1])
            road_id = graph.edge_data(edge_id)[0]
            new_length = graph.edge_data(edge_id)[1] + penaltyFactor  # PENALTY
            present_penalty[edge_id] += penaltyFactor  # record in present_penalty
            new_edge_data = (road_id, new_length,
                             graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
            graph.update_edge_data(edge_id, new_edge_data)

            # 4.11 update: punish other road of passing cross along the route
            # eg: four edge(road): 5000, 5001, 5002, 5003 going to the cross(node):100
            # car's present edge_id (or road_id) = 5000, next edge_id = 5002,
            # Therefore, other road = 5001, 5003, PUNISH these two roads
            # Tips: doesn't punish the destination cross's other road
            # (considering get to the destination refering to go_straight which has higher priority
            inc_edge_list = graph.inc_edges(path[i + 1])
            inc_edge_list.remove(edge_id)
            if i != (path.__len__() - 2):
                oppo_inc_edge_id = graph.edge_by_node(path[i + 2], path[i + 1])
                if oppo_inc_edge_id is not None:
                    inc_edge_list.remove(oppo_inc_edge_id)
            # at this time, inc_edge_list = [5001, 5003]
            for edge_id in inc_edge_list:
                new_length = graph.edge_data(edge_id)[1] + penaltyFactor // 2
                present_penalty[edge_id] += penaltyFactor // 2  # record in present_penalty
                new_edge_data = (graph.edge_data(edge_id)[0], new_length,
                                 graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                graph.update_edge_data(edge_id, new_edge_data)
            route.append(road_id)
        return route, present_penalty
    # for preset car
    else:
        for i, road_id in enumerate(preset_route):
            edge_id_list = dicReverseLookup(edge2road_dict,
                                            road_id)  # edge_id_list may including forward and backward edges
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
                oppo_inc_edge_id_list = dicReverseLookup(edge2road_dict,
                                                         next_road_id)  # may including forward and backward edges
                for edge_id in oppo_inc_edge_id_list:
                    if edge_id in graph.inc_edges(next_cross_id):
                        oppo_inc_edge_id = edge_id
                        inc_edge_list.remove(oppo_inc_edge_id)
                        break
                # at this time, inc_edge_list = [5001, 5003], punish them
                for edge_id in inc_edge_list:
                    new_length = graph.edge_data(edge_id)[1] + penaltyFactor // 2
                    present_penalty[edge_id] += penaltyFactor // 2  # record in present_penalty
                    new_edge_data = (graph.edge_data(edge_id)[0], new_length,
                                     graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                    graph.update_edge_data(edge_id, new_edge_data)
            else:
                previous_road_id = preset_route[i - 1]
                previous_cross_id = findCrossByTwoRoad(cross_list, previous_road_id, road_id)
                for edge_id in edge_id_list:
                    if edge_id in graph.out_edges(previous_cross_id):
                        forward_edge = edge_id
            new_length = graph.edge_data(forward_edge)[1] + penaltyFactor * 2  # PENALTY
            present_penalty[forward_edge] += penaltyFactor * 2  # record in present_penalty
            new_edge_data = (graph.edge_data(forward_edge)[0], new_length,
                             graph.edge_data(forward_edge)[2], graph.edge_data(forward_edge)[3])
            graph.update_edge_data(forward_edge, new_edge_data)
        return present_penalty


# 10% of the preset car's route could be changed
def changePresetRoute(car_list, road_list, preset_answer_list):
    car_dict = {}
    for car in car_list:
        car_dict[car[0]] = car[1:]
    road_dict = {}
    for road in road_list:
        road_dict[road[0]] = road[1:]
    preset_answer_priority = []
    for preset_answer in preset_answer_list:
        car_id = preset_answer[0]
        if car_dict[car_id][-2] == 1:
            preset_answer_priority.append(preset_answer)
    max_change = preset_answer_list.__len__() // 10
    # list below are all default ascending !
    # preset_answer_depart_time = sorted(preset_answer_list, key=lambda x:x[1], reverse=True)
    # preset_answer_road_number = sorted(preset_answer_list, key=lambda x:len(x), reverse=True)
    preset_answer_priority_depart_time = sorted(preset_answer_priority, key=lambda x: x[1], reverse=True)
    # preset_answer_priority_road_number = sorted(preset_answer_priority, key=lambda x:len(x), reverse=True)
    changed_route_dict = {}
    for answer in preset_answer_priority_depart_time[:max_change]:
        changed_route_dict[answer[0]] = answer[1:]
    return changed_route_dict


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
            preset_answer_line = preset_answer_line.replace(' ', '').replace('(', '').replace(')', '').strip().split(
                ',')
            preset_answer_line = [int(x) for x in preset_answer_line]
            preset_answer_list.append(preset_answer_line)
    return car_list, road_list, cross_list, preset_answer_list


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


# 'planTime' of the preset car in car.txt will be replaced by the preset 'time' in presetAnswer.txt
def replaceDepartTimeForPresetCar(car_list, preset_answer_list):
    # {car_id: time}
    preset_time_dict = {}
    for preset_answer in preset_answer_list:
        preset_time_dict[preset_answer[0]] = preset_answer[1]
    for i in range(car_list.__len__()):
        if car_list[i][-1] == 1:
            car_list[i][4] = preset_time_dict[car_list[i][0]]
    return car_list


def generateAnswer(route_dict, car_list):
    answer_info = []
    # i = 0
    for car in car_list:
        if car[0] in route_dict.keys():
            route = route_dict[car[0]]
            route = str(route).strip('[').strip(']')
            car_id = car[0]
            plan_time = car[4]
            depart_time = plan_time
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


def writeFiles(answerInfo, answer_path):
    with open(answer_path, 'w') as answer_file:
        for ans in answerInfo:
            answer_file.write(ans + '\n')


if __name__ == "__main__":
    main()
