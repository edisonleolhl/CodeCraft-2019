# -*- encoding=utf8 -*-
import sys
import numpy as np
import cv2 as cv

np.random.seed(951105)

# 'list' object in Python is global, therefore use a single element list to record TIME
TIME = [0]
car_distribution = [0, 0, 0]
car_id_list, road_id_list, cross_id_list = [], [], []
cross_dict, car_dict, road_dict = {}, {}, {}


class Car(object):
    def __init__(self, id, from_, to, speed, planTime):
        self.id, self.from_, self.to, self.speed, self.planTime = id, from_, to, speed, -1
        self.carColor = [int(value) for value in np.random.random_integers(0, 255, [3])]  # lhl: only for visualization
        self.state = 0  # lhl: state 0-ingarage, 1-wait, 2-end, 3-finishtrip,
        self.x, self.y = 0, 0  # x is the position of the channel, y is the number of channel
        self.presentRoad, self.nextCrossId = None, self.from_
        self.route, self.routeIndex = None, None

    def scheduleInit(self, planTime, route):
        self.planTime, self.route, self.routeIndex = planTime, route, 0

    def updateDynamic(self, state, x=None, y=None, presentRoad=None, nextCrossId=None):
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
            self.provideBucket, self.px, self.py,  self.provideNum = \
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
            print("Road:%s is not connected CrossId:%s " %(self.id, crossId))


    def stepInit(self):
        self.fx, self.fy, self.bx, self.by = 0, 0, 0, 0
        self.provideBucket, self.receiveBucket = None, None
        self.px, self.py, self.provideNum, self.receiveNum = None, None, None, None
        # car state initialization
        for i in range(self.length):
            for j in range(self.channel):
                if self.forwardBucket[i][j] is not None:
                    car = car_dict[self.forwardBucket[i][j]]
                    car.updateDynamic(state=1)
                if self.isDuplex:
                    if self.backwardBucket[i][j] is not None:
                        car = car_dict[self.backwardBucket[i][j]]
                        car.updateDynamic(state=1)
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
                    car.updateDynamic(state=2, x=(i - v))
                    bucket[i - v][channel] = bucket[i][channel]
                    bucket[i][channel] = None
                    previousCar, previousState = i - v, 2
                # previousCar is 'end' state, move current car to the grid just behind the previousCar
                elif previousState == 2:
                    if previousCar + 1 != i:
                        bucket[previousCar + 1][channel] = bucket[i][channel]
                        bucket[i][channel] = None
                    car.updateDynamic(state=2, x=(previousCar + 1))
                    previousCar, previousState = previousCar + 1, 2
                # current car is 'wait' state
                else:
                    previousCar, previousState = i, 1

    #
    # Road function: provide car for current road
    #
    def firstPriorityCar(self):
        if self.provideBucket is None:
            print("Please do Car.setBucket() first!")
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
    # Road function: determine first priority car's action
    #
    def firstPriorityCarAct(self, action):
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
            car.updateDynamic(state=2, x=0)
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
                car.updateDynamic(state=2, x=self.length - leftX, y=channel, presentRoad=self.id,
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
                car.updateDynamic(state=2, x=frontCarLoc + 1, y=channel, presentRoad=self.id,
                                  nextCrossId=nextCrossId)
                return 'go'
            # frontCar.state == end and frontCar.x == road.length-1
            else:
                # this channel is full, try next channel
                continue
        # all channels are full, current road cannot receive car
        car.updateDynamic(state=2, x=0)
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
        # **** dynamic parameters ****#
        self.readyCars = []
        self.leftCars = []
        self.garageCarNum = 0
        self.finishCarNum = 0
        # **** flag ****#
        self.done = False
        self.update = False

    # main functions
    def step(self):
        self.update = False
        for roadId in self.validRoad:
            road_dict[roadId].setBucket(self.id)
        # data preapre
        next_car_id_list, next_car_list, next_road_list, nextDirection = [], [], [], []
        #
        # 0,1,2,3 denote north,east,south,west
        #
        for index in range(self.provider.__len__()):
            next_car_id = road_dict[self.provider[index]].firstPriorityCar()
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
                # same next road and high priority lead to conflict
                in_road = road_dict[self.provider[presentRoadIndex]]
                for otherRoadIndex in range(self.provider.__len__()):
                    if next_road_list[presentRoadIndex] == next_road_list[otherRoadIndex] and \
                            nextDirection[presentRoadIndex] < nextDirection[otherRoadIndex]:
                        conflict = True
                        break
                # conflict
                # first priority car exists at road self.provider[otherRoadIndex]
                if conflict:
                    break
                # this car get to the destination
                if next_road_list[presentRoadIndex] == -1:
                    next_car_list[presentRoadIndex].updateDynamic(3)
                    in_road.firstPriorityCarAct('go')
                    car_distribution[1] -= 1
                    car_distribution[2] += 1
                    self.finishCarNum += 1
                    self.update = True
                # move this car to next road
                else:
                    next_road = road_dict[next_road_list[presentRoadIndex]]
                    action = next_road.receiveCar(next_car_list[presentRoadIndex].id)
                    if action == 'wait':
                        # waiting conflict
                        break
                    self.update = True
                    in_road.firstPriorityCarAct(action)
                next_car_id_list[presentRoadIndex] = in_road.firstPriorityCar()
                if next_car_id_list[presentRoadIndex] != -1:
                    next_car_list[presentRoadIndex] = car_dict[next_car_id_list[presentRoadIndex]]
                    next_road_list[presentRoadIndex] = next_car_list[presentRoadIndex].nextRoad()
                    # next_road == -1 => terminal
                    if next_road_list[presentRoadIndex] == -1:
                        nextDirection[presentRoadIndex] = 2
                    else:
                        nextDirection[presentRoadIndex] = self.direction(self.provider[presentRoadIndex],
                                                                         next_road_list[presentRoadIndex])
                # present road doesn't have car to schedule
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
        self.readyCars = self.leftCars
        self.leftCars = []
        if TIME[0] in self.garage.keys():
            self.garage[TIME[0]].sort()
            self.readyCars.extend(self.garage[TIME[0]])
        if self.readyCars.__len__() == 0:
            return
        self.readyCars.sort()
        for roadId in self.receiver:
            road_dict[roadId].setBucket(self.id)
        for i in range(self.readyCars.__len__()):
            carId = self.readyCars[i]
            roadId = car_dict[carId].nextRoad()
            road = road_dict[roadId]
            if roadId not in self.receiver:
                print("Car(%d).Road(%d) not in cross(%d).function:class.driveCarInGarage" % (carId, roadId, self.id))
            act = road.receiveCar(carId)
            if act != 'go':
                self.leftCars.append(self.readyCars[i])
            else:
                self.garageCarNum -= 1
                car_distribution[0] -= 1
                car_distribution[1] += 1


    def garageInitial(self, planTime, carId):
        if planTime not in self.garage.keys():
            self.garage[planTime] = [carId]
        else:
            self.garage[planTime].append(carId)
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
            print("time:%d" % TIME[0])
            print("cars in garage: %d, on the road: %d, finish trip: %d" % (
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
                cross = cross_dict[crossId]
                cross.step()
                if not cross.done:
                    nextCross.append(crossId)
                if cross.update or cross.done:
                    self.dead = False
            unfinishedCross = nextCross
            assert self.dead is False, print("dead lock in", unfinishedCross)
        # print("car pulling away from garage")
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
            visualize.drawMap()
            if car_distribution[2] == car_id_list.__len__():
                print(car_distribution[2])
                print('schedule time: %d' % TIME[0])
                print('%d cars have been scheduled' % car_distribution[2])
                break
            if self.dead:
                break
            TIME[0] += 1


class visualization(object):
    def __init__(self):
        self.maxX, self.maxY = 0, 0
        self.savePath = 'map2'
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
    # preset_answer_path = sys.argv[4]
    # answer_path = sys.argv[5]
    answer_path = sys.argv[4]
    # ************************************* M A I N *******************************************#
    # load .txt files
    carInfo = open(car_path, 'r').read().split('\n')[1:]
    roadInfo = open(road_path, 'r').read().split('\n')[1:]
    crossInfo = open(cross_path, 'r').read().split('\n')[1:]
    answerInfo = open(answer_path, 'r').read().split('\n')

    # preset_answer_info = []
    # with open(preset_answer_path, 'r') as preset_answer_file:
    #     for preset_answer in preset_answer_file.readlines():
    #         if preset_answer.startswith('#'):
    #             continue
    #         preset_answer = preset_answer.replace(' ', '').replace('(', '').replace(')', '').strip().split(',')
    #         preset_answer = [int(x) for x in preset_answer]
    #         preset_answer_info.append(preset_answer)

    # *****************************Create NameSpace And Dictionary*****************************#
    # create car objects
    # line = (id,from,to,speed,planTime)
    for line in carInfo:
        # id, from_, to, speed, planTime, priority_, preset_  = line.replace(' ', '').replace('\t', '')[1:-1].split(',')
        id, from_, to, speed, planTime = line.replace(' ', '').replace('\t', '')[1:-1].split(',')

        # presetOnly
        # if int(preset_) == 0:
        #     continue
        # presetOnly

        car_id_list.append(int(id))
        car_dict[int(id)] = Car(int(id), int(from_), int(to), int(speed), int(planTime))
    # create road objects
    # line = (id,length,speed,channel,from,to,isDuplex)
    for line in roadInfo:
        id, length, speed, channel, from_, to, isDuplex = line.replace(' ', '').replace('\t', '')[1:-1].split(',')
        road_id_list.append(int(id))
        road_dict[int(id)] = Road(int(id), int(length), int(speed), int(channel), int(from_), int(to),
                                  int(isDuplex))
    # create cross objects
    # line = (id,north,east,south,west)
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
                nextCrossId = road_dict[roadId].from_ if road_dict[roadId].from_ != crossId else road_dict[
                    roadId].to
                DFS(nextCrossId, i, crossId)

    DFS(cross_id_list[0])
    for crossId in cross_id_list:
        north, east, south, west = cross_dict[crossId]
        cross_dict[crossId] = Cross(crossId, north, east, south, west)

    # car route initialize
    # line = (id,startTime,route)
    count = 0

    # presetOnly
    for i, line in enumerate(answerInfo):
        if line.__len__() < 3:
            continue
        if line[0] == '#':
            continue
        line = line.strip()[1:-1].split(',')
        carId = int(line[0])
        planTime = int(line[1])
        route = [int(roadId) for roadId in line[2:]]
        car_dict[carId].scheduleInit(planTime, route)
        count += 1
    # presetOnly

    # for i, line in enumerate(preset_answer_info):
    #     carId = line[0]
    #     planTime = line[1]
    #     route = [roadId for roadId in line[2:]]
    #     car_dict[carId].scheduleInit(planTime, route)
    #     count += 1
    print("There are %d cars' route preinstalled" % count)
    # car_distribution[0] = car_id_list.__len__()
    car_distribution[0] = count
    # **** cross initialization ****#
    for carId in car_id_list:
        cross_dict[car_dict[carId].from_].garageInitial(car_dict[carId].planTime, carId)
    # ****Initialization ****#
    car_id_list.sort()
    cross_id_list.sort()
    # simulator
    schedule = Scheduler()
    schedule.schedule()


if __name__ == "__main__":
    main()
