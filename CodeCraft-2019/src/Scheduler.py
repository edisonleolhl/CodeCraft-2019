# -*- encoding=utf8 -*-
import sys
import numpy as np
import cv2 as cv

np.random.seed(951105)

# 'list' object in Python is global, therefore use a single element list to record time
TIME = [0]
allScheduleTime = [0]
priScheduleTime = [0]
allPriScheduleTime = [0]

remainingPriCnt = [0, 1] # second element '1' means continue counting, '0' means finish counting
speedParams = [0, 100, 0, 100] # highest speed, lowest speed, highest speed of pri, lowest speed of pri
planTimeParams = [0, 10000000, 0, 10000000] # latest, earliest, latest of pri, earliest of pri
diffSrc = [{}, {}] # allCarDict, priCarDict, the key of dict is cross_id, key is unique in dict
diffDst = [{}, {}] # allCarDict, priCarDict
factor = [0, 0]

priority_car_list = []
car_distribution = [0, 0, 0]
car_id_list, road_id_list, cross_id_list = [], [], []
cross_dict, car_dict, road_dict = {}, {}, {}


class Car(object):
    def __init__(self, id, from_, to, speed, planTime, priority, preset):
        self.id, self.from_, self.to, self.speed, self.planTime, self.priority, self.preset = \
            id, from_, to, speed, planTime, priority, preset
        self.depart_time = None
        self.carColor = [int(value) for value in np.random.random_integers(0, 255, [3])]  # lhl: only for visualization
        self.state = 0  # lhl: state 0-ingarage, 1-wait, 2-end, 3-finishtrip,
        self.x, self.y = 0, 0  # x is the position of the channel, y is the number of channel
        self.presentRoad, self.nextCrossId = None, self.from_
        self.route, self.routeIndex = None, None

    def scheduleInit(self, depart_time, route):
        self.depart_time, self.route, self.routeIndex = depart_time, route, 0

    def update(self, state, x=None, y=None, presentRoad=None, nextCrossId=None):
        # car not in garage of car is ready to go
        if self.state != 0 or presentRoad is not None:
            self.state = state
        if presentRoad is not None and self.state != 0 and self.routeIndex < self.route.__len__():
            self.routeIndex += 1
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.presentRoad = presentRoad if presentRoad is not None else self.presentRoad
        self.nextCrossId = nextCrossId if nextCrossId is not None else self.nextCrossId

    def nextRoad(self):
        try:
            return self.route[self.routeIndex]
        except:
            return -1


class Road(object):
    def __init__(self, id, length, speed, channel, from_, to, isDuplex):
        self.id, self.length, self.speed, self.channel, self.from_, self.to, self.isDuplex = \
            id, length, speed, channel, from_, to, isDuplex
        # absolute bucket
        self.forwardBucket = {i: [None for j in range(self.channel)] for i in range(self.length)}
        self.backwardBucket = {i: [None for j in range(self.channel)] for i in
                               range(self.length)} if self.isDuplex else None
        self.fx, self.fy, self.bx, self.by, self.forwardNum, self.backwardNum = 0, 0, 0, 0, 0, 0
        # relative bucket
        self.provideBucket, self.receiveBucket = None, None
        self.px, self.py, self.provideNum, self.receiveNum = None, None, None, None

    def setBucket(self, crossId):
        if crossId == self.to:
            self.provideBucket, self.px, self.py, self.provideNum = \
                self.forwardBucket, self.fx, self.fy, self.forwardNum
            if self.isDuplex:
                self.receiveBucket, self.receiveNum = \
                    self.backwardBucket, self.backwardNum
            else:
                self.receiveBucket, self.receiveNum = None, None
        elif crossId == self.from_:
            self.receiveBucket, self.receiveNum = \
                self.forwardBucket, self.forwardNum
            if self.isDuplex:
                self.provideBucket, self.px, self.py, self.provideNum = \
                    self.backwardBucket, self.bx, self.by, self.backwardNum
            else:
                self.provideBucket, self.px, self.py, self.provideDone, self.provideNum = \
                    None, None, None, None, None
        else:
            print("Road:%s is not connected CrossId:%s " % (self.id, crossId))

    def stepInit(self):
        self.fx, self.fy, self.bx, self.by = 0, 0, 0, 0
        self.provideBucket, self.receiveBucket = None, None
        self.px, self.py, self.provideNum, self.receiveNum = None, None, None, None
        # car state initialization
        for i in range(self.length):
            for j in range(self.channel):
                if self.forwardBucket[i][j] is not None:
                    car = car_dict[self.forwardBucket[i][j]]
                    car.update(state=1)
                if self.isDuplex:
                    if self.backwardBucket[i][j] is not None:
                        car = car_dict[self.backwardBucket[i][j]]
                        car.update(state=1)
        # first step
        for channel in range(self.channel):
            self.moveInChannel(self.forwardBucket, channel)
            if self.isDuplex:
                self.moveInChannel(self.backwardBucket, channel)

    #
    # function for bucket action
    #
    def moveInChannel(self, bucket, channel):
        # car state: 0, 1, 2, 3 in garage, wait, end, finish trip
        # 'previousCar' indicates the index of the previous car in current channel
        # 'previousState' indicates the state of the previous car in current channel
        previousCar, previousState = -1, 1
        for i in range(self.length):
            if bucket[i][channel] is not None:
                car = car_dict[bucket[i][channel]]
                v = min(car.speed, self.speed)
                if car.state == 2:
                    previousCar, previousState = i, 2
                    continue
                # current car is not blocked by previousCar, so move it to the destination grid
                # then update bucket and car state
                elif i - v > previousCar:
                    car.update(state=2, x=(i - v))
                    bucket[i - v][channel] = bucket[i][channel]
                    bucket[i][channel] = None
                    previousCar, previousState = i - v, 2
                # previousCar is 'end' state, move current car to the grid just behind the previousCar
                elif previousState == 2:
                    if previousCar + 1 != i:
                        bucket[previousCar + 1][channel] = bucket[i][channel]
                        bucket[i][channel] = None
                    car.update(state=2, x=(previousCar + 1))
                    previousCar, previousState = previousCar + 1, 2
                # current car is 'wait' state
                else:
                    previousCar, previousState = i, 1

    #
    # Road function: current road provide the cross with first priority car
    #
    def findFirstPriorityCar(self):
        if self.provideBucket is None:
            print("Please do Car.setBucket() first!")
        self.px, self.py = 0, 0 # if delete, then dead lock, don't konw why
        # find priority cars
        for x in range(self.length):
            for y in range(self.channel):
                carId = self.provideBucket[x][y]
                if carId is not None and car_dict[carId].state != 2 and car_dict[carId].priority == 1:
                    car = car_dict[carId]
                    left = min(car.speed, self.speed)
                    # check current priority car's speed whether it is enough to cross
                    if left > x:
                        # check if there is front non-priority car
                        hasFrontCar = False
                        for frontX in range(x - 1, -1, -1):
                            if self.provideBucket[frontX][y] is not None:
                                hasFrontCar = True
                                break
                        if not hasFrontCar:
                            self.px, self.py = x, y
                            return self.provideBucket[x][y]

        while self.px < self.length:
            carId = self.provideBucket[self.px][self.py]
            if carId is not None and car_dict[carId].state != 2:
                car = car_dict[carId]
                left = min(car.speed, self.speed)
                # current car's speed is enough and there are no cars in front of it
                if left > self.px:
                    return self.provideBucket[self.px][self.py]

            # current channel has the lowest priority channel, switch to the next highest priority channel
            if self.py == self.channel - 1:
                self.px, self.py = self.px + 1, 0
            # switch to the channel with higher priority
            else:
                self.py += 1

        return -1

    #
    # Road function: current road determine first priority car's action
    #
    def setFirstPriorityCarAction(self, action):
        if self.provideBucket is None:
            print("Please do Car.setBucket() first!")
        # move first priority car across the cross or get the destination cross
        if action == 'go':
            self.provideBucket[self.px][self.py] = None
            self.provideNum -= 1
        # move first priority car to the front grid in the channel
        elif action == 'move':
            carId = self.provideBucket[self.px][self.py]
            self.provideBucket[self.px][self.py] = None
            self.provideBucket[0][self.py] = carId
        # after schedule first priority car, schedule current channel
        self.moveInChannel(self.provideBucket, self.py)

    #
    # Road function: current road receive car
    #
    def receiveCar(self, carId):
        if self.receiveBucket is None:
            print("Please do Car.setBucket() first!")
        car = car_dict[carId]
        leftX = min(self.speed, car.speed) - car.x
        nextCrossId = self.from_ if car.nextCrossId != self.from_ else self.to
        # car cannot move across the cross
        if leftX <= 0:
            car.update(state=2, x=0)
            return 'move'
        # find front car
        for channel in range(self.channel):
            frontCarLoc = -1
            for index in range(self.length - 1, self.length - leftX - 1, -1):
                if self.receiveBucket[index][channel] is not None:
                    frontCarLoc = index
                    break
            # if no front car
            if frontCarLoc == -1:
                self.receiveBucket[self.length - leftX][channel] = carId
                self.receiveNum += 1
                car.update(state=2, x=self.length - leftX, y=channel, presentRoad=self.id,
                                  nextCrossId=nextCrossId)
                return 'go'
            frontCar = car_dict[self.receiveBucket[frontCarLoc][channel]]
            # if frontCar.state == wait
            if frontCar.state == 1:
                return 'wait'
            # frontCar.state == end
            elif frontCarLoc != self.length - 1:
                self.receiveBucket[frontCarLoc + 1][channel] = carId
                self.receiveNum += 1
                car.update(state=2, x=frontCarLoc + 1, y=channel, presentRoad=self.id,
                                  nextCrossId=nextCrossId)
                return 'go'
            # frontCar.state == end and frontCar.x == road.length-1
            else:
                # this channel is full, try next channel
                continue
        # all channels are full, current road cannot receive car
        car.update(state=2, x=0)
        return 'move'


class Cross(object):
    def __init__(self, id, north, east, south, west):
        # **** statistic parameters ****#
        self.id = id
        self.direction_list = [north, east, south, west]
        self.garage = {}
        self.left = []
        # absolute loc
        self.x, self.y = 0, 0
        self.mapX, self.mapY = 0, 0
        # priorityMap
        self.directionMap = {north: {east: 1, south: 2, west: -1}, \
                             east: {south: 1, west: 2, north: -1}, \
                             south: {west: 1, north: 2, east: -1}, \
                             west: {north: 1, east: 2, south: -1}}
        # relationship with roads
        self.providerDirection, self.receiverDirection, self.validRoadDirecction = [], [], []
        for index, roadId in enumerate(self.direction_list):
            if roadId != -1:
                self.validRoadDirecction.append(index)
                road = road_dict[roadId]
                if road.isDuplex:
                    self.providerDirection.append(index)
                    self.receiverDirection.append(index)
                else:
                    if road.to == self.id:
                        self.providerDirection.append(index)
                    # if road.from_ == self.id
                    else:
                        self.receiverDirection.append(index)
        self.provider = [[direction, self.direction_list[direction]] for direction in self.providerDirection]
        self.receiver = [self.direction_list[direction] for direction in self.receiverDirection]
        self.validRoad = [self.direction_list[direction] for direction in self.validRoadDirecction]
        self.provider.sort(key=lambda x: x[1])
        self.providerDirection = [self.provider[i][0] for i in range(self.provider.__len__())]
        self.provider = [self.provider[i][1] for i in range(self.provider.__len__())]
        self.readyCars = []
        self.leftCars = []
        self.readyPriCars = []
        self.nonPriCars = []
        self.garageCarNum = 0
        self.finishCarNum = 0
        self.done = False
        self.update = False

    # main functions
    def step(self):
        self.update = False
        for roadId in self.validRoad:
            road_dict[roadId].setBucket(self.id)
        # data prepare
        next_car_id_list, next_car_list, next_road_list, nextDirection = [], [], [], []
        #
        # 0,1,2,3 denote north,east,south,west
        #
        for index in range(self.provider.__len__()):
            next_car_id = road_dict[self.provider[index]].findFirstPriorityCar()
            next_car_id_list.append(next_car_id)
            # if first priority car exists
            if next_car_id != -1:
                next_car = car_dict[next_car_id]
                next_car_list.append(next_car)
                next_road = next_car.nextRoad()
                next_road_list.append(next_road)
                # next_road == -1 => destination
                if next_road == -1:
                    nextDirection.append(2)
                else:
                    nextDirection.append(self.direction(self.provider[index], next_road))
            else:
                next_car_list.append(-1)
                next_road_list.append(-1)
                nextDirection.append(-1)
        # loop
        for presentRoadIndex in range(self.provider.__len__()):
            conflict = False
            while next_car_list[presentRoadIndex] != -1:
                present_car = next_car_list[presentRoadIndex]
                in_road = road_dict[self.provider[presentRoadIndex]]

                for otherRoadIndex in range(self.provider.__len__()):
                    other_car = next_car_list[otherRoadIndex]
                    if other_car != -1 and next_road_list[presentRoadIndex] == next_road_list[otherRoadIndex]:
                        # present pri, other pri, go_straight > turn_left > turn_right
                        if present_car.priority == 1:
                            if other_car.priority == 1:
                                if nextDirection[presentRoadIndex] < nextDirection[otherRoadIndex]:
                                    conflict = True
                                    break
                        # present non-pri, other pri, lead to confict
                        elif other_car.priority == 1:
                            conflict = True
                            break
                        # present non-pri, other non-pri, go_straight > turn_left > turn_right
                        else:
                            if nextDirection[presentRoadIndex] < nextDirection[otherRoadIndex]:
                                conflict = True
                                break
                if conflict:
                    break
                # present car get to the destination
                if next_road_list[presentRoadIndex] == -1:
                    present_car.update(state=3)
                    in_road.setFirstPriorityCarAction('go')
                    car_distribution[1] -= 1
                    car_distribution[2] += 1
                    self.finishCarNum += 1
                    self.update = True
                    allScheduleTime[0] += TIME[0] - present_car.planTime
                    if present_car.priority == 1:
                        allPriScheduleTime[0] += TIME[0] - present_car.planTime
                        remainingPriCnt[0] -= 1
                        if remainingPriCnt[1] and remainingPriCnt[0] == 0:
                            priScheduleTime[0] = TIME[0] - planTimeParams[3]
                            remainingPriCnt[1] = 0

                # move present car to next road
                else:
                    next_road = road_dict[next_road_list[presentRoadIndex]]
                    action = next_road.receiveCar(present_car.id)
                    if action == 'wait':
                        # waiting conflict
                        break
                    self.update = True
                    in_road.setFirstPriorityCarAction(action)

                next_car = in_road.findFirstPriorityCar()
                # present road still has a cars to schedule, put it in the next_car_list
                if next_car != -1:
                    next_car_list[presentRoadIndex] = car_dict[next_car]
                    next_road_list[presentRoadIndex] = car_dict[next_car].nextRoad()
                    # next_road == -1 => terminal
                    if next_road_list[presentRoadIndex] == -1:
                        nextDirection[presentRoadIndex] = 2
                    else:
                        nextDirection[presentRoadIndex] = self.direction(self.provider[presentRoadIndex],
                                                                         next_road_list[presentRoadIndex])
                # present road doesn't have a car to schedule
                else:
                    next_car_list[presentRoadIndex] = -1
                    next_road_list[presentRoadIndex] = -1
                    nextDirection[presentRoadIndex] = -1
        done = True
        for fromA in range(self.provider.__len__()):
            if next_car_list[fromA] != -1:
                done = False
        self.done = done

    def driveCarInGarage(self):
        # leftCars are all from the drivePriCarInGarage
        self.readyCars = self.leftCars
        self.leftCars = []
        if self.readyCars.__len__() == 0:
            return
        self.readyPriCars = list(set(self.readyPriCars))
        self.readyCars.sort()
        for road_id in self.receiver:
            road_dict[road_id].setBucket(self.id)
        for i in range(self.readyCars.__len__()):
            depart_time = self.readyCars[i][0]
            car_id = self.readyCars[i][1]
            road_id = car_dict[car_id].nextRoad()
            road = road_dict[road_id]
            action = road.receiveCar(car_id)
            if action != 'go':
                # connot drive present car out of garage, so append it to the 'leftCars' list
                self.leftCars.append((depart_time, car_id))
            else:
                # on the go!
                # self.garage[depart_time].remove(car_id)
                self.garageCarNum -= 1
                car_distribution[0] -= 1
                car_distribution[1] += 1
                # print("Car(%d) out of cross(%d) to Road(%d) --function:class.driveCarInGarage" % (car_id, self.id, road_id))

    def drivePriCarInGarage(self):
        # leftCars include delayed cars
        self.readyPriCars = []
        self.nonPriCars = []
        for (depart_time, car_id) in self.leftCars:
            if car_dict[car_id].priority == 1:
                self.readyPriCars.append((depart_time, car_id))
            else:
                self.nonPriCars.append(((depart_time, car_id)))
        if TIME[0] in self.garage.keys():
            for car_id in self.garage[TIME[0]]:
                depart_time = TIME[0]
                if car_dict[car_id].priority == 1:
                    if (depart_time, car_id) not in self.readyCars:
                        self.readyPriCars.append((depart_time, car_id))
                else:
                    if (depart_time, car_id) not in self.nonPriCars:
                        self.nonPriCars.append(((depart_time, car_id)))
        self.leftCars = self.nonPriCars
        if self.readyPriCars.__len__() == 0:
            return
        self.readyPriCars = list(set(self.readyPriCars))
        # first sort depart_time ascending, then sort car_id ascending
        self.readyPriCars.sort()
        for road_id in self.receiver:
            road_dict[road_id].setBucket(self.id)
        for i in range(self.readyPriCars.__len__()):
            depart_time = self.readyPriCars[i][0]
            car_id = self.readyPriCars[i][1]
            road_id = car_dict[car_id].nextRoad()
            road = road_dict[road_id]
            action = road.receiveCar(car_id)
            if action != 'go':
                # connot drive present car out of garage, so append it to the 'leftCars' list
                self.leftCars.append((depart_time, car_id))
            else:
                # on the go!
                self.garage[depart_time].remove(car_id)
                self.garageCarNum -= 1
                car_distribution[0] -= 1
                car_distribution[1] += 1

    def garageInit(self, depart_time, carId):
        if depart_time not in self.garage.keys():
            self.garage[depart_time] = [carId]
        else:
            self.garage[depart_time].append(carId)
        self.garageCarNum += 1

    def direction(self, providerId, receiverId):
        return self.directionMap[providerId][receiverId]

    def setLoc(self, x, y):
        self.x, self.y = x, y

    def setMapLoc(self, mapX, mapY):
        self.mapX, self.mapY = mapX, mapY

    def roadDirection(self, roadId):
        if self.direction_list[0] == roadId:
            return 0
        elif self.direction_list[1] == roadId:
            return 1
        elif self.direction_list[2] == roadId:
            return 2
        elif self.direction_list[3] == roadId:
            return 3
        else:
            return -1

    def __loc__(self):
        return self.x, self.y

    def __mapLoc__(self):
        return self.mapX, self.mapY


class Scheduler(object):
    def __init__(self):
        self.dead = False

    def step(self):
        if TIME[0] % 200 == 0:
            print("- time:%d, allScheduleTime:%d, priScheduleTime:%d, allPriScheduleTime:%d" % (
                TIME[0], allScheduleTime[0], priScheduleTime[0], allPriScheduleTime[0]))
            print("--- cars in garage: %d, on the road: %d, finish trip: %d" % (
                car_distribution[0], car_distribution[1], car_distribution[2]))
        for crossId in cross_id_list:
            cross_dict[crossId].done = False
        # print("pre-movement...")
        for road in road_id_list:
            road_dict[road].stepInit()
        # print("while loop...")
        unfinishedCross = cross_id_list
        while unfinishedCross.__len__() > 0:
            self.dead = True
            nextCross = []
            for crossId in unfinishedCross:
                for roadId in cross_dict[crossId].validRoad:
                    road_dict[roadId].setBucket(crossId)
                cross_dict[crossId].drivePriCarInGarage()
                cross = cross_dict[crossId]
                cross.step()
                if not cross.done:
                    nextCross.append(crossId)
                if cross.update or cross.done:
                    self.dead = False
            unfinishedCross = nextCross
            assert self.dead is False, print("dead lock in", unfinishedCross)
        for i in range(cross_id_list.__len__()):
            crossId = cross_id_list[i]
            for roadId in cross_dict[crossId].validRoad:
                road_dict[roadId].setBucket(crossId)
            cross_dict[crossId].driveCarInGarage()

    def schedule(self):
        visualize = visualization()
        visualize.crossLocGen()
        while True:
            self.step()
            # visualize.drawMap()
            if car_distribution[2] == car_id_list.__len__():
                print('%d cars have been scheduled' % car_distribution[2])
                print('priScheduleTime: %d, allPriScheduleTime: %d' % (priScheduleTime[0], allPriScheduleTime[0]))
                print('schedule time: %d, allScheduleTime: %d' % (TIME[0], allScheduleTime[0]))
                JudgeTime = factor[0]*priScheduleTime[0] + TIME[0]
                JudgeTotalTime = factor[1]*allPriScheduleTime[0] + allScheduleTime[0]
                print('JudgeTime: %d, JudgeTotalTime: %d' % (JudgeTime, JudgeTotalTime))

                break
            if self.dead:
                break
            TIME[0] += 1


class visualization(object):
    def __init__(self):
        self.maxX, self.maxY = 0, 0
        self.savePath = 'training2'
        # ** cross param **#
        self.crossRadius = 14
        self.crossDistance = 150
        self.crossColor = [25, 200, 0]
        # ** road param **#
        self.roadColor = [0, 0, 0]  # black
        self.roadLineType = 4
        self.channelWidth = 5
        self.channelDistance = 3
        self.lineWidth = 2
        self.time = 0

    #
    # cross location gen
    #
    def crossLocGen(self):
        # **** relative location ****#
        # denote the first cross as the origin of coordinates
        for crossId in cross_id_list:
            cross_dict[crossId].done = False
        crossList = [cross_id_list[0]]
        minX, minY = 0, 0
        while (crossList.__len__() > 0):
            nextCrossList = []
            for crossId in crossList:
                presentX, presntY = cross_dict[crossId].__loc__()
                validRoad = cross_dict[crossId].validRoad
                for roadId in validRoad:
                    # next cross id
                    nextCrossId = road_dict[roadId].from_ if road_dict[roadId].from_ != crossId \
                        else road_dict[roadId].to
                    # if next cross is visited
                    if not cross_dict[nextCrossId].done:
                        # visit sets true
                        cross_dict[nextCrossId].done = True
                        # relative location of nextcross
                        nextX, nextY = self.crossRelativeLoc(presentX, presntY, crossId, roadId)
                        # update location
                        cross_dict[nextCrossId].setLoc(nextX, nextY)
                        minX, minY, self.maxX, self.maxY = \
                            min(nextX, minX), min(nextY, minY), max(nextX, self.maxX), max(nextY, self.maxY)
                        nextCrossList.append(nextCrossId)
            crossList = nextCrossList
        self.maxX, self.maxY = (self.maxX - minX + 2) * self.crossDistance, (self.maxY - minY + 2) * self.crossDistance
        for crossId in cross_id_list:
            x, y = cross_dict[crossId].__loc__()
            cross_dict[crossId].setLoc(x - minX, y - minY)
            cross_dict[crossId].setMapLoc((x - minX + 1) * self.crossDistance, (y - minY + 1) * self.crossDistance)

    def crossRelativeLoc(self, x, y, crossId, roadId):
        roadDirection = cross_dict[crossId].roadDirection(roadId)
        if roadDirection == 0:
            return x, y - 1
        elif roadDirection == 1:
            return x + 1, y
        elif roadDirection == 2:
            return x, y + 1
        elif roadDirection == 3:
            return x - 1, y
        else:
            print("Cross(%d) don't interact with road(%d)" % (self.id, roadId))

    #
    # draw functions
    #
    def drawMap(self):
        img = np.ones((self.maxY, self.maxX, 3), np.uint8) * 255
        # draw road
        for roadId in road_id_list:
            self.plotRoad(roadId, img)
        # draw cross
        for crossId in cross_id_list:
            self.plotCross(crossId, img)
        # plot info
        self.plotInfo(img)
        cv.imwrite(self.savePath + '/%d.jpg' % TIME[0], img)

    def plotCross(self, crossId, img):
        x, y = cross_dict[crossId].__mapLoc__()
        cv.circle(img, (x, y), self.crossRadius, color=self.crossColor, thickness=-1, lineType=-1)
        if crossId >= 10:
            xx, yy = int(x - 4 * self.crossRadius / 5), int(y + self.crossRadius / 2)
        else:
            xx, yy = int(x - self.crossRadius / 2), int(y + self.crossRadius / 2)
        cv.putText(img, str(crossId), (xx, yy), cv.FONT_HERSHEY_SIMPLEX, 0.6, [0, 0, 255], 2)

    def plotRoad(self, roadId, img):
        # get road info
        road = road_dict[roadId]
        fromX, fromY = cross_dict[road.from_].__mapLoc__()
        toX, toY = cross_dict[road.to].__mapLoc__()
        # plot line
        cv.line(img, (fromX, fromY), (toX, toY), color=self.roadColor, thickness=2)
        # plot bucket
        self.drawBucket(road, 'forward', img)
        if road.isDuplex:
            self.drawBucket(road, 'backward', img)

    def drawBucket(self, road, lane, img):
        bucket = road.forwardBucket if lane != 'backward' else road.backwardBucket
        length = road.length
        channel = road.channel
        fromX, fromY = cross_dict[road.from_].__mapLoc__()
        toX, toY = cross_dict[road.to].__mapLoc__()
        XY, intervalXY, rectangleSize, channel2XY, length2XY = self.bucketDrawInitial(fromX, fromY, toX, toY, lane,
                                                                                      length)
        for i in range(length):
            for j in range(channel):
                xRD, yRD = int(XY[0] + rectangleSize[0]), int(XY[1] + rectangleSize[1])
                if bucket[i][j] is None:
                    cv.rectangle(img, (int(XY[0]), int(XY[1])), (xRD, yRD), (0, 0, 0), 1)
                else:
                    color = car_dict[bucket[i][j]].carColor
                    cv.rectangle(img, (int(XY[0]), int(XY[1])), (xRD, yRD), color=color, thickness=-1)
                XY[channel2XY] = XY[channel2XY] + intervalXY[channel2XY]
            XY[channel2XY] = XY[channel2XY] - intervalXY[channel2XY] * channel
            XY[length2XY] = XY[length2XY] + intervalXY[length2XY]

    def bucketDrawInitial(self, fromX, fromY, toX, toY, lane, length):
        direction = self.bucketDirection(fromX, fromY, toX, toY, lane)
        unitLength = (self.crossDistance - self.crossRadius * 4) / length
        if lane == 'backward':
            toY = fromY
            toX = fromX
        if direction == 'north':
            XY = [fromX + self.channelDistance, toY + self.crossRadius * 2]
            intervalXY = self.channelDistance + self.channelWidth, unitLength
            rectangleSize = self.channelWidth, unitLength
            channel2XY, length2XY = 0, 1
        elif direction == 'south':
            XY = [fromX - self.channelDistance - self.channelWidth, toY - self.crossRadius * 2 - unitLength]
            intervalXY = -(self.channelDistance + self.channelWidth), -unitLength
            rectangleSize = self.channelWidth, unitLength
            channel2XY, length2XY = 0, 1
        elif direction == 'east':
            XY = [toX - self.crossRadius * 2 - unitLength, fromY + self.channelDistance]
            intervalXY = -unitLength, self.channelDistance + self.channelWidth
            rectangleSize = unitLength, self.channelWidth
            channel2XY, length2XY = 1, 0
        elif direction == 'west':
            XY = [toX + self.crossRadius * 2, fromY - self.channelDistance - self.channelWidth]
            intervalXY = unitLength, -(self.channelDistance + self.channelWidth)
            rectangleSize = unitLength, self.channelWidth
            channel2XY, length2XY = 1, 0
        return XY, intervalXY, rectangleSize, channel2XY, length2XY

    def bucketDirection(self, fromX, fromY, toX, toY, lane):
        if fromY > toY:
            direction = 'north' if lane == 'forward' else 'south'
        elif fromY < toY:
            direction = 'south' if lane == 'forward' else 'north'
        elif fromX < toX:
            direction = 'east' if lane == 'forward' else 'west'
        else:
            direction = 'west' if lane == 'forward' else 'east'
        return direction

    def plotInfo(self, img):
        for crossId in cross_id_list:
            cross = cross_dict[crossId]
            x, y = cross.__mapLoc__()
            cn, fn = cross.garageCarNum, cross.finishCarNum
            cv.putText(img, "%d,%d" % (cn, fn), (int(x), int(y - 1.1 * self.crossRadius)), \
                       cv.FONT_HERSHEY_SIMPLEX, 0.4, [0, 0, 255], 1)
        cv.putText(img, "in the garage:%d,on the road:%d,end of the trip:%d" % (
            car_distribution[0], car_distribution[1], car_distribution[2]), (30, 30), \
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, [0, 0, 255], 2)


def main():
    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    preset_answer_path = sys.argv[4]
    answer_path = sys.argv[5]

    carInfo = open(car_path, 'r').read().split('\n')[1:]
    roadInfo = open(road_path, 'r').read().split('\n')[1:]
    crossInfo = open(cross_path, 'r').read().split('\n')[1:]
    answerInfo = open(answer_path, 'r').read().split('\n')

    preset_answer_info = []
    with open(preset_answer_path, 'r') as preset_answer_file:
        for preset_answer in preset_answer_file.readlines():
            if preset_answer.startswith('#'):
                continue
            preset_answer = preset_answer.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
            preset_answer = [int(x) for x in preset_answer]
            preset_answer_info.append(preset_answer)

    for line in carInfo:
        id, from_, to, speed, planTime, priority, preset = line.replace(' ', '').replace('\t', '')[1:-1].split(',')
        # id, from_, to, speed, planTime = line.replace(' ', '').replace('\t', '')[1:-1].split(',')

        # presetOnly
        # if int(preset_) == 0:
        #     continue
        # presetOnly

        if int(priority) == 1:
            priority_car_list.append(id)
            remainingPriCnt[0] += 1
            speedParams[2] = max(speedParams[2], int(speed))
            speedParams[3] = min(speedParams[3], int(speed))
            planTimeParams[2] = max(planTimeParams[2], int(planTime))
            planTimeParams[3] = min(planTimeParams[3], int(planTime))
            diffSrc[1][to] = None
            diffDst[1][from_] = None

        speedParams[0] = max(speedParams[0], int(speed))
        speedParams[1] = min(speedParams[1], int(speed))

        planTimeParams[0] = max(planTimeParams[0], int(planTime))
        planTimeParams[1] = min(planTimeParams[1], int(planTime))

        diffSrc[0][to] = None
        diffDst[0][from_] = None


        car_id_list.append(int(id))
        car_dict[int(id)] = Car(int(id), int(from_), int(to), int(speed), int(planTime), int(priority), int(preset))

    print('speedParams: %s' % speedParams)
    print('planTimeParams: %s' % planTimeParams)
    print('allCarDiffSrc: %s, priDiffSrc: %s' % (diffSrc[0].__len__(), diffSrc[1].__len__()))
    print('allCarDiffDst: %s, priDiffDst: %s' % (diffDst[0].__len__(), diffDst[1].__len__()))

    factor[0] = 0.05*car_dict.__len__()/remainingPriCnt[0] + \
                0.2375*((speedParams[0]/speedParams[1])/(speedParams[2]/speedParams[3])) + \
                0.2375*((planTimeParams[0]/planTimeParams[1])/(planTimeParams[2]/planTimeParams[3])) + \
                0.2375*(diffSrc[0].__len__()/diffSrc[1].__len__()) + \
                0.2375*(diffDst[0].__len__()/diffDst[1].__len__())

    factor[1] = 0.8*car_dict.__len__()/remainingPriCnt[0] + \
                0.05*((speedParams[0]/speedParams[1])/(speedParams[2]/speedParams[3])) + \
                0.05*((planTimeParams[0]/planTimeParams[1])/(planTimeParams[2]/planTimeParams[3])) + \
                0.05*(diffSrc[0].__len__()/diffSrc[1].__len__()) + \
                0.05*(diffDst[0].__len__()/diffDst[1].__len__())

    print('factor a = %.5f, b= %.5f' % (factor[0], factor[1]))

    for line in roadInfo:
        id, length, speed, channel, from_, to, isDuplex = line.replace(' ', '').replace('\t', '')[1:-1].split(',')
        road_id_list.append(int(id))
        road_dict[int(id)] = Road(int(id), int(length), int(speed), int(channel), int(from_), int(to),
                                  int(isDuplex))
    visitDone = {}
    for line in crossInfo:
        id, north, east, south, west = line.replace(' ', '').replace('\t', '')[1:-1].split(',')
        cross_id_list.append(int(id))
        visitDone[int(id)] = False
        cross_dict[int(id)] = [int(north), int(east), int(south), int(west)]

    # DP and DFS adjust directions
    def DFS(crossId, direction=None, preCrossId=None):
        if visitDone[crossId]:
            return
        visitDone[crossId] = True
        if preCrossId is not None:
            for i in range(4):
                roadId = cross_dict[crossId][i]
                if roadId != -1:
                    pcId = road_dict[roadId].from_ if road_dict[roadId].from_ != crossId else road_dict[
                        roadId].to
                    if pcId == preCrossId:
                        break
            shift = ((i + 2) % 4 - direction) % 4
            for i in range(shift):
                cross_dict[crossId] = [cross_dict[crossId][1], cross_dict[crossId][2], cross_dict[crossId][3],
                                       cross_dict[crossId][0]]
        for i in range(4):
            roadId = cross_dict[crossId][i]
            if roadId != -1:
                nextCrossId = road_dict[roadId].from_ if road_dict[roadId].from_ != crossId else road_dict[roadId].to
                DFS(nextCrossId, i, crossId)

    DFS(cross_id_list[0])
    for crossId in cross_id_list:
        north, east, south, west = cross_dict[crossId]
        cross_dict[crossId] = Cross(crossId, north, east, south, west)
    count = 0

    # presetOnly
    for i, line in enumerate(answerInfo):
        if line.__len__() < 3:
            continue
        if line[0] == '#':
            continue
        line = line.strip()[1:-1].split(',')
        carId = int(line[0])
        depart_time = int(line[1])
        route = [int(roadId) for roadId in line[2:]]
        car_dict[carId].scheduleInit(depart_time, route)
        count += 1
    # presetOnly

    for i, line in enumerate(preset_answer_info):
        carId = line[0]
        depart_time = line[1]
        route = [roadId for roadId in line[2:]]
        car_dict[carId].scheduleInit(depart_time, route)
        count += 1
    car_distribution[0] = count
    print("There are %d cars' route preinstalled" % count)

    for carId in car_id_list:
        cross_dict[car_dict[carId].from_].garageInit(car_dict[carId].depart_time, carId)
    car_id_list.sort()
    cross_id_list.sort()
    schedule = Scheduler()
    schedule.schedule()


if __name__ == "__main__":
    main()
