#!/usr/bin/env python
'''testcmd_vel ROS Node'''
# -*- coding: UTF-8 -*-
# license removed for brevity
import rospy
import os
import sys
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
import math
cnt = 0
class sydw:
    def __init__(self, script_path):
        rospy.init_node("sydw")
        self.pub=rospy.Publisher('/cmd_vel',Twist,queue_size=10)
        self.sub=rospy.Subscriber('/shengyuan',Float32,self.adjust)
        self.angle = 0
        self.lock = False
        self.location = 0
    def adjust(self,data):
        if(data.data == self.location):
            return 
        self.location = data.data
        if(data.data>0):
            fabs = data.data
        else:
            fabs = -data.data
        rate = rospy.Rate(3)
        if(self.lock == True):
            self.lock = False
        else:
            self.lock = True
        sublock = self.lock
        global cnt
        cnt += 1
        pp = cnt
        while(self.lock == sublock):    #
            msg = Twist()
            if(data.data > self.angle):
                value = 8
            elif(data.data < self.angle):
                value = -8
            else:
                value = 0
            msg.angular.z=float(value)
            self.angle += value
            self.pub.publish(msg)
            rospy.loginfo(self.angle)
            rate.sleep()
            if(math.fabs((self.angle - fabs))<=9.3):
                break
        self.angle = 0
if __name__=="__main__":
    try:
        sydw(sys.path[0])
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("sydw class has not been constructed. Something is error.")
