import logging
import sys
from altgraph import GraphError
from altgraph.Graph import Graph
# import os
# print(os.path.abspath('.'))
# # /home/lhl/PycharmProjects/CodeCraft-2019
# print(os.path.realpath('.'))
# # /home/lhl/PycharmProjects/CodeCraft-2019
# print(os.path.relpath('.'))
# # .

# logging.basicConfig(level=logging.DEBUG,
#                     filename='logs/CodeCraft-2019.log',
#                     format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S',
#                     filemode='a')

class Algorithms(object):
    def __init__(self):
        """
        Initialization
        """

    def dijkstra(self, graph, start, end=None):
        """
        Dijkstra's algorithm for shortest paths

        `David Eppstein, UC Irvine, 4 April 2002
            <http://www.ics.uci.edu/~eppstein/161/python/>`_

        `Python Cookbook Recipe
            <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/119466>`_

        Find shortest paths from the  start node to all nodes nearer than or
        equal to the end node.

        Dijkstra's algorithm is only guaranteed to work correctly when all edge
        lengths are positive.  This code does not verify this property for all
        edges (only the edges examined until the end vertex is reached), but will
        correctly compute shortest paths even for some graphs with negative edges,
        and will raise an exception if it discovers that a negative edge has
        caused it to make a mistake.

        Adapted to altgraph by Istvan Albert, Pennsylvania State University -
        June, 9 2004
        """
        D = {}    # dictionary of final distances
        P = {}    # dictionary of predecessors
        Q = self._priorityDictionary()    # estimated distances of non-final vertices
        Q[start] = 0

        for v in Q:
            D[v] = Q[v]
            if v == end:
                break

            for w in graph.out_nbrs(v):
                # edge_id = graph.edge_by_node(v, w)
                # vwLength = D[v] + graph.edge_data(edge_id)
                vwLength = D[v] + 1
                if w in D:
                    if vwLength < D[w]:
                        raise GraphError(
                            "Dijkstra: found better path to already-final vertex")
                elif w not in Q or vwLength < Q[w]:
                    Q[w] = vwLength
                    P[w] = v

        return (D, P)


    def shortest_path(self, graph, start, end):
        """
        Find a single shortest path from the *start* node to the *end* node.
        The input has the same conventions as dijkstra(). The output is a list of
        the nodes in order along the shortest path.

        **Note that the distances must be stored in the edge data as numeric data**
        """

        D, P = self.dijkstra(graph, start, end)
        Path = []
        while 1:
            Path.append(end)
            if end == start:
                break
            end = P[end]
        Path.reverse()
        return Path


    #
    # Utility classes and functions
    #
    class _priorityDictionary(dict):
        '''
        Priority dictionary using binary heaps (internal use only)

        David Eppstein, UC Irvine, 8 Mar 2002

        Implements a data structure that acts almost like a dictionary, with
        two modifications:

            1. D.smallest() returns the value x minimizing D[x].  For this to
               work correctly, all values D[x] stored in the dictionary must be
               comparable.

            2. iterating "for x in D" finds and removes the items from D in sorted
               order. Each item is not removed until the next item is requested,
               so D[x] will still return a useful value until the next iteration
               of the for-loop.  Each operation takes logarithmic amortized time.
        '''

        def __init__(self):
            '''
            Initialize priorityDictionary by creating binary heap of pairs
            (value,key).  Note that changing or removing a dict entry will not
            remove the old pair from the heap until it is found by smallest()
            or until the heap is rebuilt.
            '''
            self.__heap = []
            dict.__init__(self)

        def smallest(self):
            '''
            Find smallest item after removing deleted items from front of heap.
            '''
            if len(self) == 0:
                raise IndexError("smallest of empty priorityDictionary")
            heap = self.__heap
            while heap[0][1] not in self or self[heap[0][1]] != heap[0][0]:
                lastItem = heap.pop()
                insertionPoint = 0
                while 1:
                    smallChild = 2*insertionPoint+1
                    if smallChild+1 < len(heap) and \
                            heap[smallChild] > heap[smallChild+1]:
                        smallChild += 1
                    if smallChild >= len(heap) or lastItem <= heap[smallChild]:
                        heap[insertionPoint] = lastItem
                        break
                    heap[insertionPoint] = heap[smallChild]
                    insertionPoint = smallChild
            return heap[0][1]

        def __iter__(self):
            '''
            Create destructive sorted iterator of priorityDictionary.
            '''
            def iterfn():
                while len(self) > 0:
                    x = self.smallest()
                    yield x
                    del self[x]
            return iterfn()

        def __setitem__(self, key, val):
            '''
            Change value stored in dictionary and add corresponding pair to heap.
            Rebuilds the heap if the number of deleted items gets large, to avoid
            memory leakage.
            '''
            dict.__setitem__(self, key, val)
            heap = self.__heap
            if len(heap) > 2 * len(self):
                self.__heap = [(v, k) for k, v in self.items()]
                self.__heap.sort()
            else:
                newPair = (val, key)
                insertionPoint = len(heap)
                heap.append(None)
                while insertionPoint > 0 and newPair < heap[(insertionPoint-1)//2]:
                    heap[insertionPoint] = heap[(insertionPoint-1)//2]
                    insertionPoint = (insertionPoint-1)//2
                heap[insertionPoint] = newPair

        def setdefault(self, key, val):
            '''
            Reimplement setdefault to pass through our customized __setitem__.
            '''
            if key not in self:
                self[key] = val
            return self[key]


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
    # print(graph)
    # all_shortest_paths = initAllShortestPaths(graph)
    # print(GraphAlgo.shortest_path(graph, 1, 1))
    route_list = findRouteForCar(graph, car_list)
    writeFiles(route_list, car_list, answer_path)

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

            # ignore the lines starting with '#'
            if car_line.startswith('#'):
                continue

            # # delete all blanks
            # car_line = car_line.replace(' ', '')
            # # delete '(' and ')' and '\n'
            # car_line = car_line.replace('(', '').replace(')', '').strip()
            # # split car_line into LIST whose elements are cars info
            # car_line = car_line.split(',')

            # above three lines can be simplified as below
            car_line = car_line.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            car_line = [int(x) for x in car_line]
            car_list.append(car_line)

    with open(road_path, 'r') as road_file:
        for road_line in road_file.readlines():

            # ignore the lines starting with '#'
            if road_line.startswith('#'):
                continue

            # # delete all blanks
            # road_line = car_line.replace(' ', '')
            # # delete '(' and ')' and '\n'
            # road_line = road_line.replace('(', '').replace(')', '').strip()
            # # split road_line into LIST whose elements are cars info
            # road_line = road_line.split(',')

            # above three lines can be simplified as below
            road_line = road_line.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            road_line = [int(x) for x in road_line]
            road_list.append(road_line)

    with open(cross_path, 'r') as cross_file:
        for cross_line in cross_file.readlines():

            # ignore the lines starting with '#'
            if cross_line.startswith('#'):
                continue

            # # delete all blanks
            # cross_line = cross_line.replace(' ', '')
            # # delete '(' and ')' and '\n'
            # cross_line = cross_line.replace('(', '').replace(')', '').strip()
            # # split cross_line into LIST whose elements are cars info
            # cross_line = cross_line.split(',')

            # above three lines can be simplified as below
            cross_line = cross_line.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            cross_line = [int(x) for x in cross_line]
            cross_list.append(cross_line)

    # print(car_list)
    # print(road_list)
    # print(cross_list)
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


# initAllShortestPaths func fails to run because graph is not connected
# calculate all shortest paths in graph, each edges distance is 1 by default
# def initAllShortestPaths(graph):
#     all_shortest_paths = []
#     for i in range(graph.number_of_nodes()):
#         for j in range(graph.number_of_nodes()):
#             GraphAlgo.shortest_path(graph, i+1, j+1)
#     return all_shortest_paths

def findRouteForCar(graph, car_list):
    algo = Algorithms()
    route_list = []
    for car in car_list:
        path = algo.shortest_path(graph, car[1], car[2])
        # print(path)
        if len(path) > 1:
            route = []
            for i in range(len(path)-1):
                edge_id = graph.edge_by_node(path[i], path[i+1])
                road_id = graph.edge_data(edge_id)[0]
                route.append(road_id)
            # print(path, route)
        route_list.append(route)
    # print(route_list)
    return route_list


# to write output file
def writeFiles(route_list, car_list, answer_path):
    with open(answer_path, 'w') as answer_file:
        for i in range(len(car_list)):
            route = route_list[i]
            route = str(route).strip('[').strip(']')
            car_id = car_list[i][0]
            car_depart_time = car_list[i][-1]
            answer_file.write('(' + str(car_id) + ', ' +
                              str(car_depart_time) + ', ' +
                              str(route) +
                              ')\n')

if __name__ == "__main__":
    main()