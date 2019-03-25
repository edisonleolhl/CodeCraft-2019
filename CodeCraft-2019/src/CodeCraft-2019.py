import logging
import random
import sys
from altgraph import GraphError
from altgraph.Graph import Graph
from Algorithms import Algorithms
from simulator1 import *

# logging.basicConfig(level=logging.DEBUG,
#                     filename='../logs/CodeCraft-2019.log',
#                     format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S',
#                     filemode='a')

def main():
    if len(sys.argv) != 5:
        logging.info('please input args: car_path, road_path, cross_path, answerPath')
        exit(1)

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    answer_path = sys.argv[4]

    logging.info("car_path is %s" % (car_path))
    logging.info("road_path is %s" % (road_path))
    logging.info("cross_path is %s" % (cross_path))
    logging.info("answer_path is %s" % (answer_path))
    print("answer_path is %s" % (answer_path))
    car_list, road_list, cross_list = readFiles(car_path, road_path, cross_path)
    # car_list = sorted(car_list, key=lambda x: x[-2], reverse=True) # fast car scheduled first
    graph = Graph()
    initMap(graph, road_list, cross_list)
    # route_list = findRouteForCar(graph, car_list)
    route_list = chooseRouteForCar(graph, car_list)

    carInfo = open(car_path, 'r').read().split('\n')[1:]
    roadInfo = open(road_path, 'r').read().split('\n')[1:]
    crossInfo = open(cross_path, 'r').read().split('\n')[1:]


    # alternativeAns = []
    # alternativeTime = []
    for i in range(1):
        answerInfo = generateAnswer(route_list, car_list)
        # alternativeAns.append(answerInfo)
        simulate = simulation(carInfo, roadInfo, crossInfo, answerInfo)
        time = simulate.simulate()
        # alternativeTime.append(time)
        print('Current schedule time: %d' %time)

    # answerInfo = alternativeAns[alternativeTime.index(min(alternativeTime))]
    writeFiles(answerInfo, answer_path)
    # print('Final schedule time: %d' %min(alternativeTime))
#
# to read input file
# output:
# road_list = [['5000', '10', '5', '1', '1', '2', '1'],
#               ...
#               ['5059', '10', '5', '1', '35', '36', '1']]
# car_list = [[...], ..., [...]]
# cross_list = [[...], ..., [...]]
def readFiles(car_path, road_path, cross_path):
    car_list = []
    road_list = []
    cross_list = []
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
    return car_list, road_list, cross_list


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

# search ALL route of graph,
def searchRoute(graph):
    road_count = {}
    for edge_id in graph.edge_list():
        road_id = graph.edge_data(edge_id)[0]
        road_count.setdefault(road_id, 0)
    algo = Algorithms()
    route_list = {}
    for start in graph.node_list():
        for end in graph.node_list():
            if start == end:
                continue
            # path1 = algo.ksp_yen(graph, start, end, 2)[0]['path']
            # path2 = algo.ksp_yen(graph, start, end, 2)[1]['path']
            # path3 = algo.simple_path(graph, start, end)
            path1 = algo.shortest_path(graph, start, end)
            path2 = algo.simple_path(graph, start, end)
            rand = random.random()
            if rand > 0.1:
                path = path1
            else:
                path = path1
            # elif rand > 0.1:
            #     path = path2
            # else:
            #     path = path3
            if not path:
                continue
            if len(path) > 1:
                route = []
                for i in range(len(path)-1):
                    edge_id = graph.edge_by_node(path[i], path[i+1])
                    road_id = graph.edge_data(edge_id)[0]
                    new_length = graph.edge_data(edge_id)[1] + 35
                    new_edge_data = (road_id, new_length, graph.edge_data(edge_id)[2], graph.edge_data(edge_id)[3])
                    graph.update_edge_data(edge_id, new_edge_data)
                    road_count[road_id] +=1
                    route.append(road_id)
                route_list[(start, end)] = route
    return route_list

# if car number > node^2 (approximataly), chooseRouteForCar is faster than findRouteForCar
def chooseRouteForCar(graph, car_list):
    route_list = []
    all_route_list = searchRoute(graph)
    for car in car_list:
        s = (car[1], car[2])
        route_list.append(all_route_list[s])
    return route_list


# if car number < node^2 (approximataly), findRouteForCar is faster than chooseRouteForCar
def findRouteForCar(graph, car_list):
    algo = Algorithms()
    route_list = []
    for car in car_list:
        # path1 = algo.ksp_yen(graph, car[1], car[2], 2, car[-2])[0]['path']
        # path2 = algo.ksp_yen(graph, car[1], car[2], 2, car[-2])[1]['path']
        path1 = algo.shortest_path(graph, car[1], car[2], car[-2])
        path2 = algo.simple_path(graph, car[1], car[2])
        if random.random()>0.01:
            path = path1
        else:
            path = path2
        if len(path) > 1:
            route = []
            for i in range(len(path)-1):
                edge_id = graph.edge_by_node(path[i], path[i+1])
                road_id = graph.edge_data(edge_id)[0]
                route.append(road_id)
        route_list.append(route)
    return route_list

# generate answerInfo
def generateAnswer(route_list, car_list):
    answerInfo = []
    for i in range(len(car_list)):
        route = route_list[i]
        route = str(route).strip('[').strip(']')
        car_id = car_list[i][0]
        plan_time = car_list[i][-1]
        speed = car_list[i][-2]
        car_depart_time = plan_time
        if speed == 2:
            car_depart_time = plan_time
        elif speed == 4:
            car_depart_time = plan_time
        elif speed == 6:
            car_depart_time = plan_time
        elif speed == 8:
            car_depart_time = plan_time
        car_depart_time += i // 28
        answerInfo.append('(' + str(car_id) + ', ' + str(car_depart_time) + ', ' + str(route) + ')')
    return answerInfo


# to write output file
def writeFiles(answerInfo, answer_path):
    with open(answer_path, 'w') as answer_file:
        for ans in answerInfo:
            answer_file.write(ans + '\n')

if __name__ == "__main__":
    main()