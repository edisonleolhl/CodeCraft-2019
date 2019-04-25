from Algorithms import Algorithms
import sys
from altgraph.Graph import Graph
import numpy as np
import random
from altgraph import GraphError
from NodeadlockScheduler import *


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

def main():
    # -------------------------------test altgraph module and dijkstra algorithm ---------------------------
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
    # # print(graph.out_edges(2))
    # print(graph.out_nbrs(3))
    # graph.hide_edge(6)
    # # print(graph.get_hops(4,5))
    # # print(graph.get_hops(1,4))
    # # print(graph.forw_bfs(4))
    # # print(graph.out_degree(1))
    # # print(graph.tail(1))
    # print('dijkstra shortest path is ' + str(algo.shortest_path(graph, 3, 4)))
    # graph.restore_edge(6)
    # print(graph.out_nbrs(3))
    # print('dijkstra shortest path is ' + str(algo.shortest_path(graph, 3, 4)))
    # for node in graph.iterdfs(1, 4):
    #     print(node)
    # print(algo.ksp_yen(graph, 1, 4, 4))
    # print(algo.simple_path(graph, 3, 1))
    # print(searchRoute(graph))
    # -------------------------------test altgraph module and dijkstra algorithm ---------------------------

    # -------------------------------get map basic information ---------------------------
    # car_path = sys.argv[1]
    # road_path = sys.argv[2]
    # cross_path = sys.argv[3]
    # preset_answer_path = sys.argv[4]
    # answer_path = sys.argv[5]
    # #
    # car_list, road_list, cross_list, preset_answer_list= readFiles(car_path, road_path, cross_path, preset_answer_path)
    # car_list = replaceDepartTimeForPresetCar(car_list, preset_answer_list)
    #
    # preset = [x for x in car_list if x[6] == 1]
    # priority_preset = [x for x in car_list if x[5] == 1 and x[6] == 1]
    # pp100 = priority_preset[:100]
    # preset_answer_list100 = preset_answer_list[0:100]
    # non_priority_preset = [x for x in car_list if x[5] == 0 and x[6] == 1]
    # priority_non_preset = [x for x in car_list if x[5] == 1 and x[6] == 0]
    # non_priority_non_preset = [x for x in car_list if x[5] == 0 and x[6] == 0]
    # priority_preset = sorted(priority_preset, key=lambda x: x[4])
    # # for item in priority_preset:
    # #     print(item)
    # print('priority_preset last depart: %s'%priority_preset[-1][4])
    # print('priority_preset number: %s'%priority_preset.__len__())
    # print('priority_non_preset number: %s'%priority_non_preset.__len__())
    # print('non_priority_preset number: %s'%non_priority_preset.__len__())
    # print('non_priority_non_preset number: %s'%non_priority_non_preset.__len__())
    # # pp = np.array(priority_preset)
    # # print(pp)
    #
    # carInfo = open(car_path,  'r').read().split('\n')[1:] # [(61838, 1716, 800, 4, 72, 0, 0), ...]
    # roadInfo = open(road_path, 'r').read().split('\n')[1:]
    # crossInfo = open(cross_path, 'r').read().split('\n')[1:]
    # answer_info = open(answer_path, 'r').read().split('\n')[:] # note that answer file doesn't have comment line
    # preset_answer_info = generatePresetAnswer(preset_answer_path)
    # scheduler = NodeadlockScheduler(carInfo, roadInfo, crossInfo, answer_info, preset_answer_info)
    # time, new_answer_info = scheduler.schedule()
    # print('Current schedule time: %d' %time)
    # -------------------------------get map basic information ---------------------------



    # -------------------------------How to decide departure rate and acc departure rate ---------------------------
    loop = 4
    JudgeTime_list = [999999 for x in range(loop)]
    answer_info_list = [None for x in range(loop)]
    garanteeFlag = False
    last_deadlock = True
    step = 10
    departure_rate = 54
    acc_departure_rate = 58
    print('departure rate=%s, acc departure rate=%s'%(departure_rate, acc_departure_rate))
    for i in range(loop):
        if garanteeFlag is False:
            print('start scheduling')
            # isDeadLock, JudgeTime = (True, None) if random.random() > 0.5 else (False, random.random()*1000)
            isDeadLock, JudgeTime = (True, None) if (departure_rate > 48 or acc_departure_rate > 52) else (False, 10000 / departure_rate)
            # isDeadLock, JudgeTime = True, None
            print('current JudgeTime: %s, isDeadLock: %s\n'%(JudgeTime, isDeadLock))
        else:
            # last time, the depart rate is very slow, don't schedule to save time
            JudgeTime_list[i] = 1
            answer_info_list[i] = (departure_rate, acc_departure_rate)
            break
        if isDeadLock:
            if last_deadlock:
                if i != 0 and answer_info_list.count(None) == loop: # previous scheduling are all deadlock
                    step = step * 2
                    print('sequent deadlock, double step, current step: %s' % step)
                elif i == 2 and answer_info_list.count(None) != loop:
                    step = step // 2
                departure_rate -= step
                acc_departure_rate -= step
                print('depart rate - step=%s, now departure rate=%s, acc departure rate=%s'%(step,departure_rate, acc_departure_rate))

            else:
                step = step // 2
                departure_rate -= step
                acc_departure_rate -= step
                print('last time ok, this time deadlock, step half to -%s, now departure rate=%s, acc departure rate=%s'%(step,departure_rate, acc_departure_rate))
            last_deadlock = True
        else:
            JudgeTime_list[i] = JudgeTime
            answer_info_list[i] = (departure_rate, acc_departure_rate)
            if last_deadlock:
                if i == 0:
                    # first time is ok, then try a big departure rate to reduce running time and to get a deadlock(so that optimal is between first schedule and second schedule
                    step = step * 2
                    departure_rate += step
                    acc_departure_rate += step
                    print('first time ok, try big, +step=%s, departure rate=%s, acc departure rate=%s'%(step, departure_rate, acc_departure_rate))
                else:
                    step = step // 2
                    departure_rate += step
                    acc_departure_rate += step
                    print('last time (true) deadlock, this time ok, step half to +%s, now departure rate=%s, acc departure rate=%s' % (
                    step, departure_rate, acc_departure_rate))
            last_deadlock = False
        if i == loop - 3 and answer_info_list.count(None) == 2:
            print('runs ok 2 times in first %s time, skip the last schedule' % (loop - 2))
            break
        if i == loop - 2:
            if answer_info_list == [None for x in range(loop)]:
                # garantee the last calculation have a feasible solution
                departure_rate = 20
                acc_departure_rate = 25
                garanteeFlag = True  # don't have to call scheduler program
                print('deadlock for first %s time, skip the last schedule'%(loop-1))
            elif answer_info_list.count(None) <= 2:
                # no running time for the last scheduling, get the current optimal answer info
                print('runs ok 2 times in first %s time, skip the last schedule'%(loop-1))
                break
    i = JudgeTime_list.index(min(JudgeTime_list))
    print('optimal index: %s'%i)
    print('optimal depart rate: %s,%s'%answer_info_list[i])
    # -------------------------------How to decide departure rate and acc departure rate ---------------------------

if __name__ == "__main__":
    main()