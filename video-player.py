import cv2, os, sys, time
import numpy as np
from threading import Thread, Semaphore, Lock

class Queue():
    def __init__(self, frames):
        self.fps = frames               # this denotes how many frames we can have within a queue
        self.queue = []                 # this is our producer queue
        self.sem = Semaphore(frames)    # this is our semaphore for maintaining resources
        self.lock = Lock()              # this is our lock for maintaining which thread is running
        
    def empty(self):
        return len(self.queue) <= 0
    
    def push(self, frame):
        self.sem.acquire()
        self.lock.acquire()
        self.queue.insert(0, frame)
        self.lock.release()
    
    def pop(self):
        self.sem.release()
        self.lock.acquire()
        frame = self.queue.pop()
        self.lock.release()
        return frame

class FrameReader(Thread):
    def __init__(self, video):
        Thread.__init__(self)
        self.vidcap = cv2.VideoCapture(video)
        self.frames = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))-1
        self.count = 0
        
    def run(self):
        global prod
        success, img = self.vidcap.read()
        
        while success and self.count < self.frames:
            # Pushing into producer queue
            prod.push(img)
            success, img = self.vidcap.read()
            self.count += 1
        prod.push(True)
        
class FrameConverter(Thread):
    def __init__(self):
        Thread.__init__(self)
    
    def run(self):
        global prod
        global cons
        
        while True:
            if not prod.empty():
                img = prod.pop()
                if type(img) == bool and img:     # we know we're done since this boolean denotes the end of the queue
                    break
                gs_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                cons.push(gs_img)
        cons.push(True)


class FrameDisplay(Thread):
    def __init__(self, delay):
        Thread.__init__(self)
        self.delay = delay
        
    def run(self):
        global cons
        
        while True:
            if not cons.empty():
                img = cons.pop()
                if type(img) == bool and img:
                    break
                if cv2.waitKey(self.delay) and 0xFF == ord("q"): # Checking for delay or quit
                    break
                cv2.imshow('Video', img)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    video = "clip.mp4"
    delay = 30
    frames = 30
    
    prod = Queue(frames)
    cons = Queue(frames)
    
    fr = FrameReader(video)
    fc = FrameConverter()
    fd = FrameDisplay(delay)
    
    fr.start()
    fc.start()
    fd.start()
    
