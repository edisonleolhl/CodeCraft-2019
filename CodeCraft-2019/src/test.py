from Algorithms import Algorithms
from altgraph.Graph import Graph
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

def main():
    algo = Algorithms()
    graph = Graph()
    for i in range(6):
        graph.add_node(i+1)
    graph.add_edge(1, 2, 30)
    graph.add_edge(2, 1, 5)
    graph.add_edge(1, 3, 15)
    graph.add_edge(3, 2, 10)
    graph.add_edge(2, 5, 20)
    graph.add_edge(2, 6, 30)
    graph.add_edge(3, 6, 15)
    graph.add_edge(6, 5, 10)
    graph.add_edge(5, 4, 10)
    graph.add_edge(6, 4, 30)
    # # graph.hide_edge(8)
    # print(graph.out_nbrs(1))
    # print(graph.out_nbrs(3))
    # print(graph.get_hops(4,5))
    # print(graph.get_hops(1,4))
    # print(graph.forw_bfs(4))
    # print(graph.out_degree(1))
    # print(graph.tail(1))
    print('dijkstra shortest path is ' + str(algo.shortest_path(graph, 4, 5)))
    # for node in graph.iterdfs(1, 4):
    #     print(node)
    # print(algo.ksp_yen(graph, 1, 4, 4))
    # print(algo.simple_path(graph, 3, 1))
    print(searchRoute(graph))

if __name__ == "__main__":
    main()