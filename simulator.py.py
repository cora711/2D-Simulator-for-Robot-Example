## ROBOT EAMPLE IN PRACTICE ##

from PIL import Image, ImageDraw, ImageFont
import random
import os
import time

cwd = os.getcwd()
im_direct = cwd + "\\images\\"

"""
MODIFIABLE PARAMETERS:
"""

image_size = (150,200)

number_of_resources = 400
number_of_workers = 9
number_of_supervisors = 1

total_generations = 3000

"""
SYSTEM FUNCTIONS
"""

def display():
    for i in Resource.Resource_list:
        if i.state != "full":
            im.putpixel(i.position, i.color)
    for i in Robot.Robot_list:
        im.putpixel(i.position, i.color)

def dist(point_1, point_2):
    return pow(pow(point_1[0]-point_2[0], 2) + pow(point_1[1] - point_2[1], 2), 0.5)

def add_tup(tup_1,tup_2):
    return (tup_1[0]+tup_2[0], tup_1[1] + tup_2[1])

def middle_pixel():
    return (image_size[0]/2, image_size[1]/2)

def base_station():
    return (image_size[0]/4, image_size[1]/4)

def resource_collect():
    return ((image_size[0]*3/4, image_size[1]*3/4))

def free_space():
    taken_check = True
    while taken_check:
        first = random.randint(0, image_size[0]-1)
        second = random.randint(0, image_size[1]-1)
        provisional_point = (first, second)

        if not taken(provisional_point):
            taken_check = False
   
    return provisional_point

def taken(position):
    if position == middle_pixel():
        return True
    for robot in Robot.Robot_list:
        if position == robot.position:
            return True
    for resource in Resource.Resource_list:
        if position == resource.position:
            return True

    for special in [middle_pixel, base_station, resource_collect]:
        if position == special():
            return True

    return False


def in_bounds(point):
    for i in range(2):
        if point[i] < 0 or point[i] >= image_size[i]:
            return False
    return True

"""
Definitions for the Robot Classes
"""

class Robot:
    Robot_list = []
    
    up = (0,-1)
    right = (1,0)
    left = (-1,0)
    down = (0,1)
    movements = [up, right, left, down]
    
    def __init__(self):
        self.access_state = False
        self.internal_clock_start = time.time()
        self.time_up = random.randint(2,50)
        
        self.position = free_space()
        self.color = (0,0,0)
        self.goal = ()

        self.life_cycle = ["looking for resource", "moving to resource"]
        self.state = self.life_cycle[0]
        
        Robot.Robot_list.append(self)

        self.log = []

    def move(self):
        if self.state != "update":
            best_move = (0,0)
            remember_pos = None
            special_marker = False
            
            for pot_move in random.sample(Robot.movements, len(Robot.movements)): # randomizes which direction goes first
                pot_new_pos = add_tup(pot_move, self.position)

                if not taken(pot_new_pos):
                    if in_bounds(pot_new_pos):
                        remember_pos = pot_move
                    
                if dist(pot_new_pos, self.goal) < dist(add_tup(best_move, self.position), self.goal):

                    if pot_new_pos == self.goal:

                        self.position = pot_new_pos
                        self.modify_state()

                        return
                    
                    else:
                        
                        if not taken(pot_new_pos):
                            best_move = pot_move
                            special_marker = True
                            
            if remember_pos != None and not special_marker:
                best_move = remember_pos
                
            self.position = add_tup(best_move, self.position)
        else:
            if self.color == (255,0,0):
                self.state = "super_update"
                self.move()
##                self.state = "update"
                
    def modify_state(self):
        if self.state == "moving to resource":
            temp_resource = self.wanted_resource
            temp_resource.state = "full"
            temp_resource.position = middle_pixel()

            self.state = "looking for resource"
            self.goal = None

            Resource()            

        if self.state == "updating worker":
            self.request_access(self.wanted_worker)
            self.state = "looking for worker to update"

        if self.state == "super_update" and self.color == (255,0,0):
            self.update()
            
    def check_update(self):
        if time.time() - self.internal_clock_start > self.time_up:
            self.state = "update"
            if self.color == (255,0,0):
                self.goal = middle_pixel()
                
    def update(self, msg):
        
        print "Worker", Robot.Robot_list.index(self)+1, "updates fields with given message."
        self.access_state = msg[0]
        self.internal_clock_start = msg[1]
        self.time_up = msg[2]
        self.goal = msg[3]
        self.state = msg[4]
        self.wanted_resource = msg[5]
        
        print"Worker", Robot.Robot_list.index(self)+1, "update complete."

    def get_access(self, asker):
        if asker.color == (255,0,0): # authentication
            if random.randint(1,5) != 1:
                self.access_state = True
                print "Worker ", Robot.Robot_list.index(self), "says `access granted'."
                return True
            else:
                print "Malfunctioning worker ", Robot.Robot_list.index(self), "says `access denied'."
                
class Worker(Robot):
    def __init__(self):
        Robot.__init__(self)
        self.wanted_resource = None

        
    def find_resource(self):
        potential_nearest_res = None
        if self.state == "looking for resource":
            shortest_distance = "inf"
            
            for res in Resource.Resource_list:
                if res.state == "free":
                    if dist(res.position, self.position) < shortest_distance:

                        potential_nearest_res = res
                        
                        shortest_distance =  dist(res.position, self.position)

        if potential_nearest_res != None:
            self.goal = potential_nearest_res.position
            
                        
                        
            self.state = "moving to resource"
            self.wanted_resource = potential_nearest_res

            potential_nearest_res.state = "taken"

            
    def act(self):
        self.check_update()
        self.find_resource()
        self.move()

class Supervisor(Robot):
    def __init__(self):

        Robot.__init__(self)
        self.color = (255,0,0)
        self.life_cycle = ["looking for worker to update", "moving to worker"]
        self.state = self.life_cycle[0]
        self.goal = free_space()
        self.wanted_worker = None

        self.time_up = 30
        self.update_message = [
            False,
            time.time(),
            100,
            None,
            "looking for resource",
            False          
            ]

##    def ask(self, recipient):
##        self.request_access(recipient)
##        self.state = "looking for worker to update"
##        self.goal = free_space()
##        self.wanted_worker = None

    def find_worker_needing_help(self):
        if self.state == "looking for worker to update":
            for i in Robot.Robot_list:
                if i.color == (0,0,0):
                    if i.state == "update":
                        self.goal = i.position
                        self.state = "updating worker"
                        self.wanted_worker = i                        
                        return

            self.goal = free_space()
        
    def update(self):
        print "Supervisor", Robot.Robot_list.index(self) - number_of_workers+1, "having system update."
        self.update_message = [
                False,
                time.time(),
                300,
                None,
                "looking for resource",
                False          
            ]
        self.state = "looking for worker to update"
        print "happens"
        self.goal = free_space()
        self.wanted_worker = None
        self.internal_clock_start = time.time()
        self.time_up = 100

    def force_update(self, recipient): ## transparency
        recipient.access_state = True
        recipient.internal_clock_start = time.time()
        self.log.append((time.time(), recipient, "Forced Update", "Denied Acess"))
        recipient.append((time.time(), self, "Forced Update", "Denied Access"))
        recipient.goal = None
        recipient.state = "looking for resource"
        recipient.wanted_resource = None
        print "Supervisor", Robot.Robot_list.index(self) - number_of_workers+1, "forces update."
        
    def request_access(self, recipient):
        if recipient.color == (0,0,0):
            print "Supervisor", Robot.Robot_list.index(self) - number_of_workers+1, "requests access to Worker", Robot.Robot_list.index(recipient)+1, "for update."
            if recipient.get_access(self):
                print "Supervisor", Robot.Robot_list.index(self) - number_of_workers+1, "sends update message:"
                print " - set access_state", False
                print " - set update start time", time.time()
                print " - set update duration", 100
                recipient.update(self.update_message)
            else:
                self.force_update(recipient)  ## transparency
        self.state = "looking for worker to update"
        self.goal = free_space()
        self.wanted_worker = None  

    def act(self):        
        self.check_update()
        self.find_worker_needing_help()
        self.move()
        
class Resource:
    Resource_list = []
    
    def __init__(self):
        self.position = free_space()
        self.state = "free"
        self.color = (0,255,0)
        Resource.Resource_list.append(self)

##class System:
##    def __init__(self):
##        
## PUT EVERY FUNCTION ETC IN HERE...
        
"""
GENERATE INITIAL RESOURCES AND ROBOTS
"""

for i in range(number_of_resources):
    Resource()
    
for i in range(number_of_workers):
    Worker()
    
for i in range(number_of_supervisors):
    Supervisor()

"""
RUN 
"""




for gen in range(total_generations):
    im = Image.new("RGB", image_size, "white")


    text_image_size = image_size
    text_image = Image.new('RGB', text_image_size, color = (255,255,255))
 
    d = ImageDraw.Draw(text_image)
    total_text = "Robot            Behavior \n -----------------------------"


    

##helvetica = ImageFont.truetype(filename="Helvetica.ttf", size=40)

    font = ImageFont.truetype("arial.ttf", size=8)
    
    
 
    



    print "gen= ", gen
    for rob in Robot.Robot_list:
        rob.act()

    for tester in Robot.Robot_list:
        total_text += "\n"
        if Robot.Robot_list.index(tester)+1 > number_of_workers:
            total_text += "supervisor" + str(Robot.Robot_list.index(tester) - number_of_workers + 1) + "   " + tester.state
        else:
            total_text += "worker" + str(Robot.Robot_list.index(tester) + 1) + "          " + tester.state
        
    d.text((1,1), total_text, fill=(0,0,0), font=font)
    text_image.save(im_direct + str(gen)+ "text.png", "PNG")
    
    display()
    im.save(im_direct + str(gen)+ ".png", "PNG")

    joined_image = Image.new('RGB', (image_size[0]+text_image_size[0], image_size[1]), color = (255,255,255))
    joined_image.paste(im)
    joined_image.paste(text_image,(image_size[0],0))

    joined_image.save(im_direct + str(gen) + "joined.png", "PNG")
    
