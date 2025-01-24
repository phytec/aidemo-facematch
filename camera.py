# Copyright (c) 2025 PHYTEC Messtechnik GmbH
# SPDX-License-Identifier: Apache-2.0
# Author: Martin Schwan <m.schwan@phytec.de>

import glob
import subprocess
import cv2 as cv

class Camera():
    def __init__(self):
        self.cameraDevice = None
        self.colorConversionCode = None
        self.apiPreference = None
        self.videoCapture = cv.VideoCapture()

    def open(self, filename):
        if self.apiPreference is None:
            raise AttributeError('API preference must be set before opening '
                                 'video capture device!')
        self.videoCapture.open(filename, self.apiPreference)
        if not self.videoCapture.isOpened():
            raise ValueError(f'Failed opening video capture device "{filename}"!')

    def convert_frame_color(self, frame):
        if self.colorConversionCode is None:
            raise AttributeError('Color conversion code must be set before '
                                 'converting frame colors!')
        return cv.cvtColor(frame, self.colorConversionCode)

class CameraUSB(Camera):
    def __init__(self):
        super().__init__()
        self.colorConversionCode = cv.COLOR_BGR2RGB
        self.apiPreference = cv.CAP_ANY

    def open(self, filename=1):
        super().open(filename)

class CameraVM016(Camera):
    def __init__(self):
        super().__init__()
        self.colorConversionCode = cv.COLOR_BAYER_GB2RGB
        self.apiPreference = cv.CAP_GSTREAMER

        if cv.getBuildInformation().find('GStreamer') < 0:
            raise ValueError('This version of OpenCV does not support GStreamer!')

    def open(self, filename=None):
        if filename is None:
            cameraDevices = glob.glob('/dev/cam-csi[0-9]*')
            if not cameraDevices:
                raise FileNotFoundError('No VM016 camera devices found!')
            filename = cameraDevices[0]

        videoDevices = glob.glob('/dev/video-isi-csi[0-9]*')
        if not videoDevices:
            raise FileNotFoundError('No ISI device found!')
        videoDevice = videoDevices[0]

        width = 1280
        height = 800

        size = f'{width}x{height}'
        cmd = f'setup-pipeline-csi1 -s {size} -c {size}'
        if not subprocess.call(cmd, shell=True):
            subprocess.call(cmd, shell=True)

        controls = [
            '-c vertical_flip=1',
            '-c horizontal_blanking=2500',
            '-c digital_gain_red=1400',
            '-c digital_gain_blue=1700',
        ]
        cmd = f'v4l2-ctl -d {filename} {" ".join(controls)}'
        if not subprocess.call(cmd, shell=True):
            print(f'v4l2-ctl failed: {ret}')
            subprocess.call(cmd, shell=True)

        fmt = f'video/x-bayer,format=grbg,width={width},height={height}'
        super().open(f'v4l2src device={videoDevice} ! {fmt} ! appsink')
