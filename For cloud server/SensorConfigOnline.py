#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
add camera into searching space
"""
import time
from Point2 import Point
import numpy as np
from mapTools import privacy_init, hasprivacythreat2, initialmapwithknowngrid, initialmapwithknowngrid_ratio, caculate_privacy_surround
import copy
from Configure import configure
import math
from heapq import heappush
import sys
import os

# from log import Log
# log = Log(__name__).getlog()

sys.setrecursionlimit(1000000)


class AStar:
    """
    AStar算法的Python3.x实现
    """

    class Node:  # 描述AStar算法中的节点数据
        def __init__(self, point, endPoint, ideallength, g=0):
            self.point = point  # 自己的坐标
            self.father = None  # 父节点
            self.g = g  # g值，g值在用到的时候会重新算
            self.step = 0
            self.cam = 0
            self.h = (abs(endPoint.x - point.x) + abs(endPoint.y - point.y) + abs(endPoint.z - point.z)) # 计算h值 曼哈顿距离

        def __str__(self):
            return "point as the node: x:" + str(self.point.x) + ",y:" + str(self.point.y) + ",z:" + str(self.point.z) + ",ca:" + str(self.point.ca)

        # 堆需要节点与节点之间的比较，因此必须实现这个魔术方法
        def __lt__(self, other):
            return self.g + self.h < other.g + other.h

    def __init__(self, occ_grid, pri_grid, grid, sum_privacy, startPoint, endPoint, passTag, Tbudget, Toptimal, preference):
        """
        构造AStar算法的启动条件
        :param map3d: Array2D类型的寻路数组
        :param startPoint: Point或二元组类型的寻路起点
        :param endPoint: Point或二元组类型的寻路终点
        :param passTag: int类型的可行走标记（若地图数据!=passTag即为障碍）
        :param threatlist: privacy restricted area affected
        """
        # 开启表
        self.openList = []
        # 关闭表
        self.closeList = []
        # 寻路地图
        self.map3d = occ_grid
        self.grid = grid
        self.prigrid = pri_grid
        self.sumpri = sum_privacy
        self.ideallength = abs(endPoint.x - startPoint.x) + abs(endPoint.y - startPoint.y) + abs(endPoint.z - startPoint.z)
        self.Tbudget = Tbudget
        self.Toptimal = Toptimal
        # print("Time limit: ", self.Tbudget)
        #self.threatlist = threat_list
        self.timestep = 0
        #self.startPoint = startPoint
        self.preference = preference


        # 起点终点
        if isinstance(startPoint, Point) and isinstance(endPoint, Point):
            self.startPoint = startPoint
            self.endPoint = endPoint
        else:
            self.startPoint = Point(*startPoint)
            self.endPoint = Point(*endPoint)

        ## 结束点的第二种可能性 - 0615
        self.endPoint2 = Point(endPoint.x,endPoint.y,endPoint.z, 1-endPoint.ca)

        # 障碍物标记
        self.passTag = [1,2,3,4]

        #print("endpoint",self.endPoint, self.endPoint2)

    """new function

    def updateNodeHvalue(self):
        for i in range(len(self.openList)):
            node = self.openList[i]
            #print("#######",node)
            #print("$$$", node.point.x)
            #rou1 = (abs(node.point.x - self.startPoint.x) +
            #        abs(node.point.y - self.startPoint.y) +
            #        abs(node.point.z - self.startPoint.z)) / self.ideallength
            rou1 = 1- (abs(node.point.x - self.endPoint.x) +
                    abs(node.point.y - self.endPoint.y) +
                    abs(node.point.z - self.endPoint.z)) / self.ideallength
            rou2 = node.step / self.Tbudget
            adaptive1 = math.exp(1 - rou1 / rou2)
            adaptive2 = math.exp(rou1 / rou2 - 1)
            # print(rou1,rou2, adaptive1, adaptive2)
            fathernode = node.father
            # print("*******", node.point.x, fathernode.point.x)
            delta_h = 0
            for j in range(len(self.threatlist)):
                # far away, oppisite
                threat = self.threatlist[j]
                #print(threat)
                
                f (abs(node.point.x - threat[0]) + abs(node.point.y - threat[1]) + abs(node.point.z - threat[2])) > (
                        abs(self.endPoint.x - threat[0]) + abs(self.endPoint.y - threat[1]) +
                        abs(self.endPoint.z - threat[2])):
                    delta_h += adaptive1 * self.map3d[threat[0]][threat[1]][threat[2]]
                else:
                    delta_h += adaptive2 * self.map3d[threat[0]][threat[1]][threat[2]]
                
                if (abs(node.point.x - threat[0]) + abs(node.point.y - threat[1]) + abs(node.point.z - threat[2])) > (
                        abs(fathernode.point.x - threat[0]) + abs(fathernode.point.y - threat[1]) +
                        abs(fathernode.point.z - threat[2])):
                    delta_h += adaptive1 * self.map3d[threat[0]][threat[1]][threat[2]] ## 绕路
                else:
                    delta_h += adaptive2 * self.map3d[threat[0]][threat[1]][threat[2]]
            node.h = (abs(self.endPoint.x - node.point.x) + abs(self.endPoint.y - node.point.y) + abs(self.endPoint.z - node.point.z))/self.ideallength
            node.h = node.h * delta_h
            # print("node.h:", node.h)
   
    def getMinNode(self):

        获得openlist中F值最小的节点
        :return: Node


        currentNode = self.openList[0]
        for node in self.openList:
            if node.g + node.h < currentNode.g + currentNode.h:
                currentNode = node
        return currentNode
 
        currentNode = self.openList[0]
        for node in self.openList:
            if node.g + node.h < currentNode.g + currentNode.h:
                currentNode = node
        return currentNode

    """


    def pointInCloseList(self, point):
        for node in self.closeList:
            if node.point == point:
                return True
        return False

    def point_in_close_list(self, point, step_num):
        for node in self.closeList:
            if node.point == point and node.step == step_num:
                return True
        return False

    def pointInOpenList(self, point):
        for node in self.openList:
            if node.point == point:
                return node
        return None

    def the_same_points_in_open_list(self, point):
        same_points_list = []
        for node in self.openList:
            if node.point == point:
                same_points_list.append(node)
        return same_points_list

    def endPointInCloseList(self):
        for node in self.closeList: ## 0615
            if node.point == self.endPoint or node.point == self.endPoint2:
                return node
        return None

    def endPointInOpenList(self):
        for node in self.openList:
            if node.point == self.endPoint or node.point == self.endPoint2: # 0615
                return node
        return None

    def searchNear(self, minF, offsetX, offsetY, offsetZ, cam):
        """
        搜索节点周围的点
        :param minF:F值最小的节点
        :param offsetX:坐标偏移量
        :param offsetY:
        :return:
        """
        # 越界检测
        if (minF.point.x + offsetX < 0 or minF.point.x + offsetX > self.grid[0] - 1 or
            minF.point.y + offsetY < 0 or minF.point.y + offsetY > self.grid[1] - 1 or
            minF.point.z + offsetZ < 0 or minF.point.z + offsetZ > self.grid[2] - 1):
            return
        # 如果是障碍，就忽略
        # if self.map3d[minF.point.x + offsetX][minF.point.y + offsetY][minF.point.z + offsetZ] != self.passTag:
        # if self.map3d[minF.point.x + offsetX][minF.point.y + offsetY][minF.point.z + offsetZ] in self.passTag:
        if self.map3d[minF.point.x + offsetX][minF.point.y + offsetY][minF.point.z + offsetZ] in self.passTag:
            return
        # 如果在关闭表中，就忽略
        currentPoint = Point(minF.point.x + offsetX, minF.point.y + offsetY, minF.point.z + offsetZ, cam)
        if self.pointInCloseList(currentPoint):
            return

        """new setting for time limit"""

        # 设置单位花费
        # step = 1/self.Toptimal
        step = 1
        # privacy_threat = (self.prigrid[minF.point.x + offsetX][minF.point.y + offsetY][minF.point.z + offsetZ] * math.exp(-(cam)) )/self.sumpri
        privacy_threat = caculate_privacy_surround(self.grid, currentPoint, self.map3d, self.pri_radius)

        time_punishment = 1
        if minF.step + 1 > self.Toptimal:
            time_punishment = math.exp((minF.step + 1 -self.Toptimal)/(self.Tbudget-self.Toptimal))
        # delta_g = self.preference * time_punishment * step + privacy_threat

        # type1
        delta_g =  time_punishment * privacy_threat
        # type2
        #delta_g = privacy_threat

        # 如果不在openList中，就把它加入openlist
        # currentNode = self.pointInOpenList(currentPoint)
        # 用一个列表来收集相同的点
        """
        same_point_list = self.the_same_points_in_open_list(currentPoint)
        if not same_point_list:
            # print("currentPoint:", currentPoint, currentNode)
            currentNode = AStar.Node(currentPoint, self.endPoint, self.ideallength, g=minF.g + delta_g)
            currentNode.father = minF
            currentNode.cam = minF.cam + cam
            currentNode.step = minF.step + 1
            self.openList.append(currentNode)

            #print("MinF$$$$$: ", minF.step, minF.point, currentNode.step, currentNode.point)
            return
        """
        currentNode = self.pointInOpenList(currentPoint)
        if not currentNode:
            currentNode = AStar.Node(currentPoint, self.endPoint, self.ideallength, g=minF.g + delta_g)
            currentNode.father = minF
            #self.openList.append(currentNode)
            heappush(self.openList, currentNode)
            return
        # 如果在openList中，判断minF到当前点的G是否更小
        if minF.g + delta_g < currentNode.g:  # 如果更小，就重新计算g值，并且改变father
            currentNode.g = minF.g + delta_g
            currentNode.father = minF

        """
        # 检查这些相同的点的step值，如果有相同的，就更新相同的
        # 如果没有相同的，就看看当前的step值和最小的step值
        # 如果最小的step值小，说明当前的step没用
        # 如果当前的step小，说明当前的step值有用，添加到openlist中
        smallest_step_num = self.Tbudget
        same_step_in_list = False
        same_node = None
        for node in same_point_list:
            if minF.step+1 == node.step:
                same_step_in_list = True
                same_node = node
                break
            if smallest_step_num > node.step:
                smallest_step_num = node.step
        if same_step_in_list:
            if minF.g + delta_g < same_node.g:  # 如果更小，就重新计算g值，并且改变father
                same_node.g = minF.g + delta_g
                same_node.father = minF
                same_node.step = minF.step + 1
                same_node.cam = minF.cam
        else:
            if minF.step+1 < smallest_step_num:
                currentNode = AStar.Node(currentPoint, self.endPoint, self.ideallength, g=minF.g + delta_g)
                currentNode.father = minF
                currentNode.cam = minF.cam + cam
                currentNode.step = minF.step + 1
                self.openList.append(currentNode)

        """

    def start(self):
        """
        开始寻路
        :return: None或Point列表（路径）
        """
        # 判断寻路终点是否是障碍
        #if self.map3d[self.endPoint.x][self.endPoint.y][self.endPoint.z] != self.passTag:
        #if self.map3d[self.endPoint.x][self.endPoint.y][self.endPoint.z] in self.passTag:
        if self.map3d[self.endPoint.x][self.endPoint.y][self.endPoint.z] in self.passTag:
            return None
        # 1.将起点放入开启列表
        startNode = AStar.Node(self.startPoint, self.endPoint, self.ideallength)
        #self.openList.append(startNode)
        heappush(self.openList, startNode)
        # 2.主循环逻辑
        while True:
            # 找到F值最小的点
            #minF = self.getMinNode()
            # print("minF: ", minF.point, minF.step)
            #if minF == None :
            #    print("no solution for minF!")
            #    return None
            minF = None
            if len(self.openList) == 0:
                print("No solution for minF!")
                return None
            else:
                minF = self.openList[0]
            # 把这个点加入closeList中，并且在openList中删除它
            self.closeList.append(minF)
            self.openList.remove(minF)

            # 判断这个节点的上下左右节点
            # turn on camera
            # actions = [[0, -1, 0, 0],[0, 1, 0, 0],[-1, 0, 0, 0],[1, 0, 0, 0],[0, 0, 1, 0],[0, 0, -1, 0],[0, -1, 0, 1],[0, 1, 0, 1],[-1, 0, 0, 1],[0, 0, 1, 1],[0, 0, -1, 1],[1, 0, 0, 1]]
            # actionlist = [0,1,2,3,4,5,6,7,8,9,10,11]
            # np.random.shuffle(actionlist)
            #
            # for i in range (len(actionlist)):
            #    self.searchNear(minF, actions[actionlist[i]][0], actions[actionlist[i]][1], actions[actionlist[i]][2], actions[actionlist[i]][3])
            # """
            # 判断这个节点的上下左右节点
            self.searchNear(minF, 0, -1, 0, 0)
            self.searchNear(minF, 0, 1, 0, 0)
            self.searchNear(minF, -1, 0, 0, 0)
            self.searchNear(minF, 1, 0, 0, 0)
            self.searchNear(minF, 0, 0, 1, 0)
            self.searchNear(minF, 0, 0, -1, 0)
            #"""

            #self.updateNodeHvalue()

            # 判断是否终止
            point = self.endPointInCloseList()
            if point:  # 如果终点在关闭表中，就返回结果
                # print("The plan found!")
                cPoint = point
                pathList = []
                while True:
                    if cPoint.father:
                        pathList.append(cPoint.point)
                        cPoint = cPoint.father
                    else:
                        # print(pathList)
                        # print(list(reversed(pathList)))
                        # print(pathList.reverse())
                        return list(reversed(pathList))
            if len(self.openList) == 0:
                print("No plan could meet the time limit!")
                return None

def Astar_Sensor_Config_online(config, iteration, log, num):

    grid_x = config.grid_x
    grid_y = config.grid_y
    grid_z = config.grid_z
    grid = config.grid
    safety_threshold = config.safety_threshold
    privacy_threshold = config.privacy_threshold
    # privacy_radius = 1 ##
    privacy_radius = config.privacy_radius

    # drone parameter
    starting_point = config.starting_point
    end_point = config.end_point
    T_budget = config.T_budget
    T_optimal = config.T_optimal
    viewradius = config.viewradius
    Kca = config.Kca
    threat_list = []

    #occ_grid, obstacle_num, occ_grid_known, pri_grid_known, privacy_sum_known = initialmap(grid_x, grid_y, grid_z,
    #                                                                                       starting_point, end_point,
    #                                                                                       safety_threshold,
    #                                                                                       privacy_threshold,
    #                                                                                       privacy_radius)
    # occ_grid_name = "occ_grid" + str(iteration) + ".npy"
    occ_grid_name = os.getcwd() + "/data/" + "occ_grid-" + str(num) + ".npy"
    occ_grid = np.load(file=occ_grid_name)
    # occ_grid = np.load(file="occ_grid-1.npy")
    pri_grid, privacy_sum = privacy_init(grid_x, grid_y, grid_z, occ_grid, privacy_radius)
    # occ_grid_known_name = "occ_grid_known" + str(iteration) + ".npy"
    occ_grid_known_name = os.getcwd() +"/data/"+"occ_grid_known_initial" + str(iteration) + ".npy"
    occ_grid_known = np.load(file=occ_grid_known_name)
    # occ_grid_known = np.load(file="occ_grid_known.npy")
    pri_grid_known, privacy_sum_known = privacy_init(grid_x, grid_y, grid_z, occ_grid_known, privacy_radius)
    #occ_grid_known, pri_grid_known, privacy_sum_known = initialmapwithknowngrid(grid_x, grid_y, grid_z,
    #                                                                            privacy_threshold, privacy_radius,
    #                                                                            occ_grid)
    #pri_grid, privacy_sum = privacy_init(grid_x, grid_y, grid_z, occ_grid, privacy_radius)
    # print("The occ_grid is: ")
    # for m in range(grid_x):
    #     print("The value of x: ", m)
    #     print(occ_grid[m])
    starttime = time.time()
    #aStar = AStar(occ_grid, pri_grid_known, grid, privacy_sum_known, starting_point, end_point, 1 , T_budget)
    # 开始寻路
    #trajectory_ref = aStar.start()
    #trajectory_ref_temp = np.load(file="plan_path.npy")
    # 导入初规划路径路径结果
    reference_path_name = os.getcwd() +"/data/"+"reference_path" + str(iteration) + ".npy"
    trajectory_ref_temp = np.load(file=reference_path_name)
    # trajectory_ref_temp = np.load(file="reference_path.npy")
    trajectory_ref = []
    for i in range (len(trajectory_ref_temp)):
        point = Point(int(trajectory_ref_temp[i][0]),int(trajectory_ref_temp[i][1]),int(trajectory_ref_temp[i][2]),int(trajectory_ref_temp[i][3]))
        trajectory_ref.append(point)

    endtime = time.time()
    dtime = endtime - starttime
    # print("程序运行时间：%.8s s" % dtime)

    path_grid = copy.deepcopy(occ_grid)

    # print(len(pathList))
    sum = 0
    if trajectory_ref == None:
        print("No solution!")
        exit(0)
    else:
        for point in trajectory_ref:
            #print(point)
            path_grid[point.x][point.y][point.z] = 9
            sum += pri_grid_known[point.x][point.y][point.z]
            # print(point, pri_grid_known[point.x][point.y][point.z])
        # print("----------------------", len(trajectory_ref))

    # 再次显示地图

    # print(path_grid, sum)
    #trajectory_ref = [starting_point] + trajectory_ref
    trajectory_plan = copy.deepcopy(trajectory_ref)
    # sensor_initial = np.zeros(len(trajectory_plan))
    # sensor_plan = copy.deepcopy(sensor_initial)
    time_step = 0
    # print("---------------------------------")
    # print("The length of original plan is: ", len(trajectory_plan))
    # for m in range(len(trajectory_plan)):
    #     print("The No.", m, " step: ", trajectory_plan[m])
    # print()

    idx = 0
    current_f = sum + len(trajectory_plan)
    replantime = 0

    while not (idx >= len(trajectory_plan)):
        current_p = trajectory_plan[idx]
        current_ca = trajectory_plan[idx].ca
        #print("currentnow:", current_p, idx)

        if current_p.x == end_point.x and current_p.y == end_point.y and current_p.z == end_point.z :
            # print("current:", current_p, idx)
            break

        next_p = trajectory_plan[idx+1]
        next_idx = idx + 1
        # print (current_p,next_p,next_idx)
        # print("The UAV would move a step: ")
        # print("The current point: ", current_p)
        # print("The next point: ", next_p)
        # print("The index of next point: ", next_idx, "\n")

        if current_ca == 2:  ## 1 = camera is open with high resolution, 2 = camera is off with lower resolution 0630
            time_step += 1
            current_p = next_p
            idx += 1
            # print("The UAV has finished this step.\n")
            continue

        # take picture
        # update occ_grid, pri_grid
        flag, occ_grid_known, pri_grid_known, privacy_sum_known, threat_list = hasprivacythreat2 (current_p, occ_grid_known, occ_grid, pri_grid_known, privacy_sum_known, config)
        # print("The length of privacy_list: ", len(threat_list))
        #for m in range(len(threat_list)):
        #    print(threat_list[m])

        if flag:
            # localization
            # p_threat, h_impact = privacy_modeling()
            # update occ_grid, pri_grid
            replan_flag = 0
            for j in range (idx+1, len(trajectory_plan)):
                if pri_grid_known[trajectory_plan[j].x][trajectory_plan[j].y][trajectory_plan[j].z] > 0:
                    if trajectory_plan[j].ca != 2:
                        trajectory_plan[j].ca = 2
                        replan_flag = 1
                        # print("change sensor configuration for next point")
            if replan_flag :
                replantime += 1
            # print("replan_time:", replantime)
            # cam_off = 0
            # for ll in range(len(trajectory_plan)):
            #     sum += pri_grid_known[trajectory_plan[ll].x][trajectory_plan[ll].y][trajectory_plan[ll].z]
            #     cam_off += trajectory_plan[ll].ca
            #     print("now", trajectory_plan[ll])
            # print("The length of now_trajectory_plan: ", len(trajectory_plan), sum, cam_off)

            # current_f = sum + len(trajectory_plan) + cam_off

            # print("fitness", current_f)

        time_step += 1
        idx = idx + 1
        # print("The UAV has finished this step.\n")

    # print(occ_grid)
    path_grid2 = copy.deepcopy(occ_grid)

    ## log info
    # sum of privacy risk with pri_grid
    PR_sum_unknown_plan = 0
    # sum of privacy risk with pri_grid_knwon
    PR_sum_known_plan = 0
    # times of camera reconfigured
    num_ca_plan = 0
    # times of with intrusion of restricted area with pri_grid
    num_intruder_notknown_plan = 0
    # times of with intrusion of restricted area with pri_grid_knwon
    num_intruder_known_plan = 0
    # num_should_avoid_intruder_plan = 0
    # num_cannot_avoid_intruder_plan = 0

    for point in trajectory_plan:
        if point.ca == 1:
            path_grid2[point.x][point.y][point.z] = 7
        else:
            path_grid2[point.x][point.y][point.z] = 10
            num_ca_plan += 1
        # sum_unknown_plan += pri_grid[point.x][point.y][point.z] * math.exp(-(point.ca))
        # sum_known_plan += pri_grid_known[point.x][point.y][point.z] * math.exp(-(point.ca))
        PR_sum_unknown_plan += caculate_privacy_surround(grid, point, occ_grid, privacy_radius)
        PR_sum_known_plan += caculate_privacy_surround(grid, point, occ_grid_known, privacy_radius)
        if pri_grid[point.x][point.y][point.z] > 0 and occ_grid[point.x][point.y][point.z] == 0:
            num_intruder_notknown_plan += 1

        if pri_grid_known[point.x][point.y][point.z] > 0 and occ_grid_known[point.x][point.y][point.z] == 0:
            num_intruder_known_plan += 1

        # if occ_grid[point.x][point.y][point.z] == 2 or occ_grid[point.x][point.y][point.z] == 3 or occ_grid[point.x][point.y][point.z] == 4 :
        #     num_should_avoid_intruder_plan += 1
        #
        # if occ_grid_known[point.x][point.y][point.z] == 2 or occ_grid_known[point.x][point.y][point.z] == 3 or occ_grid_known[point.x][point.y][point.z] == 4:
        #     num_cannot_avoid_intruder_plan += 1
        # print(point, pri_grid_known[point.x][point.y][point.z])
    print("\033[94mFitness for replanned path:\033[0m \n ", len(trajectory_plan) - 1, PR_sum_unknown_plan,
          PR_sum_known_plan,
          num_ca_plan,
          num_intruder_notknown_plan, num_intruder_known_plan)
    log.info("Online_Sensor_Config: Length of replanned trajectory: %d" % (len(trajectory_plan) - 1))
    log.info("Online_Sensor_Config: Sum of privacy threat of replanned trajectory(occ_grid): %f" % PR_sum_unknown_plan)
    log.info("Online_Sensor_Config: Sum of privacy threat of replanned trajectory(occ_grid_known): %f" % PR_sum_known_plan)
    log.info("Online_Sensor_Config: Times of turning off camera of replanned trajectory: %d" % num_ca_plan)
    # log.info("Online_Sensor_Config: Times of intrusion of replanned trajectory: %d" % num_intruder_plan)
    log.info("Online_Sensor_Config: Times of intrusion of replanned trajectory(occ_grid): %d" % num_intruder_notknown_plan)
    log.info("Online_Sensor_Config: Times of intrusion of replanned trajectory(occ_grid_known): %d" % num_intruder_known_plan)
    # log.info(
    #     "Online_Sensor_Config: Times of intrusion of replanned trajectory(should avoid): %d" % num_should_avoid_intruder_plan)
    # log.info(
    #     "Online_Sensor_Config: Times of intrusion of replanned trajectory(cannot avoid): %d" % num_cannot_avoid_intruder_plan)


    # 再次显示地图
    PR_sum_unknown_ref = 0
    PR_sum_known_ref = 0
    num_ca_ref = 0
    num_intruder_notknown_ref = 0
    num_intruder_known_ref = 0
    # num_should_avoid_intruder_ref = 0
    # num_cannot_avoid_intruder_ref = 0

    for point in trajectory_ref:

        # sum_unknown_ref += pri_grid[point.x][point.y][point.z] * math.exp(-(point.ca))
        # sum_known_ref += pri_grid_known[point.x][point.y][point.z] * math.exp(-(point.ca))
        PR_sum_unknown_ref += caculate_privacy_surround(grid, point, occ_grid, privacy_radius)
        PR_sum_known_ref += caculate_privacy_surround(grid, point, occ_grid_known, privacy_radius)
        if point.ca == 2:
            num_ca_ref += 1
        # print(point, pri_grid_known[point.x][point.y][point.z])
        if pri_grid[point.x][point.y][point.z] > 0 and occ_grid[point.x][point.y][point.z] == 0:
            num_intruder_notknown_ref += 1

        if pri_grid_known[point.x][point.y][point.z] > 0 and occ_grid_known[point.x][point.y][point.z] == 0:
            num_intruder_known_ref += 1

        # if  occ_grid[point.x][point.y][point.z] == 2 or occ_grid[point.x][point.y][point.z] == 3 or occ_grid[point.x][point.y][point.z] == 4 :
        #     num_should_avoid_intruder_ref += 1
        #
        # if occ_grid_known[point.x][point.y][point.z] == 2 or occ_grid_known[point.x][point.y][point.z] == 3 or occ_grid_known[point.x][point.y][point.z] == 4:
        #     num_cannot_avoid_intruder_ref += 1
    # print("\033[94m Fitness for reference path:\033[0m \n", len(trajectory_ref) - 1, sum_ref, num_ca_ref,
    #       num_intruder_ref)
    print("\033[94mFitness for preplanned path:\033[0m \n ", len(trajectory_plan) - 1, PR_sum_unknown_ref, PR_sum_known_ref,
          num_ca_ref,
          num_intruder_notknown_ref, num_intruder_known_ref)
    log.info("Online_Sensor_Config: Length of preplanned trajectory: %d" % (len(trajectory_ref) - 1))
    log.info("Online_Sensor_Config: Sum of privacy threat of replanned trajectory(occ_grid): %f" % PR_sum_unknown_ref)
    log.info("Online_Sensor_Config: Sum of privacy threat of replanned trajectory(occ_grid_known): %f" % PR_sum_known_ref)
    log.info("Online_Sensor_Config: Times of turning off camera of preplanned trajectory: %d" % num_ca_ref)
    # log.info("Online_Sensor_Config: Times of intrusion of preplanned trajectory: %d" % num_intruder_ref)
    log.info(
        "Online_Sensor_Config: Times of intrusion of preplanned trajectory(occ_grid): %d" % num_intruder_notknown_ref)
    log.info("Online_Sensor_Config: Times of intrusion of preplanned trajectory(occ_grid_known): %d" % num_intruder_known_ref)
    # log.info(
    #     "Online_Sensor_Config: Times of intrusion of preplanned trajectory(should avoid): %d" % num_should_avoid_intruder_ref)
    # log.info(
    #     "Online_Sensor_Config: Times of intrusion of preplanned trajectory(cannot avoid): %d" % num_cannot_avoid_intruder_ref)
    

    #print(path_grid2, sum)
    # print("---------------------------------")
    # print("The last plan is finished!")
    # print("The length of last plan is: ", len(trajectory_plan))
    # for m in range(len(trajectory_plan)):
    #     print("The No.", m, " step: ", trajectory_plan[m])
    end = time.time()
    dtime = end - starttime
    # print("程序运行时间：%.8s s" % dtime)
    print("\033[94m Replan times: \033[0m", replantime)
    log.info("Online_Sensor_Config: Replanning times: %d" % replantime)
    #grid_visualization(occ_grid, starting_point, end_point, trajectory_plan, trajectory_ref)

    occ_grid_known_name = os.getcwd() +"/data/"+"occ_grid_known" + str(iteration) + ".npy"
    np.save(file=occ_grid_known_name, arr=occ_grid_known)
    # np.save(file="occ_grid_known.npy", arr=occ_grid_known)
    # b = np.load(file="occ_grid_known.npy")
    # for m in range(grid_x):
    #     print("The value of x: ", m)
    #     print(b[m])

    plan_path = np.zeros((len(trajectory_plan), 4))
    for i in range(len(trajectory_plan)):
        plan_path[i] = [trajectory_plan[i].x, trajectory_plan[i].y, trajectory_plan[i].z, trajectory_plan[i].ca]

    plan_path_SC_name = os.getcwd() +"/data/"+"plan_path_SC" + str(iteration) + ".npy"
    np.save(file=plan_path_SC_name, arr=plan_path)
    # np.save(file="plan_path_SC.npy", arr=plan_path)
    # c = np.load(file="plan_path_SC.npy")
    # print(c, len(c))

    exploration_rate = 0

    for i in range(grid_x):
        for j in range(grid_y):
            for k in range(grid_z):
                if occ_grid_known[i][j][k]!=occ_grid[i][j][k]:
                    exploration_rate += 1
    exploration_rate =  1 -  exploration_rate/(grid_x * grid_y * grid_z * privacy_threshold)
    print("\033[94m exploration rate: \033[0m", exploration_rate)
    log.info("Online_Sensor_Config: Exploration rate: %f" % exploration_rate)

    return 



