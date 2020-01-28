import io
from table import Table
from picamera.array import PiRGBArray
from picamera import PiCamera
import sys
import cv2
import numpy
import math
from enum import Enum

class GripPipeline:
    """
    An OpenCV pipeline generated by GRIP.
    """
    
    def __init__(self):
        """initializes all values to presets or None if need to be set
        """

        self.__blur_type = BlurType.Box_Blur
        self.__blur_radius = 3.6036036036036037

        self.blur_output = None

        self.__hsv_threshold_input = self.blur_output
        self.__hsv_threshold_hue = [11.33093525179856, 89.8471986417657]
        self.__hsv_threshold_saturation = [105.48561151079137, 255.0]
        self.__hsv_threshold_value = [71.08812949640287, 255.0]

        self.hsv_threshold_output = None


    def process(self, source0):
        """
        Runs the pipeline and sets all outputs to new values.
        """
        # Step Blur0:
        self.__blur_input = source0
        (self.blur_output) = self.__blur(self.__blur_input, self.__blur_type, self.__blur_radius)

        # Step HSV_Threshold0:
        self.__hsv_threshold_input = self.blur_output
        (self.hsv_threshold_output) = self.__hsv_threshold(self.__hsv_threshold_input, self.__hsv_threshold_hue, self.__hsv_threshold_saturation, self.__hsv_threshold_value)


    @staticmethod
    def __blur(src, type, radius):
        """Softens an image using one of several filters.
        Args:
            src: The source mat (numpy.ndarray).
            type: The blurType to perform represented as an int.
            radius: The radius for the blur as a float.
        Returns:
            A numpy.ndarray that has been blurred.
        """
        if(type is BlurType.Box_Blur):
            ksize = int(2 * round(radius) + 1)
            return cv2.blur(src, (ksize, ksize))
        elif(type is BlurType.Gaussian_Blur):
            ksize = int(6 * round(radius) + 1)
            return cv2.GaussianBlur(src, (ksize, ksize), round(radius))
        elif(type is BlurType.Median_Filter):
            ksize = int(2 * round(radius) + 1)
            return cv2.medianBlur(src, ksize)
        else:
            return cv2.bilateralFilter(src, -1, round(radius), round(radius))

    @staticmethod
    def __hsv_threshold(input, hue, sat, val):
        """Segment an image based on hue, saturation, and value ranges.
        Args:
            input: A BGR numpy.ndarray.
            hue: A list of two numbers the are the min and max hue.
            sat: A list of two numbers the are the min and max saturation.
            lum: A list of two numbers the are the min and max value.
        Returns:
            A black and white numpy.ndarray.
        """
        out = cv2.cvtColor(input, cv2.COLOR_BGR2HSV)
        return cv2.inRange(out, (hue[0], sat[0], val[0]),  (hue[1], sat[1], val[1]))


BlurType = Enum('BlurType', 'Box_Blur Gaussian_Blur Median_Filter Bilateral_Filter')


table = Table(1)

grip = GripPipeline()


def main(stop_message, sem):

    def connection(stop_message):

        x = stop_message[0]

        print("[*]Thread 2 queue:", x)

        if x != 2:
            print("[*]Thread 2 exiting")
            cam.close()
            sem.release()
            sys.exit()

    cam = PiCamera()
    cam.resolution = (640, 480)
    cam.framerate = 32
    rawCap = PiRGBArray(cam, size=(640, 480))

    for frame in cam.capture_continuous(rawCap, format='bgr', use_video_port=True):

        frame = frame.array
        frame2 = frame
        try:
            grip.process(frame)
            
            output = grip.hsv_threshold_output

            _, thresh = cv2.threshold(frame, 127 , 255, 0)
            _, contours ,_ = cv.findContours(thresh, 1, 2)
            
            (x, y), radius = cv2.minEnclosingCircle(contours[0])
            
            
            print("Center: {}\nRadius: {}".format((x,y), radius))

            cv2.circle(frame2, (x,y), radius, (0, 255, 0), 2)
            cv2.circle(output, (x,y), radius, (0, 255, 0), 2)
            print("Ball found")

            table.updateNumber((x, y), key=0)
            table.updateNumber(radius, key=1)
        except Exception as e:
            print(e)
            print("--------------")
            print("Ball not found")

            table.updateNumber("B", key=0)
            table.updateNumber("B", key=1)
    
        cv2.imshow('Input', frame2)
        cv2.imshow('Output', output)

        rawCap.truncate(0)

        connection(stop_message)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
