from altgraph import GraphError
from operator import itemgetter
from collections import deque
import random

class Algorithms(object):
    def __init__(self):
        """
        Initialization
        """

    def dijkstra(self, graph, start, end=None, usedByYenKSP=False, car_speed=0):
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

            # graph.out_nbrs(v): Return a list of all nodes connected by outgoing edges.
            for w in graph.out_nbrs(v):
                edge_id = graph.edge_by_node(v, w)
                # edge_weight = road_length/speed_limit/channel_number
                # max_speed = min(car_speed, graph.edge_data(edge_id)[2])
                # vwLength = D[v] + graph.edge_data(edge_id)[1] / max_speed / graph.edge_data(edge_id)[3]
                # vwLength = D[v] + graph.edge_data(edge_id)[1] / graph.edge_data(edge_id)[2] / graph.edge_data(edge_id)[3]
                vwLength = D[v] + graph.edge_data(edge_id)[1] /graph.edge_data(edge_id)[3]

                # vwLength = D[v] + graph.edge_data(edge_id)
                if w in D:
                    if vwLength < D[w]:
                        raise GraphError(
                            "Dijkstra: found better path to already-final vertex")
                elif w not in Q or vwLength < Q[w]:
                    Q[w] = vwLength
                    P[w] = v


        if usedByYenKSP:
            if end:
                if end not in graph.forw_bfs(start):  # can not reach end_node from start_node
                    return {'cost': D[start],
                            'path': []}
                return {'cost': D[end],
                        'path': self.path(P, start, end)}
            else:
                return (D, P)
        else:
            return (D, P)


    def shortest_path(self, graph, start, end, car_speed=0):
        """
        Find a single shortest path from the *start* node to the *end* node.
        The input has the same conventions as dijkstra(). The output is a list of
        the nodes in order along the shortest path.

        **Note that the distances must be stored in the edge data as numeric data**
        """

        D, P = self.dijkstra(graph, start, end, False, car_speed)
        Path = []
        if end not in P:
            return
        while 1:
            Path.append(end)
            # if end not in P:
            #     break
            if end == start:
                break
            end = P[end]
        Path.reverse()
        return Path

    ## Computes K paths from a source to a sink.
    #
    # @param graph A digraph of class Graph.
    # @param start The source node of the graph.
    # @param sink The sink node of the graph.
    # @param K The amount of paths being computed.
    #
    # @retval [] Array of paths, where [0] is the shortest, [1] is the next
    # shortest, and so on.
    #
    def ksp_yen(self, graph, node_start, node_end, max_k=2, car_speed=0):
        if node_end not in graph.forw_bfs(node_start):  # can not reach end_node from start_node
            return
        distances, previous = self.dijkstra(graph, node_start, None, True, car_speed)

        A = [{'cost': distances[node_end],
              'path': self.path(previous, node_start, node_end)}]
        B = []

        if not A[0]['path']:
            return A

        for k in range(1, max_k):
            for i in range(0, len(A[-1]['path']) - 1):
                node_spur = A[-1]['path'][i]
                path_root = A[-1]['path'][:i + 1]

                edges_removed = []
                for path_k in A:
                    curr_path = path_k['path']
                    if len(curr_path) > i and path_root == curr_path[:i + 1]:
                        # cost = graph.remove_edge(curr_path[i], curr_path[i + 1])
                        hidden_edge_id = graph.edge_by_node(curr_path[i], curr_path[i+1])
                        if hidden_edge_id == None:
                            continue
                        # cost = -1
                        cost = graph.edge_data(hidden_edge_id)
                        graph.hide_edge(hidden_edge_id)
                        # if cost == -1:
                        #     continue
                        edges_removed.append([curr_path[i], curr_path[i + 1], cost])

                path_spur = self.dijkstra(graph, node_spur, node_end, True, car_speed)

                if path_spur['path']:
                    path_total = path_root[:-1] + path_spur['path']
                    dist_total = distances[node_spur] + path_spur['cost']
                    potential_k = {'cost': dist_total, 'path': path_total}

                    if not (potential_k in B):
                        B.append(potential_k)

                # for edge in edges_removed:
                #     # graph.add_edge(edge[0], edge[1], edge[2])
                #     hidden_edge_id = graph.edge_by_node(edge[0], edge[1])
                #     graph.restore_edge(hidden_edge_id)
                graph.restore_all_edges()

            if len(B):
                B = sorted(B, key=itemgetter('cost'))
                A.append(B[0])
                B.pop(0)
            else:
                break

        return A

    ## Finds a paths from a source to a sink using a supplied previous node list.
    #
    # @param previous A list of node predecessors.
    # @param node_start The source node of the graph.
    # @param node_end The sink node of the graph.
    #
    # @retval [] Array of nodes if a path is found, an empty list if no path is
    # found from the source to sink.
    #
    def path(self, previous, node_start, node_end):
        route = []

        node_curr = node_end
        while True:
            route.append(node_curr)
            if previous[node_curr] == node_start:
                route.append(node_start)
                break
            elif previous[node_curr] == None:
                return []

            node_curr = previous[node_curr]

        route.reverse()
        return route

    # generate a simple path from start to end using Depth First Search
    def simple_path(self, graph, start, end=None):
        visited, stack = set([start]), deque([start])
        while stack:
            # pop the last but not remove
            curr_node = stack[-1]
            visited.add(curr_node)
            if curr_node == end:
                break
            isLeafNode = True
            out_edges = graph.out_edges(curr_node)
            random.shuffle(out_edges)
            if out_edges:
                for edge in out_edges:
                    tail = graph.tail(edge)
                    if tail not in visited:
                        stack.append(tail)
                        isLeafNode = False
                        break
            if isLeafNode is True:
                stack.pop()
        simple_path = []
        for i in range(stack.__len__()):
            simple_path.append(stack[i])
        return simple_path

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