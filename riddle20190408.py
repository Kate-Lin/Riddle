#!/usr/bin/env python
#Coded by Zhao Lei --2018.3.31
import os
import rospy
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String,Int16,Float32
import tf
import tf2_ros
from sound_play.libsoundplay import SoundClient
import sys
import freenect
import cv2
import numpy as np
from PIL import Image
import time
import math
from std_srvs.srv import Empty 
import actionlib
import actionlib_msgs.msg
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal, MoveBaseResult
from geometry_msgs.msg import Pose,Point,Quaternion,Twist
from beginner_tutorials.msg import PeoplePose
import shutil
from cv2 import cv as cv
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
import aiml
import serial
from time import sleep

mybot = aiml.Kernel()
response_publisher = rospy.Publisher('response',String,queue_size=10)



class TalkBack:
    def __init__(self, script_path):
        rospy.init_node("riddle")
        self.soundhandle = SoundClient()
        self.voice=rospy.get_param("~voice","voice_don_diphone")
        self.wavepath = rospy.get_param("~wavepath", script_path + "/../sounds")
        self.move_base_client = actionlib.SimpleActionClient('move_base',MoveBaseAction)
	#self.ori_pub=rospy.Publisher('/cmd_vel',Twist,queue_size=10)
        self.ori_msg=Twist()
	self.ori_msg.angular.x=0
	self.ori_msg.angular.y=0
	self.stop_msg=Twist()
        self.angle = 0.0
        self.lock = False
        self.location = 0
        rospy.init_node("sydw")
        self.pub=rospy.Publisher('/cmd_vel',Twist,queue_size=10)
        self.sub=rospy.Subscriber('/shengyuan',Float32,self.adjust)

	self.people_ori=0
	self.conf=0
	self.count=0
        self.load_aiml('startup.xml')
        #mybot.learn('0.aiml')

        self.sl("I want to play the riddle game!",1,2)
        #rospy.sleep(10)
        self.rot1=[0.000000,0.000000,0.775809,-0.630967]
    	self.rot=[0,0,0.775809,-0.630967]
        self.pos1=[9.549557,2.289376,0.000000]
        self.move(self.rot1,self.pos1,self.count_people)
        
        
#assistant functions
    def load_aiml(self,xml_file):
    	data_path = rospy.get_param("aiml_path")
        print data_path
        os.chdir(data_path)
        if os.path.isfile("standard.brn"):
            mybot.bootstrap(brainFile = "standard.brn")
        else:
            mybot.bootstrap(learnFiles = xml_file, commands = "load aiml b")
            mybot.saveBrain("standard.brn")

    def callback_listener(self,data):
	    input = data.data
	    response = mybot.respond(input)
	    input = response
	    data.data = mybot.respond(input)
            if(len(response)>0):
            	self.count=self.count+1
	    rospy.loginfo("I heard:: %s",data.data)
	    rospy.loginfo("I spoke:: %s",response)
            if(self.count>5 and len(response)>0):#The number of questions
                self.move(self.rot1,self.pos1)
                rospy.sleep(5)
	    response_publisher.publish(response)

 '''   def callback_Voice_point(self,angle):
            if angle.data == '':
                angle.data='0.0'
            angle.data=float(angle.data)
            if self.angle != angle.data:
                self.angle = angle.data
                self.rot[3]=math.cos(angle.data/360*math.pi)
                self.rot[2]=math.sin(angle.data/360*math.pi)
                self.rot1[3] = self.rot[3]*self.rot1[3]-self.rot[0]*self.rot1[0]-self.rot[1]*self.rot1[1]-self.rot[2]*self.rot1[2]
                self.rot1[0] = self.rot[3]*self.rot1[0]+self.rot[0]*self.rot1[3]+self.rot[1]*self.rot1[2]-self.rot[2]*self.rot1[1]
                self.rot1[1] = self.rot[3]*self.rot1[1]-self.rot[0]*self.rot1[2]+self.rot[1]*self.rot1[3]+self.rot[2]*self.rot1[0]
                self.rot1[2] = self.rot[3]*self.rot1[2]+self.rot[0]*self.rot1[1]-self.rot[1]*self.rot1[0]+self.rot[2]*self.rot1[3]
                self.rot1[3] = self.rot[3]*self.rot1[3]+self.rot[0]*self.rot1[0]+self.rot[1]*self.rot1[1]+self.rot[2]*self.rot1[2]
                self.rot1[0] = self.rot[3]*self.rot1[0]-self.rot[0]*self.rot1[3]-self.rot[1]*self.rot1[2]+self.rot[2]*self.rot1[1]
                self.rot1[1] = self.rot[3]*self.rot1[1]+self.rot[0]*self.rot1[2]-self.rot[1]*self.rot1[3]-self.rot[2]*self.rot1[0]
                self.rot1[2] = self.rot[3]*self.rot1[2]-self.rot[0]*self.rot1[1]+self.rot[1]*self.rot1[0]-self.rot[2]*self.rot1[3]
                quat = self.rot1[0]*self.rot1[0]+self.rot1[1]*self.rot1[1]+self.rot1[2]*self.rot1[2]+self.rot1[3]*self.rot1[3]
                self.rot1[0] = self.rot1[0] / quat
                self.rot1[1] = self.rot1[1] / quat
                self.rot1[2] = self.rot1[2] / quat
                self.rot1[3] = self.rot1[3] / quat
                print(self.rot1)
'''
            
    '''def voi_ori_callback(self,data):
    	    if(self.conf==0):
	        self.ori_pub.publish(self.stop_msg)    	    
    	    	return
	    #print data.data
	    people_ori=data.data
	    threshold=0.6
	    if(people_ori>threshold):
		self.ori_msg.angular.z=1.2
	    elif(people_ori<-threshold):
		self.ori_msg.angular.z=-1.2
	    else:
		self.ori_msg.angular.z=0
	    self.ori_pub.publish(self.ori_msg)
	    #rospy.sleep(1)
	    #self.ori_pub.publish(self.stop_msg)
	    #print self.people_ori
	    
    def conf_ori_callback(self,data):
    	if(data.data==1):
    		self.conf=1
    	else:
    		self.conf=0
        '''
    def get_video(self):
        self.array,_ = freenect.sync_get_video()
        self.array = cv2.cvtColor(self.array,cv2.COLOR_RGB2BGR)
        return self.array

    def sl(self,con,a=1,b=1):#speak_log
        rospy.sleep(a)
        rospy.loginfo(con)
        self.soundhandle.stopAll()
        self.soundhandle.say(con, self.voice)
        rospy.sleep(b)
#end of assistant functions
        
    def move(self,rot_origin,pos_origin,movecb=None):

        #rot = tf.transformations.quaternion_from_euler(rot_origin[0],rot_origin[1],rot_origin[2])
	    #rot=[self.quaternion_get_into_the_door[0],self.quaternion_get_into_the_door[1],self.quaternion_get_into_the_door[2],self.quaternion_get_into_the_door[3]]
        self.sl("I know",0,2)
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = 'map'
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = pos_origin[0]
        goal.target_pose.pose.position.y = pos_origin[1]
        goal.target_pose.pose.position.z = pos_origin[2]
        goal.target_pose.pose.orientation.x = rot_origin[0]
        goal.target_pose.pose.orientation.y = rot_origin[1]
        goal.target_pose.pose.orientation.z = rot_origin[2]
        goal.target_pose.pose.orientation.w = rot_origin[3]
	self.move_base_client.send_goal(goal,done_cb=movecb)

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
    
    #def count_people(self,state,result):#count number of people
    def count_people(self,result,state):#count number of people
        begin=time.time()#timer
        self.sl("Now I am goint to count the number of people",0,2)
        face_num_max=0
        i=0
        while (time.time()-begin<20.0):
            face_cascade=cv2.CascadeClassifier('/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml')
            scaling_factor =1.5
            frame = self.get_video()
            #depth_array=np.transpose(self.get_depth())
            frame=cv2.resize(frame,None,fx=scaling_factor,fy=scaling_factor,interpolation=cv2.INTER_AREA)
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            self.face_rects=face_cascade.detectMultiScale(gray,1.1,5)
            for(x,y,w,h) in self.face_rects:
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),1)
            if(len(self.face_rects)>face_num_max):
                face_num_max=len(self.face_rects)
                cv2.imwrite("/home/ros/robocup/src/beginner_tutorials/launch/photo/max_size_people+.jpg",frame)
            cv2.imshow("show",frame)
            i+=1#loop time
            
        print i
        self.sl("There are "+str(face_num_max)+" person",1,2)

        self.sl("Who wants to play riddle game with me? ",1,2)

        rospy.loginfo("Starting ROS AIML Server")
        rospy.Subscriber("chatter", String, self.callback_listener)
        #rospy.Subscriber("Shengyuan", String, self.callback_Voice_point)
        rospy.Subscriber("Shengyuan", String, self.adjust)
   

if __name__=="__main__":
    try:
        TalkBack(sys.path[0])
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Talkback class has not been constructed. Something is error.")
