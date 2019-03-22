import logging
import sys
from altgraph import GraphError
from altgraph.Graph import Graph
from Algorithms import Algorithms
from simulator import *

logging.basicConfig(level=logging.DEBUG,
                    filename='../logs/CodeCraft-2019.log',
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')

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
    graph = Graph()
    initMap(graph, road_list, cross_list)
    route_list = findRouteForCar(graph, car_list)
    writeFiles(route_list, car_list, answer_path)

    carInfo = open(car_path, 'r').read().split('\n')[1:]
    roadInfo = open(road_path, 'r').read().split('\n')[1:]
    crossInfo = open(cross_path, 'r').read().split('\n')[1:]
    answerInfo = open(answer_path, 'r').read().split('\n')

    for i in range(2):
        simulate = simulation(carInfo, roadInfo, crossInfo, answerInfo)
        time = simulate.simulate()
        print('schedule time: %d' %time)

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

def findRouteForCar(graph, car_list):
    algo = Algorithms()
    route_list = []
    for car in car_list:
        path = algo.shortest_path(graph, car[1], car[2])
        if len(path) > 1:
            route = []
            for i in range(len(path)-1):
                edge_id = graph.edge_by_node(path[i], path[i+1])
                road_id = graph.edge_data(edge_id)[0]
                route.append(road_id)
        route_list.append(route)
    return route_list


# to write output file
def writeFiles(route_list, car_list, answer_path):
    with open(answer_path, 'w') as answer_file:
        for i in range(len(car_list)):
            route = route_list[i]
            route = str(route).strip('[').strip(']')
            car_id = car_list[i][0]
            plan_time = car_list[i][-1]
            speed = car_list[i][-2]
            car_depart_time = plan_time
            if speed == 2:
                car_depart_time = plan_time + 12
            elif speed == 4:
                car_depart_time = plan_time + 8
            elif speed == 6:
                car_depart_time = plan_time + 4
            elif speed == 8:
                car_depart_time = plan_time
            car_depart_time += i//13
            answer_file.write('(' + str(car_id) + ', ' +
                              str(car_depart_time) + ', ' +
                              str(route) +
                              ')\n')

if __name__ == "__main__":
    main()