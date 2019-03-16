import logging
import sys
import re
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
    car_list, road_list, cross_list = readFiles(car_path, road_path, cross_path)
    map = initMap(road_list, cross_list)

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
            cross_list.append(cross_line)

    # print(car_list)
    # print(road_list)
    # print(cross_list)
    return car_list, road_list, cross_list


# process
def initMap(road_list, cross_list):
    # init empty graph
    map = []
    for i in range(len(cross_list)):
        temp = []
        for j in range(len(cross_list)):
            temp.append('M')
        map.append(temp)

    for road in road_list:
        map[int(road[4])-1][int(road[5])-1] = (int(road[0]), int(road[1]), int(road[2]), int(road[3]))
        # duplex channel, indicating the correspnding reverse edge in adjacent matrix graph
        if road[-1] == '1':
            map[int(road[5]) - 1][int(road[4]) - 1] = (int(road[0]), int(road[1]), int(road[2]), int(road[3]))
    print(map)
    return map
# to write output file


if __name__ == "__main__":
    main()