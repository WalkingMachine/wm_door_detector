#!/usr/bin/env python

import roslib
import rospy

from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from threading import Event


# Class that detects if the door is open
class wait_door:
    def __init__(self, timeout=None):
        self.distances = []
        self.door_open = Event()
        self.timeout = timeout
        self.no_door_found = False

    def avg(self, lst):
        return sum(lst) / max(len(lst), 1)

    def process_scan(self, scan_msg):
        try:
            middle_index = len(scan_msg.ranges)/2
            ranges_at_center = scan_msg.ranges[middle_index-2:middle_index+2]
            distance_to_door = self.avg(ranges_at_center)
            self.distances += [distance_to_door]

            avg_distance_now = self.avg(self.distances[-5:])

            if self.distances[0] > 1.0:
                self.no_door_found = True
                rospy.loginfo("No door found")
                self.door_open.set()
            elif avg_distance_now > 1.0:
                rospy.loginfo("Distance to door is more than a meter")
                self.door_open.set()

        except Exception, e:
            rospy.logerr("Fail sub to laser")
            self.laser_sub.unregister()

    def run(self):
        rospy.loginfo("Waiting for door...")
        self.laser_sub = rospy.Subscriber("/scan", LaserScan, self.process_scan)
        self.door_pub = rospy.Publisher('/door', String, queue_size=10)

        opened_before_timeout = self.door_open.wait(timeout=self.timeout)

        rospy.loginfo("Unregistering laser and clearing data")
        self.laser_sub.unregister()
        self.distances = []

        self.door_open.clear()

        if self.no_door_found:
            rospy.loginfo("No door found")
            self.door_pub.publish("no_door")
            return "no_door"

        if opened_before_timeout:
            rospy.loginfo("Door is open")
            self.door_pub.publish("open")
            return "open"

        rospy.loginfo("timed out with door still closed")
        return "close"

if __name__ == '__main__':
    rospy.init_node('wait_for_door')

    timeout = 10
    
    wait_for_door = wait_door(timeout)
    
    result = wait_for_door.run()