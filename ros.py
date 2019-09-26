import io
import json
import inspect
import time
import cv2
import numpy as np
import requests
import signal
import sys

import roslib
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

_DEBUGMODE = True
cam = 'http://192.168.1.1:80'
url = cam+'/osc/'
exe = url+'commands/execute'

# ROS publisher
image_pub = rospy.Publisher("image_raw", Image, queue_size=1)
bridge = CvBridge()

def handler(signal, frame):
        print("Shutting down...")
        sys.exit(0)


def startSession():
    j = {'name': 'camera.{}'.format(inspect.currentframe().f_code.co_name), 'parameters': {}}

    r = requests.post(exe, data=json.dumps(j))
    if _DEBUGMODE:
        print("---startSession---")
        print(r.json())
    return r.json()


def closeSession(id):
    j = {'name': 'camera.{}'.format(inspect.currentframe().f_code.co_name), 'parameters': {'sessionId': '{}'.format(id)}}

    r = requests.post(exe, data=json.dumps(j))
    if _DEBUGMODE:
        print("---closeSession---")
        print(r.json())
    return r.json()



def _getLivePreview(id):
    global image_pub
    global bridge
    j={'name':'camera.{}'.format(inspect.currentframe().f_code.co_name),
    'parameters': {'sessionId': id}}
    print(j)
    r=requests.post(exe, data=json.dumps(j), stream=True)
    bytes = b''
    for byteData in r.iter_content(chunk_size=1024):
        bytes += byteData
        a = bytes.find(b'\xff\xd8')
        b = bytes.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes[a:b+2]
            bytes = bytes[b+2:]
            try:
                img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                cv2.imshow('live preview', img)
                if cv2.waitKey(1) == 27:
                    cv2.destroyAllWindows()
                    return
                image_pub.publish(bridge.cv2_to_imgmsg(img, "bgr8"))
            except:
                print("OpenCV Error")
            #rospy.spin()
    return r.json()

def main():
    signal.signal(signal.SIGINT, handler)
    # ROS settings
    rospy.init_node('theta_livePreview_publisher', anonymous=True)

    # session
    d = startSession()
    if d['state'] == 'error':
        return closeSession('SID_001')

    # api and options
    id = d['results']['sessionId']
    img = _getLivePreview(id)

    # session
    closeSession(id)


if __name__ == '__main__':
    main()




