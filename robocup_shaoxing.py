#!/usr/bin/env python
#!coding=utf-8
#2018.8.2 不完整

import rospy
from collections import  deque
from roslib import message
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import Twist
from math import copysign
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from move_base_msgs.msg import MoveBaseActionResult
import tf
import tf2_ros
from sound_play.libsoundplay import SoundClient
import sys
import re
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal, MoveBaseResult
import os
import freenect
import cv2
import numpy as np
from PIL import Image
import time
import math
from std_srvs.srv import Empty
import actionlib
import actionlib_msgs.msg
from geometry_msgs.msg import Pose,Point,Quaternion
from beginner_tutorials.msg import PeoplePose
import shutil
from cv2 import cv as cv
from cv_bridge import CvBridge, CvBridgeError


class TalkBack:
    def __init__(self, script_path):
        rospy.init_node('robocup_xf_gpsr')

        rospy.on_shutdown(self.cleanup)

        self.rate = rospy.get_param("~rate", 2)
        r = rospy.Rate(self.rate)

        #set the default TTSvoice to use
        self.voice = rospy.get_param("~voice", "voice_cmu_us_clb_arctic_clunits")

        #Set the wav file path if used
        self.wavepath = rospy.get_param("~wavepath", script_path + "/../sounds")

        #Create the sound client object
        self.soundhandle = SoundClient()

        #Wait a moment to let the client connect to the sound_play server
        rospy.sleep(1)

        #Make sure any lingering sound_play process are stopped .
        self.soundhandle.stopAll()

        self.gpsr_pub = rospy.Publisher('move_base_simple/goal', PoseStamped, queue_size=5)


	

        self.soundhandle.playWave(self.wavepath + "/R2D2a.wav")
        rospy.sleep(2)
        self.soundhandle.say("Ready", self.voice)
	


        rospy.loginfo("Say one of the navigation commands ...")
	print '...  ... '

        #self.voice_vel_pub = rospy.Publisher("address", String, queue_size = 5)
        #rospy.Subscriber('/recognizer/output', String, self.talkback )           	
        #########********
        #send response text to xf_tts_topic, and make it to wave 
        self.voice_vel_pub = rospy.Publisher("/voice/xf_tts_topic", String, queue_size = 5)  
        #receive text from tuling_nlu_topic which is recognized from wave to text    
        rospy.Subscriber('/xfspeech', String, self.talkback )       


        rospy.Subscriber('/move_base/result', MoveBaseActionResult, self.base_status_callback)
        
        #face recognizer
        #rospy.Subscriber('/recognizer/output', String, self.talkback) #Subscriber for the recognizer, and call the callback function
	self.voice_vel_pub = rospy.Publisher('who_voice', String , queue_size=5)
	self.point_pub = rospy.Publisher('move_base_simple/goal', PoseStamped, queue_size=5)
	self.peopleposepub = rospy.Publisher("people_pose_info",PeoplePose,queue_size=1)
        self.follow_select_pub = rospy.Publisher("follow_select_cmd",String,queue_size=5)
	self.voice_shell=rospy.Publisher("follow_select",String,queue_size=1)
	self.begin=time.time()

        ###########################
        self.exit_point = PoseStamped()
        ###########################

	self.posePosition('door')
	rospy.sleep(5)
	self.base_sts = 0
	
	

	self.keys_command = {'take the coffee from the cooking table and bring it to me':'Do you need me to take the coffee for you?',
			     'go to the living room and tell Tom what is your name':'Do you send me to living room?',
			     'go to find the milk in the kitchen and bring it to Merry who is in the bedroom':'Sir, you need me to take the milk to Merry?'}
			    
	self.keys_movebase = {'kitchen':'chu_fang',
			      'dining':'can_ting',
			      'living':'ke_ting',
			      'bedroom':'wo_shi',
			      'cooking':'can_zhuo',
			      'book':'shu_jia',
			      'back':'go back here'}
			      
				    
	self.answers_to_questions = {'capital':['capital','the capital','capital of china'],
				     'island':['island','world','word','biggest island'],
			   	     'what_season':['what season','it is now','what season it is now'],
			  	     'hours':['hours','hours','ours',' our','many hours','a day','in a day'],
			 	     'season_year':['year','many season','are there','one year'],
			 	     'seconds':['seconds','second','minute','one minute'],
			 	     'province':['province','biggest province','province of china'],
				     'area':['area','large','how large','the area','area of china'],
				     'children':['children','queen','Queen','Victoria','have','did','many children'],
				     'president':['who','first','president','usa','USA','the first', 'first president'],
				     'animal':['animal','national',"china's",'national animal'],
				     'new_york':['New York','former','name of New York','new york'],
				     
				    }


	self.keys_command1 = ['take', 'Take', 'go to', 'bring', 'find', 'tell', 'answer', 'question', 'coffee', 'milk', 'kitchen', 'living room','dining room','bedroom','follow']

	
### ///

	self.l_object=['drinks', 'coffee', 'milk', 'juice', 'red bull', 'redbull', 'sprite', 'tea', 'food', 'biscuit', 'snacks', 'chips', 'cleaning stuff', 'roll paper', 'toothpaste']

	self.l_location1=['kitchen', 'livingroom', 'living room', 'bedroom', 'bed room', 'dining room', 'diningroom', 'book cabinet', 'dining table', 'diningtable', 'tv table', 'TV table', 'dresser']

	self.l_vbdeliver=['bring', 'carry', 'deliver', 'take']

	self.l_name=['Gray','David','Daniel','Jack','Jenny','Michael','Lucy','Peter','Tom','Jordan', 'tom', 'green', 'jack', 'kevin', 'alice', 'james','david','daniel','jenny','michael', 'lucy', 'peter','jordan', 'Tom', 'Green', 'Kevin', 'Alice', 'James', 'David', 'Daniel', 'Jack', 'Jenny', 'Michael', 'Lucy', 'Peter', 'Jordan']

	self.l_location2=['kitchen', 'livingroom', 'living room', 'bedroom', 'bed room', 'dining room', 'diningroom', 'book cabinet', 'dining table', 'diningtable', 'tv table', 'TV table', 'dresser']

	#navigate to --> navigate 
	self.l_go=['go to', 'navigate to', 'reach', 'get into', 'rich', 'bring', 'give', 'get', 'grasp', 'take', 'pick up']

	#look for-->look, search for --> search
	self.l_find=['find', 'search for']

	self.l_talk=['speak', 'tell', 'answer']

	#l_question=['your name','the name of your team','the time','what time is it','tell the date','what day is today','what day is tomorrow']
	self.l_question=['your name','team','the time','what time','date','today','tomorrow']

	# question string is long, so we can translate it into dictionary, ying she
	self.d_question={'your name':'my name','team':'the name of my team','the time':'the time','what time':'what time is it','date':'the date','today':'what day is today','tomorrow':'what day is tomorrow'}

	self.d_prep = {'in':'in',
		       'at':'at'}

	self.d_object={'milk':['milk','that milk','the milk'],
		       'tea':['tea'],
		       'chips':['chips','trips'],
		       'biscuit':['cute',"he's cute",'this cute','coat','cold','this coat','biscuit','piss code','biss code','code','kiss'],
		       'cola':['cola','caller','colder','coller','corner','color','colour'],
		       'juice':['juice'],
		       'roll paper':['paper'],
		       'red bull':['red bull','red ball','red','bull','ball'],
		       'toothpaste':['to spend','To spend','spend','tooth','two space'],
	   	       'sprite':['spread','sprite'],
		       'coffee':['coffee'], 
		       'cake':['cake','Cake'],
		       'bread':['bread','grap','grab','Grab','bread','Bread'],
		       #'Noodles':['noodle','noodles'],
		       'water':['water'],
		       #'paper':['paper','Paper'],
		       'PIE':['PIE','pie'],
		       'tea':['Tea','tea'],
		       'biscuit':['biscuit','Biscuit','basic','basket'],
		       'cheap':['Cheap','cheap'],
		       'soap':['soap','Soap','soup','self'],
		       'shampoo':['shampoo','Shampoo'],
		       #'Milk tea':['Milk tea','Milk','tea','milk'],
		       'cloth':['cloth','Cloth','clothes'],
		       'sponge':['sponge','Sponge'],
		       'pringles':['pringles','Pringles'],
		       'cookies':['Cookies','cookies'],
		       'apple':['apple','Apple'],
		       'melon':['melon','Melon'],
		       'banana':['banana','Banana'],
		       'pear':['pear','Pear'],
		       'peach':['peach','Peach'],
		       'pasta':['pasta','Pasta'],
		       'noodles':['noodles','Noodles'],
		       'tuna fish':['tuna fish','Tuna fish','Tuna','tuna'],
		       'pickles':['pickles','Pickles'],
		       'choco flakes':['choco flakes','Choco flakes','Choco','choco','flakes','Flakes'],
		       'muesli':['Muesli','muesli'],
		       'beer':['beer','Beer'],
		       'coke':['coke','Coke'],
		       'water':['water','Water'],
		       'tea spoon':['tea spoon','Tea spoon'],
		       'spoon':['spoon','Spoon'],
		       'fork':['fork','Fork'],
		       'knife':['knife','Knife'],
		       'napkin':['napkin','Napkin'],
		       'big dish':['Big dish','big dish'],
		       'small dish':['small dish','Small dish'],
		       'bowl':['bowl','Bowl'],
		       'glass':['glass','Glass'],
		       'mug':['mug','Mug'],
		       'tray':['tray','Tray'],
		       'box':['box','Box'],
		       'bag':['bag','Bag'],
		       'sprite':['sprite','Sprite'] }

	self.d_location={'kitchen':['kitchen'],
	   		 'living room':['living','leaving'],
	   		 'bedroom':['bedroom','bad','bed room','bad room'],
	  		 'dining room':['dining'],
			 'dining table':['dining table','ing table','dining t'],
	   		 'TV table':['TV','tv','tv table','TV table'],
	   		 'dresser':['dresser'],
	   		 'book cabinet':['book','cabinet','net','book cabinet'],
	   		 'corridor':['corridor','Corridor'],
	   		 'bathroom':['bathroom','Bathroom'] }

	self.d_find={'find':['find','Find','found','Found','fine','Fine'],
		     'look for':['look','Look'],
		     'search for':['search','such','search for','such for','Search','Such','Search for'],
		     'locate':['locate']}

	self.d_go = {'go to':['go to','Go to'],
		     'navigate to':['navigate to','gate','guide','navi','navigate','Navigate to','Navigate'],
		     'reach':['reach','rich','Reach','Rich'],
		     'get into':['get into','into','get','Get','Get into'] }

	self.d_name={'Gray':['Gray','gray','great','Great'], 			                      			 
		     'David':['David','david'], 
		     'Jack':['Jack','jack'],
		'Michael':['Michael','michael'],
		'Lucy':['Lucy', 'lucy'],
		'Peter':['Peter', 'peter'],
		'Jordan':['Jordan','jordan'],
		'a person':['person'],
		'Tom':['Tom','tom','come','Come','town'],
		'Angel':['Angel','angel'],
		'Paul':['Paul','paul','part','play','Part','poor','power','paw'],
		'Jamie':['jamie','Jamie','Janney','janney','jimmy','jenny'],
		'Green':['Green','green'],
		'Fisher':['Fisher','fisher','fish'],
		'Kevin':['Kevin','kevin','keep','Keep','given'],
		'Shirley':['Shirley','shirley'],
		'Tracy':['Tracy','tracy','trees'],
		'Robin':['Robin','robin'],
		'John':['John','john'],
		'Morgan':['Morgan','morgan'],
		'Taylor':['Taylor','taylor'],
		'Hayden':['Hayden','hayden'],
		'Peyton':['Peyton','peyton'],
		'Alex':['Alex','alex'] }



### ///

 #22222222222222222222

	#global
	self.flag=0
	self.special_case = ' '
	self.point1=' '
	self.point2=' '
	self.com_type = 0
	self.person_name=' '
	self.com1 = ' '
	self.com_y = ' '   #actually, they don't matter !
	self.place = ' '
	self.base_sts = ' '
	self.r5=[' ',' ']
	self.r6=[' ',' ']
	self.r7=[' ',' ']
	self.action =' '
	#self.name=[]
        self.name=[[0 for i in range(2)] for i in range(6)]
	self.position=[[0 for i in range(3)] for i in range(6)]
	self.flag=0
	self.flag_2=0
	self.id=0
	self.na=None
	self.array=None
	self.frame =None
	self.face_rects=None
	self.j = 0
	self.num=0
	self.id_name=0
	self.pro=None
	self.flag_face_detect=0
	self.a=0
	self.ob_name=' '
	self.r_final=' '
##
	self.m1=' '
	self.m2=' '
	self.m3=' '
        self.m5=' '
        self.ans=' '
	#self.base_sts = 3	

########################################################				    	
#    def get_command1(self, data):
#	if data != ('yes' or 'no'):
#            return data
#	else:
#	    return '... ...'

    def get_command1(self, data):
	kms = self.keys_movebase.keys()
	#r44 = re.findall(r"\w+",data)
	for i in range(len(kms)):
	    if kms[i] in data:
        	return data
	    else:
		return self.com1

    #because of cann't list all the possible strings which 
    #can show up in the contest, so define this function !   222222222222222
    def get_command11(self, data):
	count = 0
	for i in range(len(self.keys_command1)):
	    #print i
	    #print self.keys_command1[i]
	    if self.keys_command1[i] in data:
		  count = count + 1
	    else:
		count = count
	if count > 0:
	    return data
	else:
	    return self.com1 
	    
    def get_command12(self,data):
        if ('Yes.' or 'yes' or 'No.' or 'no') in data:
            return self.com1
        else:
            return data

    def get_command2(self, data):
        return data
	#else:
	 #   return self.com_y


    def diff_command(self, data):
	#if data == ('yes' or 'no'):
	if len(data) <=6:                  ###########<===============
	    return data
	else:
	    return '... ...'


    def get_command3(self, data):
        # Attempt to match the recognized word or phrase to the 
        # keywords_to_command dictionary and return the appropriate
	for (command3, keywords) in self.answers_to_questions.iteritems():        
	    for word in keywords:
                if data.find(word) > -1:
                     return command3


##############################
#    def base_status_callback(self, msg):
#    	self.base_status = msg.status.status
#	self.base_sts = self.base_status

###############################################################


    #self.ks2 = keys_movebase.keys()
    
    #command_to_base response, to the point one
    def analyzeMove(self, t2):
        print 13
	#print 'analy'
	r4 = re.findall(r"\w+",t2)
	print r4
        for i in range(len(r4)):
	     if r4[i] in self.ks4:
		print self.ks4
		self.r5[0]=r4[i]
		#print 2
		print self.r5[0]
		break
	if (self.r5[0] != ' '):
	        print 14        
	        for i in range(len(r4)):
	            if r4[i] in self.ks2:
		          #print r4[i]
		          #print ''
		          self.r6[0]=r4[i]
		          print self.keys_movebase[r4[i]]
		          self.point1=r4[i]
		          print 10
		          print self.point1
		          self.posePosition(r4[i])        # 3333333333333333333
		          break
        else:
                print 15
                for i in range(len(r4)):
                    #print r4
                    #print i
	            if r4[i] in self.ks2:
		       #print r4[i]
		       #print ''
		       print self.keys_movebase[r4[i]]
		       self.point1=r4[i]
		       print 11
		       print self.point1
		       self.r_final=r4[i]+'_table'
		       print self.r_final
		       self.posePosition(r4[i])        # 3333333333333333333
		       break
    #command_to_base response, to the point two
    def analyzeMove2(self, t2):
	#print 'analy2'
	r4 = re.findall(r"\w+",t2)
	
	''' #何舟-这段话没用
		i = len(r4)-1
		while(i>=0):
		    if r4[i] in self.ks4:
			print self.ks4
			self.r7[0]=r4[i]
			print self.r7[0]       # 3333333333333333333
			break
		    else:
			i = i-1
	''' #hezhou
	i = len(r4)-1
	while(i>=0):
	    if r4[i] in self.ks2:
		if 'me' in r4:          #何舟
		    r4[i]='back'        #何舟
		print self.keys_movebase[r4[i]]
		self.point2=r4[i]
		self.posePosition(r4[i])       # 3333333333333333333
		break
	    else:
		i = i-1

    def twoIfString(self, t2):
	count2 = 0
	for i in range(len(self.keys_command1)):
	    #print i
	    #print self.keys_command1[i]
	    if self.keys_command1[i] in t2:
		  count2 = count2 + 1
	    else:
		count2 = count2
	return count2


### / / / / / 　　运送　　／／／／／／／
    def understand_1(self, t1):
        c1='Do you need me'
	flag_1=0
        if ('grasp' in t1) or ('bring' in t1) or ('give' in t1) or ('Take' in t1) or ('Get' in t1) or ('take' in t1) or ('bring' in t1) or ('pick up' in t1):
            self.com_type = 1
            print 100
            if ('me' in t1) and ('and' not in t1):
                print 218
                c1=c1+' give you the '
            elif (('me' in t1) and ('and' in t1)) or ((self.fun_find_name(t1)) and ('and' in t1)):
                print 304
                c1=c1+' take the '
            elif (self.fun_find_name(t1)) and ('and' not in t1):
                print 102
                name1=self.fun_find_name(t1)
                c1=c1+' give to '+name1+' at the '
                for (locat0,valu_locat0) in self.d_location.iteritems():
                    for word in valu_locat0:
	                if t1[:35].find(word)>-1:
	                   c1=c1+locat0+' the '
	                   print 103
	                   self.special_case = locat0
                           break
            else:
                print 300
                c1=c1+' take the '
            for (obj,valu_obj) in self.d_object.iteritems():
	        for word in valu_obj:
                    if t1.find(word)>-1:
                        c1=c1+obj
		        break
                
	    for (locat,valu_locat) in self.d_location.iteritems():
		
		if (flag_1 ==1):
		    break
                for word in valu_locat:
	            if t1.find(word)>-1:
	                c1=c1+' from the '+locat
	                self.special_case = ' '
			flag_1=1
                        break
            if ('and' in t1): 
               if ('me' not in t1) and (self.fun_find_name(t1) is None):
                  c1=c1+' and go back '        
               elif ('me' not in t1) and (self.fun_find_name(t1)):
                  c1=c1+' and give it to '+self.fun_find_name(t1)+' at the '     
               else:
                  c1=c1+' and give it to you'
               for (locat2,valu_locat2) in self.d_location.iteritems():
                   for word in valu_locat2:
	               if t1[-15:].find(word)>-1:
	                  c1=c1+locat2
	                  break
        return c1
        
    def fun_find_name(self,t1):
        for (name,value_name) in self.d_name.iteritems():
            for word in value_name:
                if t1.find(word)>-1:
                    return name
                    break


###


###／／／／／／／／　　找人　　／／／／／／／／／／
    def understand_2(self, t2):
        c2='Do you need me'
        if ('tell' in t2[:10]):
           self.com_type = 2
           c2=c2+' tell you the name of the person '+self.func_prep(t2)+' the '
           for (locat,valu_locat) in self.d_location.iteritems():
	        for word in valu_locat:
                    if t2[-10:].find(word)>-1:
                       c2=c2+locat+' '
		       break
        return c2

    def func_prep(self, t2):
        for (prep,valu_prep) in self.d_prep.iteritems():
    	    for word in valu_prep:
                if t2[-20:].find(word)>-1:
                    return prep
		    break
        
        
		    	    
##
    def understand_5(self, t5):
	c5='Do you need me'
        if ('answer' in t5):
            self.com_type = 5
            for (name,valu_name) in self.d_name.iteritems():
                for word in valu_name:
                    if t5.find(word)>-1:
                       c5=c5+' '+'find '+name
            for (locat,valu_locat) in self.d_location.iteritems():
                for word in valu_locat:
                    if t5.find(word)>-1:
                       c5=c5+' '+'in the '+locat+' and answer a question'
        elif ('time' in t5):
             self.com_type = 5
             self.flag = 7
             for (name,valu_name) in self.d_name.iteritems():
                 for word in valu_name:
                     if t5.find(word)>-1:
                        c5=c5+' '+'find '+name
             for (locat,valu_locat) in self.d_location.iteritems():
                 for word in valu_locat:
                     if t5.find(word)>-1:
                        c5=c5+' '+'in the '+locat+' and speak the time'
        elif ('follow' in t5):
             self.com_type = 5
             for (name,valu_name) in self.d_name.iteritems():
                 for word in valu_name:
                     if t5.find(word)>-1:
                        c5=c5+' '+'find '+name
             for (locate,valu_locate) in self.d_location.iteritems():
                 for word in valu_locate:
                     if t5.find(word)>-1:
                        c5=c5+' '+'in the '+locate+' and follow'
        elif ('team' in t5):
             self.com_type = 5
             self.flag = 8
             for (name,valu_name) in self.d_name.iteritems():
                 for word in valu_name:
                     if t5.find(word)>-1:
                        c5=c5+' '+'find '+name
             for (locate,valu_locate) in self.d_location.iteritems():
                 for word in valu_locate:
                     if t5.find(word)>-1:
                        c5=c5+' '+'in the '+locate+' and say our team'
		        break
    
 
	return c5

#####／／／／／／／　　找物　　／／／／／／／
    def understand_3(self, t3):
        c3='Do you need me'
        if (('look' in t3) and ('answer' not in t3)):           #去掉了find，加入了后面三个understand5的词语
            self.com_type = 3
	    print 3
            for (find,valu_find) in self.d_find.iteritems():
                for word in valu_find:
                    if t3.find(word)>-1:
                       c3=c3+' '+find+' the '
		       break

            for (obj,valu_obj) in self.d_object.iteritems():
                for word in valu_obj:
                    if t3.find(word)>-1:      ################
                        c3=c3+obj+' in the '
		        break

            for (locat,valu_locat) in self.d_location.iteritems():
                for word in valu_locat:
                    if (t3.find(word)>-1) :      ################
                        c3=c3+locat
		        break
	    if 'back' in t3:
		c3=c3+' and go back'
		self.flag_2=1	    
        return c3
        
        
######／／／／／／　　指引　　／／／／／／／／／／





######／／／／／／　　跟人　　／／／／／／／／／／







### ##
    def yesToBase(self, c, command_full):
        if (c == ' Yes.' or c == 'yes'):
            print 'OK. I will. '
            s3 = 'OK. I will. '
	    self.base_sts = 0
            self.soundhandle.say(s3)
            if (self.com_type == 1):
                print 1
                if (('and' not in command_full) and ('from the' in command_full)):
                    self.analyzeMove2(command_full)
                    #until the robot arrive at the goal point  # . .......
                    rospy.set_param('inflation_radius', 0.05)
                    while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have reached the point.'
                             self.soundhandle.say('I have reached the point.')
                             break
                    self.analyzeMove(command_full)
                    rospy.set_param('inflation_radius', 0.05)
                    while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have reached the point.'
                             self.soundhandle.say('I have reached the point.')
                             break
                else:
		    if ('bedroom' in command_full):
			  self.posePosition('zhongjiandian')
			  print 49
			  while True:
                               #print 9
                               if self.base_sts !=3:
                                  pass
                               else:
                                  print 'I have reached the point.'
				  self.base_sts=0     #何舟
                                  break
                    print 5
                    self.analyzeMove(command_full)
                    print 6
                    rospy.set_param('inflation_radius', 0.05)
                    print 7
                    if (self.point1 == ' ' and 'me' in command_full):
                          print 8
                          print 'I have reached the point.'
                          self.soundhandle.say('I have reached the point.')
                    else:
                         while True:
                               #print 9
                               if self.base_sts !=3:
                                  pass
                               else:
                                  print 'I have reached the point.'
                                  self.soundhandle.say('I have reached the point.')
				  rospy.sleep(3)      #何舟
				  self.base_sts=0     #何舟
                                  break
                    if (self.point1 == ' '):
                        pass 
                    elif (self.r5[0] !=' '):
                        if ('and' not in command_full):
                            self.findperson()
                        elif ('me' in command_full):
                            self.posePosition('back')
                            while True:
                                   if self.base_sts !=3:
                                      pass
                                   else:
                                      print 'I have reached the point.'
                                      self.soundhandle.say('I have reached the point.')
                                      break
                        else:
                            self.analyzeMove2(command_full)
			    print 491
                            rospy.set_param('inflation_radius', 0.05)
                            while True:
                                   if self.base_sts !=3:
                                      pass
                                   else:
                                      print 'I have reached the point.'
                                      self.soundhandle.say('I have reached the point.')
                                      break
                            self.findperson()                            
                    elif ('and' in command_full):
			  if ('bedroom' in command_full):
			  	self.posePosition('zhongjiandian')
			  	print 49
			  	while True:
                               		if self.base_sts !=3:
                                  		pass
                               		else:
                                  		print 'I have reached the point.'
				  		self.base_sts=0     #何舟
                                  		break
                          self.analyzeMove2(command_full)
			  print 49
                          rospy.set_param('inflation_radius', 0.05)
                          while True:
                                if self.base_sts !=3:
                                   pass
                                else:
                                   print 'I have reached the point.'
                                   self.soundhandle.say('I have reached the point.')
                                   break
                    else:
                          self.posePosition('back')
                          while True:
                                   if self.base_sts !=3:
                                      pass
                                   else:
                                      print 'I have come back.'
                                      self.soundhandle.say('I have come back.')
                                      break  
                    
            elif (self.com_type == 2):
                  print 2
                  self.analyzeMove(command_full)
                  rospy.set_param('inflation_radius', 0.05)
                  while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have reached the point.'
                             self.soundhandle.say('I have reached the point.')
                             break
                  self.findperson()
                  if (self.position[0][0]!=0) or (self.position[0][1] != 0):
                     for i in range(1,6):
                          self.askname(c)
                          break
                  else:
                     self.person_name = 'Tom'
                  if (self.person_name != None):             
                      print 'I have remembered you.'
                      self.soundhandle.say('I have remembered you.')
                  self.posePosition('back')
                  rospy.set_param('inflation_radius', 0.05)
                  while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have come back.The name of the person is '+self.person_name
                             self.soundhandle.say('I have come back.The name of the person is '+self.person_name)
                             break
                  self.posePosition('back')
                  while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have come back.'
                             self.soundhandle.say('I have come back.')
                             break
                             
            elif (self.com_type == 3):
                  print 4
		  if ('bedroom' in command_full):
			  self.posePosition('zhongjiandian')
			  print 49
			  while True:
                               #print 9
                               if self.base_sts !=3:
                                  pass
                               else:
                                  print 'I have reached the point.'
				  self.base_sts=0     #何舟
                                  break
                  self.analyzeMove(command_full)
                  rospy.set_param('inflation_radius', 0.05)
                  while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have reached the point.'
                             self.soundhandle.say('I have reached the point.')
                             rospy.sleep(3)
			     self.base_sts=0       #何舟
			     break
		  self.posePosition(self.r_final)
		  print self.r_final
                  while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have reached the point.'
                             self.soundhandle.say('I have reached the point.')
                             rospy.sleep(3)
			     self.base_sts=0       #何舟
			     for (obj,valu_obj) in self.d_object.iteritems():
				for word in valu_obj:
				    if command_full.find(word)>-1:      ##########
				        ob_name=obj
					break
			     if(ob_name=='cola'):
			     	self.find_object_with_kinect(np.array([120,59,85]),np.array([220,255,211]),ob_name)
			     elif(ob_name=='chips'):
			     	self.find_object_with_kinect(np.array([123,125,23]),np.array([175,255,143]),ob_name)
			     elif(ob_name=='water'):
			     	self.find_object_with_kinect(np.array([156,72,53]),np.array([209,255,230]),ob_name)
			     elif(ob_name=='milk'):
			     	self.find_object_with_kinect(np.array([17,58,102]),np.array([204,215,199]),ob_name)
			     elif(ob_name=='coffee'):
			     	self.find_object_with_kinect(np.array([3,86,28]),np.array([116,206,184]),ob_name)
			     elif(ob_name=='soap'):
			     	self.find_object_with_kinect(np.array([17,21,22]),np.array([158,189,85]),ob_name)
			     elif(ob_name=='toothpaste'):
			     	self.find_object_with_kinect(np.array([80,50,84]),np.array([167,179,220]),ob_name)
			     elif(ob_name=='biscuit'):
			     	self.find_object_with_kinect(np.array([158,67,87]),np.array([197,255,248]),ob_name)
			     elif(ob_name=='soap'):
			     	self.find_object_with_kinect(np.array([17,21,22]),np.array([158,189,85]),ob_name)
			     elif(ob_name=='noodles'):
			     	self.find_object_with_kinect(np.array([38,15,5]),np.array([104,194,178]),ob_name)
			     elif(ob_name=='cake'):
			     	self.find_object_with_kinect(np.array([161,69,34]),np.array([184,219,148]),ob_name)

                             print 'I have found it.'
                             self.soundhandle.say('I have found it.')
                             break
		  if (self.flag_2==1):       #flag_2判断是否要back 何舟
			  if ('bedroom' in command_full):
			  	self.posePosition('zhongjiandian')
			  	print 49
			  	while True:
                               		if self.base_sts !=3:
                                  		pass
                               		else:
                                  		print 'I have reached the point.'
				  		self.base_sts=0     #何舟
                                  		break
		          self.posePosition('back')
		          while True:
		                  if self.base_sts !=3:
		                     pass
		                  else:
		                     print 'I have come back.'
		                     self.soundhandle.say('I have come back.')
		                     break
            elif (self.com_type == 5):
		  if ('bedroom' in command_full):
			  self.posePosition('zhongjiandian')
			  print 49
			  while True:
                               #print 9
                               if self.base_sts !=3:
                                  pass
                               else:
                                  print 'I have reached the point.'
				  self.base_sts=0     #何舟
                                  break
                  self.analyzeMove(command_full)
                  rospy.set_param('inflation_radius', 0.05)
                  while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have reached the point.'
                             self.soundhandle.say('I have reached the point.')
                             rospy.sleep(3)
                             break
                  self.findperson()
                  if (self.flag == 7):
                      print 'The time is .'
                      self.soundhandle.say('The time is .')
                  elif (self.flag == 8):
                        print "Our team's name is strive team"
                        self.soundhandle.say("Our team's name is strive team.")
            else:
                  print 5
                  print 'error!!!  error!!!  error!!!'
                  self.soundhandle.say('error error error')
                  self.posePosition('back')
                  while True:
                          if self.base_sts !=3:
                             pass
                          else:
                             print 'I have come back.'
                             self.soundhandle.say('I have come back.')
                             break
                  
            
        elif (c == 'No.' or c == 'no'):
            s2 = "I don't understand1. Please say again. "
	    self.soundhandle.say(s2)
	    print s2
	    print ''
	    self.com1 = ' '
	    self.m1=' '
	    self.m2=' '
	    self.m3=' '
            self.m5=' '
        else:
            s2 = "I don't understand2. Please say again. "
	    self.soundhandle.say(s2)
	    print s2
	    print ''
            print '...'


    def answerQuestion(self,tt):
        if tt == 'capital':
	    self.ans='The capital of China is Beijing.'
        if tt == 'island':
	    self.ans='Greenland.'
        if tt == 'what_season':
	    self.ans='It is spring now.'
        if tt == 'hours':
	    self.ans='There are twenty four hours in a day.'
        if tt == 'season_year':
	    self.ans='Four seasons.'
        if tt == 'seconds':
	    self.ans='Sixty seconds.'
        if tt == 'province':
	    self.ans='Xinjiang is the biggest province of China.'
        if tt == 'area':
	    self.ans='Nine million and six hundred thousand saquare kilometers.'
        if tt == 'children':
	    self.ans='Nine children.'
        if tt == 'president':
	    self.ans='George Washington.'
        if tt == 'animal':
	    self.ans='It is Panda.'
        if tt == 'new_york':
	    self.ans='It was New Amsterdam.'
	
	return self.ans




    #answers&questions_function
    def answersToQuestions(self, t4):
	r4 = re.findall(r"\w+",t4)
	for i in range(len(self.ks3)):
	    k0 = self.ks3[i]
	    r3 = re.findall(r"\w+",k0)
	    ret3 = list(set(r3) ^ set(r4))
	    if len(ret3) <= len(r3)/4 + 1:           ########### raise the rate of error_permission
		print self.answers_to_questions[k0]
		self.soundhandle.say(self.answers_to_questions[k0])     ##########test publish ##


    #analyze if the question is empty
    def questionEmpty(self, t5):
	r51 = re.findall(r"\w+", t5)
	if ('what' in t5) or ('how' in t5):
	    return True


    ###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #two questionEmpty function, choose one, either is OK ! 
    def questionEmpty2(self, t5):
	r51 = re.findall(r"\w+",t5)
	for i in range(len(self.ks3)):
	    k5 = self.ks3[i]
	    r52 = re.findall(r"\w+",k5)
	    ret5 = list(set(r52) ^ set(r51))
	    if len(ret5) <= len(r52)/4 + 1:           
		return True

    def posePosition(self, place):
        if place == 'kitchen':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = -4.772365
	    self.exit_point.pose.position.y = 7.466029
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = 0.945463
	    self.exit_point.pose.orientation.w = 0.325730
	    self.gpsr_pub.publish(self.exit_point)
	    	
	if place == 'dining':
	    #print 'dining '
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = 0.285942
	    self.exit_point.pose.position.y = 3.316015
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = 0.938682
	    self.exit_point.pose.orientation.w = 0.344785
	    self.gpsr_pub.publish(self.exit_point)
	    	
	if place == 'living':      #3333333333333333
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = -1.957119
	    self.exit_point.pose.position.y = 10.725082
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = -0.337172
	    self.exit_point.pose.orientation.w = 0.941443
	    self.gpsr_pub.publish(self.exit_point)
	    #print 'living room publish base_controal'
	    	
        if place == 'bedroom':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = 2.881929
	    self.exit_point.pose.position.y = 6.453794
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = -0.327067
	    self.exit_point.pose.orientation.w = 0.945001
	    self.gpsr_pub.publish(self.exit_point)

	if place == 'cooking':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    	
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.15)
	    
	    self.exit_point.pose.position.x = -5.7
	    self.exit_point.pose.position.y = 3.3
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = self.q[0]
	    self.exit_point.pose.orientation.y = self.q[1]
	    self.exit_point.pose.orientation.z = self.q[2]
	    self.exit_point.pose.orientation.w = self.q[3]
	    self.gpsr_pub.publish(self.exit_point)
	    #print 'cooking publish base_controal'

	if place == 'back':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    	
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.15)
	    
	    self.exit_point.pose.position.x = 1.420880
	    self.exit_point.pose.position.y = 1.856649
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = self.q[0]
	    self.exit_point.pose.orientation.y = self.q[1]
	    self.exit_point.pose.orientation.z = self.q[2]
	    self.exit_point.pose.orientation.w = self.q[3]
	    self.gpsr_pub.publish(self.exit_point)

	
	if place == 'backforward':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    	
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.15)
	    
	    self.exit_point.pose.position.x = 0
	    self.exit_point.pose.position.y = 0
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = self.q[0]
	    self.exit_point.pose.orientation.y = self.q[1]
	    self.exit_point.pose.orientation.z = self.q[2]
	    self.exit_point.pose.orientation.w = self.q[3]
	    self.gpsr_pub.publish(self.exit_point)

	if place == 'kitchen_table':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = -5.676982
	    self.exit_point.pose.position.y = 7.866771
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = 0.945753
	    self.exit_point.pose.orientation.w = 0.324887
	    self.gpsr_pub.publish(self.exit_point)
	if place == 'dining_table':
	    #print 'dining '
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = -0.820458
	    self.exit_point.pose.position.y = 4.843864
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = -0.896439
	    self.exit_point.pose.orientation.w = 0.443167
	    self.gpsr_pub.publish(self.exit_point)
	    	
	if place == 'living_table':      #3333333333333333
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = 1.091109
	    self.exit_point.pose.position.y = 9.541927
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = -0.334180
	    self.exit_point.pose.orientation.w = 0.942509
	    self.gpsr_pub.publish(self.exit_point)
	    #print 'living room publish base_controal'
	    	
        if place == 'bedroom_table':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = 3.479954
	    self.exit_point.pose.position.y = 6.724703
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = 0.425627
	    self.exit_point.pose.orientation.w = 0.904899
	    self.gpsr_pub.publish(self.exit_point)

   
        if place == 'door':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = 1.420880
	    self.exit_point.pose.position.y = 1.856649
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = 0.437764
	    self.exit_point.pose.orientation.w = 0.899090
	    self.gpsr_pub.publish(self.exit_point)
	if place == 'zhongjiandian':
            self.exit_point.header.stamp = rospy.Time.now()
	    self.exit_point.header.frame_id = 'map'
	    self.q = tf.transformations.quaternion_from_euler(0,0,1.34)
	    
	    self.exit_point.pose.position.x = -0.080834
	    self.exit_point.pose.position.y = 8.1255
	    self.exit_point.pose.position.z = 0
	    
	    self.exit_point.pose.orientation.x = 0
	    self.exit_point.pose.orientation.y = 0
	    self.exit_point.pose.orientation.z = -0.18424
	    self.exit_point.pose.orientation.w = 0.98288
	    self.gpsr_pub.publish(self.exit_point)




	self.place = ' '


	    	
	
    
###########################################################
    def findperson(self):
	begin_findperson=time.time()
	duration_findperson=0.0
	num=0
	self.j=0
	depth=0
	face_num_max=0
	while (time.time()-begin_findperson<60.0):
		face_cascade=cv2.CascadeClassifier('/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml')
		scaling_factor =1.0
		frame = self.get_video()
		depth_array=np.transpose(self.get_depth())
		cv2.imwrite("/home/ros/robocup/src/beginner_tutorials/launch/photo/user."+"find_person"+".jpg",frame)
		self.frame=cv2.resize(frame,None,fx=scaling_factor,fy=scaling_factor,interpolation=cv2.INTER_AREA)
		gray=cv2.cvtColor(self.frame,cv2.COLOR_BGR2GRAY)
		self.face_rects=face_cascade.detectMultiScale(gray,1.3,5)
		for(x,y,w,h) in self.face_rects:
			x0=x
			y0=y
			rospy.loginfo("x:")
			print x
			rospy.loginfo("y:")
			print y
			rospy.loginfo("w:")
			print w
			rospy.loginfo("h:")
			print h
			flag_findperson=0
			if(x+w>=640 or y+h>=480):
				continue
			flag_break=0
			min_dep=10
			i_min=x0
			j_min=y0
			for i in range(int(w)):
				#print("i=",i)
				#print("x=",x0+i)
				for j in range(int(h)):	
					#print("j=",j)
					#print("y=",y0+j)
					depth=1.0 / (depth_array[x0+i][y0+j] * -0.0030711016 + 3.3309495161)
					print depth
					if(depth_array[x0+i][y0+j]<2047 and depth>0 and depth<min_dep):
						min_dep=depth
						#i_min=i
						#j_min=j
						print "changed"
			depth=min_dep-0.5
			line=320-(x+w*0.5)
			#angle=8.13587-0.03162*line+0.000975239*line*line
			angle=np.arctan((np.tan(3.1415926*28.75/180)/320)*line)
			a=math.sin(angle)
			b=math.cos(angle)
			x_len=depth*a+0.5*math.sin(angle)
			cv2.rectangle(self.frame,(x,y),(x+w,y+h),(0,255,0),1)
			#self.position[num][0]=x_len
			#self.position[num][1]=depth*b

			self.tflistener = tf.TransformListener()
			self.tflistener.waitForTransform('map','camera_link',rospy.Time(),rospy.Duration(4.0))
			(trans1,rot1) = self.tflistener.lookupTransform('map','camera_link',rospy.Time(0))
			print "map to camera_link: "
			print trans1,rot1
			self.tfbroadcaster = tf.TransformBroadcaster()
			self.tfbroadcaster.sendTransform((x_len,depth*b,0.0),(0.0,0.0,0.0,1.0),rospy.Time.now(),"camera_link","people")
			self.peopleposepub.publish(PeoplePose(x_len,depth*b))
			rospy.sleep(1)
			(trans2,rot2) = self.tflistener.lookupTransform('camera_link','people',rospy.Time(0))
			print "camera_link to people: "
			print trans2,rot2
			self.tflistener.waitForTransform('map','people',rospy.Time(),rospy.Duration(4.0))
			try:
        			(trans,rot) = self.tflistener.lookupTransform('map','people',rospy.Time(0))
    			except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
        			rospy.logerr('Error occure when transfrom.')
			self.position[num][0]=trans[0]
			self.position[num][1]=trans[1]
			#self.peopleposepub.publish(2.0,-1.0)

			num=num+1
			print self.position
			rospy.loginfo("angle:")
			print angle
			rospy.loginfo("x_len:")
			print x_len
			rospy.loginfo("depth")
			print depth
			print x0,y0,x0+i_min,y0+j_min
			self.num=num
			cv2.imwrite("/home/ros/robocup/src/beginner_tutorials/launch/photo/user."+"find_person"+".jpg",self.frame)
			rospy.loginfo("l have found the person")
			self.soundhandle.say("l have found the person")
		if(self.position[0][0]!=0 or self.position[0][1]!=0):
			break
	rospy.sleep(3)
	if((self.position[0][0]!=0 or self.position[0][1] != 0)):
		self.go_to_the_point(self.position[self.j][0],self.position[self.j][1])
	else:
	        rospy.loginfo("!!!!!!I have not found person!!!!!!")#
	        self.soundhandle.say("I have not found person.")#
		self.posePosition(self.r6[0])
		print "I have found the person."
	        self.soundhandle.say("I have found the person.")
##############################################################################
    
        
    

        
    def shutdown(self):
        rospy.loginfo("Stopping the robot...")
        
        # Unregister the subscriber to stop cmd_vel publishing
        self.depth_subscriber.unregister()
        rospy.sleep(1)
        
        # Send an emtpy Twist message to stop the robot
        self.cmd_vel_pub.publish(Twist())
        rospy.sleep(1) 
#####################################################################
    def find_object_with_kinect(self,colorLower, colorUpper, Object_Name):
         mybuffer = 64
       	 pts = deque(maxlen=mybuffer)
         frame,_ = freenect.sync_get_video()
         frame=cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)
    	 hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    	 mask = cv2.inRange(hsv, colorLower, colorUpper)
    	 mask = cv2.erode(mask, None, iterations=2)
    	 mask = cv2.dilate(mask, None, iterations=2)
    	 cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    	 center = None
    	 if len(cnts) > 0:
             c = max(cnts, key = cv2.contourArea)
             ((x, y), radius) = cv2.minEnclosingCircle(c)
             M = cv2.moments(c)
             center = (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]))
             if radius > 10:
                 rect=cv2.minAreaRect(c)
                 cv2.rectangle(frame,(int(x)-int(radius),int(y)-int(radius)),(int(x+radius),int(y+2*radius)),(0,255,0),1)
            	 font = cv2.FONT_HERSHEY_SIMPLEX  
                 cv2.putText(frame,Object_Name, (int(x)-int(radius),int(y)-int(radius)), font, 1, (255,255,255), 2)  
                 pts.appendleft(center)
	 print 49
         cv2.imwrite("/home/ros/robocup/src/gpsr_2018/"+"result"+".jpg",frame)
#####################################################  
    def go_to_the_point(self,coord_x,coord_y):
	rospy.loginfo("i will go to the point")
	self.soundhandle.say("i will go to the point")
	#start move	
	rot = tf.transformations.quaternion_from_euler(0,0,0)
	goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = 'map'
    	goal.target_pose.header.stamp = rospy.Time.now()
        self.exit_point.pose.position.x = coord_x
	self.exit_point.pose.position.y = coord_y
	self.exit_point.pose.position.z = 0 
	self.exit_point.pose.orientation.x = rot[0]
	self.exit_point.pose.orientation.y = rot[1]
	self.exit_point.pose.orientation.z = rot[2]
	self.exit_point.pose.orientation.w = rot[3]

    	self.gpsr_pub.publish(self.exit_point)
	print "Have Sended Goal to the move_base."
	#debug
	print "target pose: "
	print coord_x,coord_y
	print "I have found the person."
	self.soundhandle.say("I have found the person.")


    def get_video(self):
	    self.array,_ = freenect.sync_get_video()
	    self.array = cv2.cvtColor(self.array,cv2.COLOR_RGB2BGR)
	    return self.array

    def get_depth(self):
	    array,_ = freenect.sync_get_depth()
	    print "have taken depth photo"
	    #np.savetxt("/home/leichao/out.txt",array)
	    print array
	    return array
	
    def askname(self,com_y):
            print 'Can you tell me what is your name?'
            self.soundhandle.say('Can you tell me what is your name?')
            if (self.remember_name(com_y)):
                person_name=self.remember_name(com_y)
            else:
                print 'Please say again.'
                self.soundhandle.say('Please say again.')
    
    def remember_name(self,com_y):
            for (name,value_name) in self.d_name.iteritems():
                for word in value_name:
                    if comy.find(word)>-1:
                       return name
                       break

 
#######################################################################
    def talkback(self, msg):
	print (msg.data)
        if(msg.data=='Follow.'):
		self.voice_shell.publish("follow")
		print '我已经发了follow了～～'
	else:
		com = self.diff_command(msg.data)###yes or no

		#self.com1 = self.get_command1(msg.data)
		self.com1 = self.get_command11(msg.data)   ##@222222222222222222222
		self.com_y = self.get_command2(msg.data)
		self.com_full=self.get_command11(msg.data)
		self.com3 = self.get_command3(msg.data)

		#rospy.loginfo(com1)
		self.ks = self.keys_command.keys()
		self.ks2 = self.keys_movebase.keys()
		self.ks3 = self.answers_to_questions.keys()
		self.ks4 = self.d_name.keys()
		

	## ///
		self.m1 = self.understand_1(self.com1)
		self.m2 = self.understand_2(self.com1)
		self.m3 = self.understand_3(self.com1)
		self.m5 = self.understand_5(self.com1)
		
		self.cm3 = self.get_command3(msg.data)
	## ///


		#diao yong
		#back_txt = self.analyzeTwoStr(self.com1)
	#	self.analyzeTwoStr(self.com1)
		#rospy.loginfo(back_txt)
		#print back_txt

		#diao yong
	#	self.yesToBase(self.com_y, self.com1)

		#diao yong
	#	self.answersToQuestions(self.com3)
		
		
		if len(com)<=6:                  #<==============
		    self.yesToBase(self.com_y, self.com1)
		elif self.cm3:
		    anss=self.answerQuestion(self.cm3)
		    self.soundhandle.say(anss)
		    print anss
		    print ''

		elif len(self.m1)>=15 or len(self.m2)>=15 or len(self.m3)>=15 or len(self.m5)>=15:
		    if len(self.m1)>=15:
			self.soundhandle.say(self.m1)
		        print self.m1
			print ''
		    if len(self.m2)>=15:
			self.soundhandle.say(self.m2)
		        print self.m2
			print ''
		    if len(self.m3)>=15:
			self.soundhandle.say(self.m3)
		        print self.m3
			print ''
		    if len(self.m5)>=15:
			self.soundhandle.say(self.m5)
		        print self.m5
			print ''

		else:
		    print "I don't understand3. Please say again. "
		    print ''
		    sz = "I don't understand4. Please say again. "
		    self.soundhandle.say(sz)



		self.m1=' '
		self.m2=' '
		self.m3=' '
		self.m5=' '
		#print ''
		#self.com1 = ''
		#self.com_y = ''
		#self.com3 = ''
		#com = ''



    def cleanup(self):
        #self.soundhandle.stopAll()
        rospy.loginfo("Shutting down talkback node...")
        
    def base_status_callback(self, msg):
    	self.base_status = msg.status.status
	self.base_sts = self.base_status


 

if __name__=="__main__":
    try:
        TalkBack(sys.path[0])
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Talkback node terminated.")	



        



		

