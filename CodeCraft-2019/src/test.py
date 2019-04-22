from Algorithms import Algorithms
import sys
from altgraph.Graph import Graph
import numpy as np
import random
from altgraph import GraphError

def searchRoute(graph):
    algo = Algorithms()
    route_list = {}
    for start in graph.node_list():
        for end in graph.node_list():
            if start == end:
                continue
            # path1 = algo.ksp_yen(graph, car[1], car[2], 2, car[-2])[0]['path']
            # path2 = algo.ksp_yen(graph, car[1], car[2], 2, car[-2])[1]['path']
            path1 = algo.shortest_path(graph, start, end)
            path2 = algo.simple_path(graph, start, end)
            if random.random()>0.01:
                path = path1
            else:
                path = path2
            if not path:
                continue
            if len(path) > 1 :
                # route = []
                # for i in range(len(path)-1):
                #     # edge_id = graph.edge_by_node(path[i], path[i+1])
                #     # road_id = graph.edge_data(edge_id)[0]
                #     route.append(edge_id)
                route_list[(start, end)] = path
    return route_list

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

def replaceDepartTimeForPresetCar(car_list, preset_answer_list):
    # {car_id: time}
    preset_time_dict = {}
    for preset_answer in preset_answer_list:
        preset_time_dict[preset_answer[0]] = preset_answer[1]
    for i in range(car_list.__len__()):
        if car_list[i][-1] == 1:
            car_list[i][4] = preset_time_dict[car_list[i][0]]
    return car_list

def main():
    # algo = Algorithms()
    # graph = Graph()
    # for i in range(6):
    #     graph.add_node(i+1)
    # # print(graph.node_list())
    # graph.add_edge(1, 2, 30)
    # graph.add_edge(2, 1, 5)
    # graph.add_edge(1, 3, 15)
    # graph.add_edge(3, 2, 10)
    # graph.add_edge(2, 5, 20)
    # graph.add_edge(2, 6, 30)
    # graph.add_edge(3, 6, 15)
    # graph.add_edge(6, 5, 10)
    # graph.add_edge(5, 4, 10)
    # graph.add_edge(6, 4, 30)
    # # # graph.hide_edge(8)
    # print(graph.out_edges(2))
    # print(graph.out_nbrs(3))
    # print(graph.get_hops(4,5))
    # print(graph.get_hops(1,4))
    # print(graph.forw_bfs(4))
    # print(graph.out_degree(1))
    # print(graph.tail(1))
    # print('dijkstra shortest path is ' + str(algo.shortest_path(graph, 4, 5)))
    # for node in graph.iterdfs(1, 4):
    #     print(node)
    # print(algo.ksp_yen(graph, 1, 4, 4))
    # print(algo.simple_path(graph, 3, 1))
    # print(searchRoute(graph))

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    preset_answer_path = sys.argv[4]
    answer_path = sys.argv[5]
    #
    car_list, road_list, cross_list, preset_answer_list= readFiles(car_path, road_path, cross_path, preset_answer_path)
    car_list = replaceDepartTimeForPresetCar(car_list, preset_answer_list)

    preset = [x for x in car_list if x[6] == 1]
    priority_preset = [x for x in car_list if x[5] == 1 and x[6] == 1]
    pp100 = priority_preset[:100]
    preset_answer_list100 = preset_answer_list[0:100]
    non_priority_preset = [x for x in car_list if x[5] == 0 and x[6] == 1]
    priority_non_preset = [x for x in car_list if x[5] == 1 and x[6] == 0]
    non_priority_non_preset = [x for x in car_list if x[5] == 0 and x[6] == 0]
    priority_preset = sorted(priority_preset, key=lambda x: x[4])
    for item in priority_preset:
        print(item)
    print('priority_preset number: %s'%priority_preset.__len__())
    print('priority_non_preset number: %s'%priority_non_preset.__len__())
    print('non_priority_preset number: %s'%non_priority_preset.__len__())
    print('non_priority_non_preset number: %s'%non_priority_non_preset.__len__())
    # pp = np.array(priority_preset)
    # print(pp)


if __name__ == "__main__":
    main()