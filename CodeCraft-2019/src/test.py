from Algorithms import Algorithms
from altgraph.Graph import Graph
from altgraph import GraphError



def main():
    algo = Algorithms()
    graph = Graph()
    for i in range(7):
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
    # print(graph.get_hops(4,5))
    # print(graph.get_hops(1,4))
    # print(graph.forw_bfs(4))

    print('dijkstra shortest path is ' + str(algo.shortest_path(graph, 1, 4)))
    for node in graph.iterdfs(3,5):
        print(node)
    # print(algo.ksp_yen(graph, 1, 4, 4))


if __name__ == "__main__":
    main()