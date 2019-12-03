#!/usr/bin/env python

import serial
from time import sleep
import rospy
from std_msgs.msg import String


rospy.init_node('Voice_point')

pub = rospy.Publisher('Shengyuan',String,queue_size=10)
r = rospy.Rate(1) # 10hz
def Voice_check():
	data ='' 
	angle =''
	serialPort = "/dev/ttyUSB0"
	baudRate   = 115200
	ser = serial.Serial(serialPort, baudRate, timeout=0.5) 

	while True:  
 	   #data =recv(ser) 
	    data = ser.readline() 
 	   #ser.write(data)
            if len(data)>50:
   	        angle=data[15:18]
	    pub.publish(angle)	

while not rospy.is_shutdown():
	Voice_check()
   
