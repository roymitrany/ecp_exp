import random
import sys
import time
import os

while True:
    time.sleep(random.randint(20,40))
    dst_ip = "%s.%d"%(sys.argv[1], random.randint(int(sys.argv[2]),int(sys.argv[3])))
    os.system('ping -c 1 ' + dst_ip)

