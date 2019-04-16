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

remainingPriCnt = [0, 1]  # second element '1' means continue counting, '0' means finish counting
speedParams = [0, 100, 0, 100]  # highest speed, lowest speed, highest speed of pri, lowest speed of pri
planTimeParams = [0, 10000000, 0, 10000000]  # latest, earliest, latest of pri, earliest of pri
diffSrc = [{}, {}]  # allCarDict, priCarDict, the key of dict is cross_id, key is unique in dict
diffDst = [{}, {}]  # allCarDict, priCarDict
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
        self.carColor = [int(value) for value in np.random.random_integers(0, 255, [3])]  # only for visualization
        self.state = 0  # state 0-ingarage, 1-wait, 2-end, 3-finishtrip,
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
        self.fx, self.fy, self.bx, self.by = 0, 0, 0, 0
        # relative bucket
        self.provideBucket, self.receiveBucket = None, None
        self.px, self.py = None, None

    def setBucket(self, crossId):
        if crossId == self.to:
            self.provideBucket, self.px, self.py = self.forwardBucket, self.fx, self.fy
            if self.isDuplex:
                self.receiveBucket = self.backwardBucket
            else:
                self.receiveBucket = None
        elif crossId == self.from_:
            self.receiveBucket = self.forwardBucket
            if self.isDuplex:
                self.provideBucket, self.px, self.py = self.backwardBucket, self.bx, self.by
            else:
                self.provideBucket, self.px, self.py, self.provideDone = None, None, None, None
        else:
            print("Road:%s is not connected CrossId:%s " % (self.id, crossId))

    def stepInit(self):
        self.fx, self.fy, self.bx, self.by = 0, 0, 0, 0
        self.provideBucket, self.receiveBucket = None, None
        self.px, self.py = None, None
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
        # 'frontCar' indicates the index of the front car in current channel
        # 'frontState' indicates the state of the front car in current channel
        # NOTE: 'frontCar' is initialized to -1, so it also indicates the flag of passing the cross
        frontCar, frontState = -1, 1
        # iterate the channel from front to end
        for i in range(self.length):
            if bucket[i][channel] is not None:
                car = car_dict[bucket[i][channel]]
                v = min(car.speed, self.speed)
                if car.state == 2:
                    frontCar, frontState = i, 2
                    continue
                # if current car is 'wait' state and is not blocked by frontCar
                # then move it to the destination grid and update bucket and car state
                elif i - v > frontCar:
                    car.update(state=2, x=(i - v))
                    bucket[i - v][channel] = bucket[i][channel]
                    bucket[i][channel] = None
                    frontCar, frontState = i - v, 2
                # if current car is 'wait' state and is blocked by a 'end' state car
                # then move current car to the grid just behind the frontCar and update bucket and car state
                elif frontState == 2:
                    if frontCar + 1 != i:
                        bucket[frontCar + 1][channel] = bucket[i][channel]
                        bucket[i][channel] = None
                    car.update(state=2, x=(frontCar + 1))
                    frontCar, frontState = frontCar + 1, 2
                # if current car is 'wait' state and is blocked by a 'wait' state car or could pass the cross
                # then current car remains 'wait' state
                else:
                    frontCar, frontState = i, 1

    #
    # Road function: current road provide the Cross with first priority car
    #
    def findFirstPriorityCar(self):
        if self.provideBucket is None:
            print("Please do Car.setBucket() first!")
        self.px, self.py = 0, 0  # if delete, then dead lock, don't know why
        # far_car_list = []
        # find priority cars
        for x in range(self.length):
            for y in range(self.channel):
                carId = self.provideBucket[x][y]
                if carId is not None and car_dict[carId].state != 2 and car_dict[carId].priority == 1:
                    car = car_dict[carId]
                    speed = min(car.speed, self.speed)
                    # check current priority car's speed whether it is enough to cross
                    if speed > x:
                        # check if there is a front car (if exists, must be non-priority car)
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
                speed = min(car.speed, self.speed)
                # current car's speed is enough and there are no cars in front of it
                if speed > self.px:
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
        # move first priority car to the front grid in the channel
        elif action == 'move':
            carId = self.provideBucket[self.px][self.py]
            self.provideBucket[self.px][self.py] = None
            self.provideBucket[0][self.py] = carId
        # after schedule first priority car, schedule current channel
        self.moveInChannel(self.provideBucket, self.py)

    #
    # Road function: current road receive car
    # Return: 'move' means move to the front grid of the previous road, maybe because current road(self) is full
    #
    def receiveCar(self, carId):
        if self.receiveBucket is None:
            print("Please do Road.setBucket() first!")
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
        self.leftCars = []
        self.garageCarNum = 0
        self.finishCarNum = 0
        self.done = False
        self.update = False

    # main functions
    def step(self):
        self.update = False
        for roadId in self.validRoad:
            road_dict[roadId].setBucket(self.id)
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
                # next_road == -1 => destination
                if next_road == -1:
                    # assign 'go_straight' which is '2'
                    nextDirection.append(2)
                    # 4.10 update: must assign next_road as opposite road !
                    # eg: direction_list: [5574, 5481, 5795, 6450] indicating relative orientation relationship
                    # a car in 6450 get to the destination, so assign next_road as 5481 for it
                    present_index = self.direction_list.index(self.provider[index])
                    oppo_index = (present_index + 2) % 4
                    next_road_list.append(self.direction_list[oppo_index])
                else:
                    # assign direction value (go_straight = 2, turn_left = 1, turn_right = -1)
                    # according to the relative orientation
                    nextDirection.append(self.direction(self.provider[index], next_road))
                    next_road_list.append(next_road)
            else:
                next_car_list.append(-1)
                next_road_list.append(-1)
                nextDirection.append(-1)
        # loop
        for presentRoadIndex in range(self.provider.__len__()):
            conflict = False
            while next_car_list[presentRoadIndex] != -1:
                present_car = next_car_list[presentRoadIndex]
                provide_car_road = road_dict[self.provider[presentRoadIndex]]
                for otherRoadIndex in range(self.provider.__len__()):
                    other_car = next_car_list[otherRoadIndex]
                    # check if present car's next_road is the same as other car's next_road
                    # only same next_road leads to conflict
                    if other_car != -1 and next_road_list[presentRoadIndex] == next_road_list[otherRoadIndex]:
                        # present is pri, other is pri, go_straight > turn_left > turn_right
                        if present_car.priority == 1:
                            if other_car.priority == 1:
                                if nextDirection[presentRoadIndex] < nextDirection[otherRoadIndex]:
                                    conflict = True
                                    break
                        # present is non-pri, other is pri, confict
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
                # if no conflict, present car get to the destination
                # 4.10 update: code below is wrong, because already change from -1 to oppo road
                # if next_road_list[presentRoadIndex] == -1:
                if present_car.to == self.id:
                    present_car.update(state=3)
                    provide_car_road.setFirstPriorityCarAction('go')  # after scheduling first pri car, moveInChannel
                    car_distribution[1] -= 1
                    car_distribution[2] += 1
                    self.finishCarNum += 1
                    self.update = True
                    allScheduleTime[0] += TIME[0] - present_car.planTime
                    if car_distribution[2] % 10 == 0:
                        print('car:%s depart_time:%s schedule_time:%s'%(present_car.id, present_car.depart_time, TIME[0]-present_car.depart_time))
                    if present_car.priority == 1:
                        allPriScheduleTime[0] += TIME[0] - present_car.planTime
                        remainingPriCnt[0] -= 1
                        if remainingPriCnt[1] and remainingPriCnt[0] == 0:
                            priScheduleTime[0] = TIME[0] - planTimeParams[3]
                            remainingPriCnt[1] = 0

                # move present car to next road(action='go') or to the front grid(action='move')
                else:
                    next_road = road_dict[next_road_list[presentRoadIndex]]
                    action = next_road.receiveCar(present_car.id)
                    if action == 'wait':
                        # waiting conflict
                        break
                    self.update = True
                    present_car.update(state=2)
                    provide_car_road.setFirstPriorityCarAction(action)  # after scheduling first pri car, moveInChannel

                # # priority cars could depart in present road
                # 4.10 update, not simply .from_, but check the provide or receive direction to determine to or from_
                if provide_car_road.from_ == self.id:
                    depart_cross_id = provide_car_road.to
                else:
                    depart_cross_id = provide_car_road.from_
                depart_cross = cross_dict[depart_cross_id]
                depart_cross.drivePriCarInGarage(provide_car_road.id)
                # because drive pri car func may change relative bucket, so must call setBucket !
                provide_car_road.setBucket(self.id)

                next_car = provide_car_road.findFirstPriorityCar()
                # present road still has a cars to schedule, put it in the next_car_list
                if next_car != -1:
                    next_car_list[presentRoadIndex] = car_dict[next_car]
                    next_road_list[presentRoadIndex] = car_dict[next_car].nextRoad()
                    # next_road == -1 => terminal
                    if next_road_list[presentRoadIndex] == -1:
                        # # assign 'go_straight' which is '2'
                        nextDirection[presentRoadIndex] = 2
                        # 4.11 update: must assign next_road as opposite road !
                        # note that the index is 'presentRoadIndex' not just 'index', 'index' refers to code outside while loop
                        present_index = self.direction_list.index(self.provider[presentRoadIndex])
                        oppo_index = (present_index + 2) % 4
                        next_road_list[presentRoadIndex] = self.direction_list[oppo_index]
                    else:
                        nextDirection[presentRoadIndex] = self.direction(self.provider[presentRoadIndex],
                                                                         next_road_list[presentRoadIndex])
                # present road doesn't have a car to schedule
                # -1 means present road has finished scheduling
                else:
                    next_car_list[presentRoadIndex] = -1
                    next_road_list[presentRoadIndex] = -1
                    nextDirection[presentRoadIndex] = -1

        done = True
        for fromA in range(self.provider.__len__()):
            if next_car_list[fromA] != -1:
                # if any roads didn't finish scheduling, then assign self.done = False
                done = False
        self.done = done

    #
    # This func is called at the end of the time piece
    #
    def driveCarInGarage(self):
        # leftCars are all from the drivePriCarInGarage
        readyCars = self.leftCars
        self.leftCars = []
        if readyCars.__len__() == 0:
            return
        readyCars = list(set(readyCars))
        # readyCars.sort()
        # 4.10 find a bug: only call readyCars.sort() is wrong!
        # because readyCars include pri and non-pri cars, but doesn't sort in order (pri, depart_time, car_id)!
        readyPri, readyNonPri = [], []
        for (depart_time, car_id) in readyCars:
            if car_dict[car_id].priority == 1:
                readyPri.append((depart_time, car_id))
            else:
                readyNonPri.append((depart_time, car_id))
        readyPri.sort()
        readyNonPri.sort()
        readyCars = readyPri + readyNonPri
        for road_id in self.receiver:
            road_dict[road_id].setBucket(self.id)
        for i in range(readyCars.__len__()):
            depart_time = readyCars[i][0]
            car_id = readyCars[i][1]
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

    #
    # Parameter: to_road = 'road_id', if given(not default None), then only drive cars on this road
    #
    def drivePriCarInGarage(self, to_road=None):
        # leftCars include delayed cars
        readyPriCars = []
        tempLeftCars = []
        for (depart_time, car_id) in self.leftCars:
            if car_dict[car_id].priority == 1:
                readyPriCars.append((depart_time, car_id))
            else:
                tempLeftCars.append(((depart_time, car_id)))
        if TIME[0] in self.garage.keys():
            for car_id in self.garage[TIME[0]]:
                depart_time = TIME[0]
                if car_dict[car_id].priority == 1:
                    if (depart_time, car_id) not in readyPriCars:
                        readyPriCars.append((depart_time, car_id))
                else:
                    if (depart_time, car_id) not in tempLeftCars:
                        tempLeftCars.append(((depart_time, car_id)))
        self.leftCars = tempLeftCars
        if readyPriCars.__len__() == 0:
            return
        readyPriCars = list(set(readyPriCars))
        # first sort depart_time ascending, then sort car_id ascending
        readyPriCars.sort()
        for road_id in self.receiver:
            if to_road is None:
                road_dict[road_id].setBucket(self.id)
            if to_road is not None and to_road == road_id:
                road_dict[road_id].setBucket(self.id)
        for i in range(readyPriCars.__len__()):
            depart_time = readyPriCars[i][0]
            car_id = readyPriCars[i][1]
            road_id = car_dict[car_id].nextRoad()
            if road_id not in self.receiver:
                print("Car(%d).Road(%d) not in cross(%d).function:class.outOfCarport" % (carId, roadId, self.id_))
            if to_road is not None and to_road != road_id:
                self.leftCars.append((depart_time, car_id))  # don't forget to add into self.leftCars !
                continue
            road = road_dict[road_id]
            action = road.receiveCar(car_id)
            if action != 'go':
                # connot drive present car out of garage, so append it to the 'leftCars' list
                self.leftCars.append((depart_time, car_id))
            else:
                # on the go!
                # print('pri car %d departs from cross %d to road %d' %(car_id, self.id, road_id))
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


class Scheduler(object):
    def __init__(self, carInfo, roadInfo, crossInfo, answer_info, preset_answer_info):
        self.dead = False
        global TIME, allScheduleTime, priScheduleTime, allPriScheduleTime
        global remainingPriCnt, speedParams, planTimeParams, diffSrc, diffDst, factor
        global priority_car_list, car_distribution, car_id_list, road_id_list, cross_id_list
        global cross_dict, car_dict, road_dict

        TIME = [0]
        allScheduleTime = [0]
        priScheduleTime = [0]
        allPriScheduleTime = [0]

        remainingPriCnt = [0, 1]  # second element '1' means continue counting, '0' means finish counting
        speedParams = [0, 100, 0, 100]  # highest speed, lowest speed, highest speed of pri, lowest speed of pri
        planTimeParams = [0, 10000000, 0, 10000000]  # latest, earliest, latest of pri, earliest of pri
        diffSrc = [{}, {}]  # allCarDict, priCarDict, the key of dict is cross_id, key is unique in dict
        diffDst = [{}, {}]  # allCarDict, priCarDict
        factor = [0, 0]

        priority_car_list = []
        car_distribution = [0, 0, 0]
        car_id_list, road_id_list, cross_id_list = [], [], []
        cross_dict, car_dict, road_dict = {}, {}, {}

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

        factor[0] = 0.05 * round(car_dict.__len__() / remainingPriCnt[0], 5) + \
                    0.2375 * round(
            round(speedParams[0] / speedParams[1], 5) / round(speedParams[2] / speedParams[3], 5),
            5) + \
                    0.2375 * round(
            round(planTimeParams[0] / planTimeParams[1], 5) / round(planTimeParams[2] / planTimeParams[3], 5), 5) + \
                    0.2375 * round(diffSrc[0].__len__() / diffSrc[1].__len__(), 5) + \
                    0.2375 * round(diffDst[0].__len__() / diffDst[1].__len__(), 5)

        factor[1] = 0.8 * round(car_dict.__len__() / remainingPriCnt[0], 5) + \
                    0.05 * round(round(speedParams[0] / speedParams[1], 5) / round(speedParams[2] / speedParams[3], 5),
                                 5) + \
                    0.05 * round(
            round(planTimeParams[0] / planTimeParams[1], 5) / round(planTimeParams[2] / planTimeParams[3], 5), 5) + \
                    0.05 * round(diffSrc[0].__len__() / diffSrc[1].__len__(), 5) + \
                    0.05 * round(diffDst[0].__len__() / diffDst[1].__len__(), 5)

        print('factor a = %.10f, b= %.10f' % (factor[0], factor[1]))

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
                    nextCrossId = road_dict[roadId].from_ if road_dict[roadId].from_ != crossId else road_dict[
                        roadId].to
                    DFS(nextCrossId, i, crossId)

        DFS(cross_id_list[0])
        for crossId in cross_id_list:
            north, east, south, west = cross_dict[crossId]
            cross_dict[crossId] = Cross(crossId, north, east, south, west)

        count = 0

        for i, line in enumerate(preset_answer_info):
            carId = line[0]
            depart_time = line[1]
            route = [roadId for roadId in line[2:]]
            car_dict[carId].scheduleInit(depart_time, route)
            count += 1

        # presetOnly
        for i, line in enumerate(answer_info):
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

        car_distribution[0] = carInfo.__len__()
        print("There are %d cars' route preinstalled" % carInfo.__len__())

        for carId in car_id_list:
            cross_dict[car_dict[carId].from_].garageInit(car_dict[carId].depart_time, carId)
        car_id_list.sort()
        cross_id_list.sort()

    def step(self):
        if TIME[0] % 200 == 0:
            print("- time:%d, allScheduleTime:%d, priScheduleTime:%d, allPriScheduleTime:%d" % (
                TIME[0], allScheduleTime[0], priScheduleTime[0], allPriScheduleTime[0]))
            print("--- cars in garage: %d, on the road: %d, finish trip: %d" % (
                car_distribution[0], car_distribution[1], car_distribution[2]))
        for crossId in cross_id_list:
            cross_dict[crossId].done = False
        for road in road_id_list:
            road_dict[road].stepInit()
        # priority cars depart
        for cross_id in cross_id_list:
            for road_id in cross_dict[cross_id].validRoad:
                road_dict[road_id].setBucket(cross_id)
            cross_dict[cross_id].drivePriCarInGarage()
        # print('----------TIME: %d, finish pre priority cars departure----------------'%(TIME[0]))
        unfinishedCross = cross_id_list
        while unfinishedCross.__len__() > 0:
            self.dead = True
            nextCross = []
            for cross_id in unfinishedCross:
                cross = cross_dict[cross_id]
                cross.step()
                if not cross.done:
                    nextCross.append(cross_id)
                if cross.update or cross.done:
                    self.dead = False
            unfinishedCross = nextCross
            assert self.dead is False, print("dead lock in", unfinishedCross)
        for i in range(cross_id_list.__len__()):
            cross_id = cross_id_list[i]
            for roadId in cross_dict[cross_id].validRoad:
                road_dict[roadId].setBucket(cross_id)
            cross_dict[cross_id].driveCarInGarage()
        # for logging!
        # print('time:%d' % TIME[0])
        # with open('my_logging.txt', 'a') as my_logging:
        #     my_logging.writelines('time:%d' % TIME[0] + '\n')
        # for road_id in road_id_list:
        #     channel_num = road_dict[road_id].channel
        #     channel_list = [[] for x in range(channel_num)]
        #     for x, y in road_dict[road_id].forwardBucket.items():
        #         for i in range(channel_num):
        #             temp = -1 if y[i] is None else y[i]
        #             channel_list[i].append(temp)
        #     # print('(%d_forward_%s)'%(road_id, channel_list))
        #     if road_dict[road_id].isDuplex == 1:
        #         channel_num = road_dict[road_id].channel
        #         b_channel_list = [[] for x in range(channel_num)]
        #         for x, y in road_dict[road_id].backwardBucket.items():
        #             for i in range(channel_num):
        #                 temp = -1 if y[i] is None else y[i]
        #                 b_channel_list[i].append(temp)
        #         # print('(%d_backward_%s)'%(road_id, b_channel_list))
        #     with open('my_logging.txt', 'a') as my_logging:
        #         my_logging.writelines('(%d_forward_%s)' % (road_id, channel_list) + '\n')
        #         if road_dict[road_id].isDuplex == 1:
        #             my_logging.writelines('(%d_backward_%s)' % (road_id, b_channel_list) + '\n')

        # print('----------TIME: %d, finish non-depart cars departure----------------'%(TIME[0]))

    def schedule(self):
        while True:
            self.step()
            if car_distribution[2] == car_id_list.__len__():
                print('%d cars have been scheduled' % car_distribution[2])
                print('priScheduleTime: %d, allPriScheduleTime: %d' % (priScheduleTime[0], allPriScheduleTime[0]))
                print('schedule time: %d, allScheduleTime: %d' % (TIME[0], allScheduleTime[0]))
                JudgeTime = factor[0] * priScheduleTime[0] + TIME[0]
                JudgeTotalTime = factor[1] * allPriScheduleTime[0] + allScheduleTime[0]
                print('JudgeTime: %d, JudgeTotalTime: %d' % (round(JudgeTime), round(JudgeTotalTime)))
                return TIME[0]
            if self.dead:
                break
            TIME[0] += 1


