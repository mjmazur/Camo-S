"""

GUI for Camo-S Analysis

Naming conventions:
Class: ClassName
Functions: functionName
Variable names: variable, variable_name
Widgets: Name_widgetype, i.e. Upload_button, Direct_linedit, Spectral_label

"""
###################################################################################################
################################## IMPORTS AND SUPPORT FUNCTIONS ##################################
###################################################################################################

#################### STANDARD IMPORTS ####################

import numpy as np
import pyqtgraph as pg
import sys 
sys.path.append('../RMS/RMS/Routines')
import matplotlib.pyplot as plt
import scipy.ndimage
import os
import sys
import imageio 
imread = imageio.imread
import math
from sklearn.linear_model import RANSACRegressor
from sklearn.metrics import (r2_score, mean_absolute_error)
from scipy.signal import savgol_filter

#################### PYQT5 LIBRARY/PACKAGE IMPORTS ####################

from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from calibration import Ui_CalibrationDialog

#################### FROM WMPL ####################

from wmpl.Formats.Vid import readVid
from wmpl.Utils.TrajConversions import unixTime2Date
from wmpl.Formats.Plates import loadScale, plateScaleMap

# Cython init
import pyximport
pyximport.install(setup_args={'include_dirs':[np.get_include()]})
from BinImageCy import binImage as binImageCy

spectral_library = __import__("CAMO-Spectral_Library")

#################### SUPPORT FUNCTIONS AND CLASSES ####################
def twoDGaussian(params, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    x, y, saturation = params
    if isinstance(saturation, np.ndarray):
        saturation = saturation[0,0]

    xo = float(xo)
    yo = float(yo)

    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    g = offset + amplitude*np.exp(-(a*((x - xo)**2) + 2*b*(x - xo)*(y - yo) + c*((y-yo)**2)))

    g[g > saturation] = saturation

    return g.ravel()

def fitPSF(imarray, avepixel_mean, x2, y2):
    segment_radius = 25
    roundness_threshold = 0.5
    max_feature_ratio = 0.8

    x_fitted = []
    y_fitted = []
    amplitude_fitted = []
    intensity_fitted = []
    sigma_y_fitted = []
    sigma_x_fitted = []

    # Set the initial guess
    initial_guess = (10.0, segment_radius, segment_radius, 1.0, 1.0, 0.0, avepixel_mean)

    for star in zip(list(y2), list(x2)):
        hot_pixel = False
        small_star = False
        zero_intensity = False
        fitting_failed = False
        max_ratio = False

        y, x = star

        y_min = y - segment_radius
        y_max = y + segment_radius
        x_min = x - segment_radius
        x_max = x + segment_radius

        if y_min < 0:
            y_min = np.array([0])
        if y_max > np.shape(imarray)[0]:
            y_max = np.array(np.shape(imarray)[0])
        if x_min < 0:
            x_min = np.array([0])
        if x_max > np.shape(imarray)[1]:
            x_max = np.array(np.shape(imarray[1]))

        x_min = int(x_min)
        x_max = int(x_max)
        y_min = int(y_min)
        y_max = int(y_max)

        star_seg = imarray[y_min:y_max,x_min:x_max]

        y_ind, x_ind = np.indices(star_seg.shape)

        saturation = (2**(8*star_seg.itemsize) - 1)*np.ones_like(y_ind)

        try:
            popt, pcov = scipy.optimize.curve_fit(twoDGaussian, (y_ind, x_ind, saturation), star_seg.ravel(), \
                p0=initial_guess, maxfev=200)
        except RuntimeError:
            fitting_failed = True

        if fitting_failed == False:
            amplitude, yo, xo, sigma_y, sigma_x, theta, offset = popt
        else:
            amplitude, yo, xo, sigma_y, sigma_x, theta, offset = (0,0,0,1.0,1.0,0,0)

        if min(sigma_y/sigma_x, sigma_x/sigma_y) < roundness_threshold:
            hot_pixel = True

        if (4*sigma_x*sigma_y/segment_radius**2 > max_feature_ratio):
            max_ratio = True

        crop_y_min = int(yo - 3*sigma_y) + 1
        if crop_y_min < 0: crop_y_min = 70

        crop_y_max = int(yo + 3*sigma_y) + 1
        if crop_y_max >= star_seg.shape[0]: crop_y_max = star_seg.shape[0] - 1

        crop_x_min = int(xo - 3*sigma_x) + 1
        if crop_x_min < 0: crop_x_min = 0

        crop_x_max = int(xo + 3*sigma_x) + 1
        if crop_x_max >= star_seg.shape[1]: crop_x_max = star_seg.shape[1] - 1


        if (y_max - y_min) < 3:
            crop_y_min = int(yo - 2)
            crop_y_max = int(yo + 2)
        if (x_max - x_min) < 3:
            crop_x_min = int(xo - 2)
            crop_x_max = int(xo + 2)

        star_seg_crop = star_seg[crop_y_min:crop_y_max,crop_x_min:crop_x_max]

        if (star_seg_crop.shape[0] == 0) or (star_seg_crop.shape[1] == 0):
            small_star = True

        bg_corrected = offset
        intensity = np.sum(star_seg_crop - bg_corrected)

        if intensity <= 0:
            zero_intensity = True

        if (hot_pixel == True) or (small_star == True) or (zero_intensity == True) or (max_ratio == True):
            x_fitted.append(x)
            y_fitted.append(y)
            amplitude_fitted.append(-999)
            intensity_fitted.append(0)
            sigma_y_fitted.append(-999)
            sigma_x_fitted.append(-999)
        else:
            x_fitted.append(x_min + xo)
            y_fitted.append(y_min + yo)
            amplitude_fitted.append(amplitude)
            intensity_fitted.append(intensity)
            sigma_y_fitted.append(sigma_y)
            sigma_x_fitted.append(sigma_x)

    return x_fitted, y_fitted, amplitude_fitted, intensity_fitted, sigma_y_fitted, sigma_x_fitted

# Allows user to adjust image levels 
def adjustLevels(img_array, minv, gamma, maxv, nbits=None, scaleto8bits=False):
    """
     Adjusts levels on image with given parameters.

    Arguments:
        img_array: [ndarray] Input image array.
        minv: [int] Minimum level.
        gamma: [float] gamma value
        Mmaxv: [int] maximum level.

    Keyword arguments:
        nbits: [int] Image bit depth.
        scaleto8bits: [bool] If True, the maximum value will be scaled to 255 and the image will be converted
            to 8 bits.

    Return:
        [ndarray] Image with adjusted levels.
    """
    
    if nbits is None:
       
        # Get the bit depth from the image type
        nbits = 8*img_array.itemsize

    input_type = img_array.dtype

    # Calculate maximum image level
    max_lvl = 2**nbits - 1.0

    # Limit the maximum level
    if maxv > max_lvl:
        maxv = max_lvl

    # Check that the image adjustment values are in fact given
    if (minv is None) or (gamma is None) or (maxv is None):
        return img_array

    minv = minv/max_lvl
    maxv = maxv/max_lvl
    interval = maxv - minv
    invgamma = 1.0/gamma

    # Make sure the interval is at least 10 levels of difference
    if interval*max_lvl < 10:

        minv *= 0.9
        maxv *= 1.1

        interval = maxv - minv
       
    # Make sure the minimum and maximum levels are in the correct range
    if minv < 0:
        minv = 0

    if maxv*max_lvl > max_lvl:
        maxv = 1.0
   
    img_array = img_array.astype(np.float64)

    # Reduce array to 0-1 values
    img_array = np.divide(img_array, max_lvl)

    # Calculate new levels
    img_array = np.divide((img_array - minv), interval)

    # Cut values lower than 0
    img_array[img_array < 0] = 0

    img_array = np.power(img_array, invgamma)

    img_array = np.multiply(img_array, max_lvl)

    # Convert back to 0-maxval values
    img_array = np.clip(img_array, 0, max_lvl)

    # Scale the image to 8 bits so the maximum value is set to 255
    if scaleto8bits:
        img_array *= 255.0/np.max(img_array)
        img_array = img_array.astype(np.uint8)

    else:

        # Convert the image back to input type
        img_array = img_array.astype(input_type)

    return img_array

# Loads the image into the script
def loadImage(img_path, flatten=-1):
    """ Load the given image. Handle loading it using different libraries. 
    
    Arguments:
        img_path: [str] Path to the image.
    Keyword arguments:
        flatten: [int] Convert color image to grayscale if -1. -1 by default.
    """

    img = imageio.imread(img_path, as_gray=bool(flatten))

    return img

# Bins a given image, provides a numpy array 
def binImage(img, bin_factor, method='avg'):
    """ Bin the given image. The binning has to be a factor of 2, e.g. 2, 4, 8, etc.
    This is just a wrapper function for a cythonized function that does the binning.
    
    Arguments:
        img: [ndarray] Numpy array representing an image.
        bin_factor: [int] The binning factor. Has to be a factor of 2 (e.g. 2, 4, 8).
    Keyword arguments:
        method: [str] Binning method.  'avg' by default.
            - 'sum' will sum all values in the binning window and assign it to the new pixel.
            - 'avg' will take the average.
    Return:
        out_img: [ndarray] Binned image.
    """

    input_type = img.dtype

    # Make sure the input image is of the correct type
    if img.dtype != np.uint16:
        img = img.astype(np.uint16)
    
    # Perform the binning
    img = binImageCy(img, bin_factor, method=method)

    # Convert the image back to the input type
    img = img.astype(input_type)

    return img

# Structure containing flat field
class FlatStruct(object):
    def __init__(self, flat_img, dark=None):
        """ Structure containing the flat field.
        Arguments:
            flat_img: [ndarray] Flat field.
        """

        # Convert the flat to float64
        self.flat_img = flat_img.astype(np.float64)

        # Store the original flat
        self.flat_img_raw = np.copy(self.flat_img)

        # Apply the dark, if given
        self.applyDark(dark)

        # Compute the flat median
        self.computeAverage()

        # Fix values close to 0
        self.fixValues()


    def applyDark(self, dark):
        """ Apply a dark to the flat. """

        # Apply a dark frame to the flat, if given
        if dark is not None:
            self.flat_img = applyDark(self.flat_img_raw, dark)
            self.dark_applied = True

        else:
            self.flat_img = np.copy(self.flat_img_raw)
            self.dark_applied = False

        # Compute flat median
        self.computeAverage()

        # Fix values close to 0
        self.fixValues()


    def computeAverage(self):
        """ Compute the reference level. """


        # # Bin the flat by a factor of 4 using the average method
        # flat_binned = binImage(self.flat_img, 4, method='avg')

        # # Take the maximum average level of pixels that are in a square of 1/4*height from the centre
        # radius = flat_binned.shape[0]//4
        # img_h_half = flat_binned.shape[0]//2
        # img_w_half = flat_binned.shape[1]//2
        # self.flat_avg = np.max(flat_binned[img_h_half-radius:img_h_half+radius, \
        #     img_w_half-radius:img_w_half+radius])

        self.flat_avg = np.median(self.flat_img)

        # Make sure the self.flat_avg value is relatively high
        if self.flat_avg < 1:
            self.flat_avg = 1


    def fixValues(self):
        """ Handle values close to 0 on flats. """

        # Make sure there are no values close to 0, as images are divided by flats
        self.flat_img[(self.flat_img < self.flat_avg/10) | (self.flat_img < 10)] = self.flat_avg


    def binFlat(self, binning_factor, binning_method):
        """ Bin the flat. """

        # Bin the processed flat
        self.flat_img = binImage(self.flat_img, binning_factor, binning_method)

        # Bin the raw flat image
        self.flat_img_raw = binImage(self.flat_img_raw, binning_factor, binning_method)

# Load flat
# def loadFlat(dir_path, file_name, dtype=None, byteswap=True, dark=None):
#     """ Load the flat field image. 
#     Arguments:
#         dir_path: [str] Directory where the flat image is.
#         file_name: [str] Name of the flat field file.
#     Keyword arguments:
#         dtype: [bool] A given file type fill be force if given (e.g. np.uint16).
#         byteswap: [bool] Byteswap the flat image. False by default.
#     Return:
#         flat_struct: [Flat struct] Structure containing the flat field info.
#     """

#     # Load the flat image
#     flat_img = loadImage(os.path.join(dir_path, file_name), -1)

#     # Change the file type if given
#     if dtype is not None:
#         flat_img = flat_img.astype(dtype)

#     # If the flat isn't a 8 bit integer, convert it to uint16
#     elif flat_img.dtype != np.uint8:
#         flat_img = flat_img.astype(np.uint16)


#     if byteswap:
#         flat_img = flat_img.byteswap()
        

#     # Init a new Flat structure
#     flat_struct = FlatStruct(flat_img, dark=dark)

#     return flat_struct

# def uploadFlat(self, dtype=None, byteswap=True, dark=None):


            

# Apply flat
def applyFlat(img, flat_struct):
    """ Apply a flat field to the image.
    Arguments:
        img: [ndarray] Image to flat field.
        flat_struct: [Flat struct] Structure containing the flat field.
        
    Return:
        [ndarray] Flat corrected image.
    """

    # Check that the input image and the flat have the same dimensions, otherwise do not apply it
    if img.shape != flat_struct.flat_img.shape:
        return img

    input_type = img.dtype

    # Apply the flat
    img = flat_struct.flat_avg*img.astype(np.float64)/flat_struct.flat_img

    # Limit the image values to image type range
    dtype_info = np.iinfo(input_type)
    img = np.clip(img, dtype_info.min, dtype_info.max)

    # Make sure the output array is the same as the input type
    img = img.astype(input_type)

    return img

# Get handle positions in ROI
def getHandlePositions(self):
    """Return the positions of all handles in local coordinates."""
    pos = [self.mapFromScene(self.lines[0].getHandles()[0].scenePos())]
    for l in self.lines:
        pos.append(self.mapFromScene(l.getHandles()[1].scenePos()))
    return pos

###################################################################################################
########################################## PRIMARY CLASS ##########################################
###################################################################################################

class Ui(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):

        # call inherited classes __init__ method
        super(Ui, self).__init__(*args, **kwargs)    
        
        # Load the .ui file
        # uic.loadUi('Camo-S.ui', self)
        uic.loadUi('camo-s-new.ui', self)                
        self.title = "CAMO-S ANALYSIS"
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # display the GUI 
        self.show()                                  

        ###########################################################################################
        ################################ /// GUI MODIFICATIONS /// ################################
        ###########################################################################################

        #################### DIRECT FILE IMAGE VIEW ####################

        # Create the widget
        self.direct_imagewidget = pg.GraphicsView()
        # Set Graphics View to ViewBox                                         
        self.direct_imageframe = pg.ViewBox()
        # Set Graphics view as central widget                                               
        self.direct_imagewidget.setCentralWidget(self.direct_imageframe) 
        # Lock aspect ratio for the frame                   
        self.direct_imageframe.setAspectLocked()        
        # Disable menu                      
        self.direct_imageframe.setMenuEnabled(False)   
        # Invert the image along the y axis                       
        self.direct_imageframe.invertY()
        # Add image item to ViewBox
        self.direct_image = pg.ImageItem()           
        # add item to image frame (ViewBox)                                       
        self.direct_imageframe.addItem(self.direct_image)                                   
        # Location of widget in layout
        self.Direct_layout.addWidget(self.direct_imagewidget, 0, 0)                         

        #################### DIRECT IMAGE HISTOGRAM ####################

        # Create histogram widget
        self.direct_hist = pg.HistogramLUTWidget()   
        # Connect histogram to image in ViewBox                                       
        self.direct_hist.setImageItem(self.direct_image)                                    
        # location of widget in layout
        self.Direct_layout.addWidget(self.direct_hist, 0, 20)                               

        #################### INITIALIZE DIRECT MOUSE ####################

        self.direct_roi = None
        # Change to crosshair cursor in the direct image view widget
        self.direct_imagewidget.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        # Enable mouse click event in the image view widget
        self.direct_image.mousePressEvent = self.getDirectPosition

        #################### DIRECT MARKERS ####################

        # Init affine marker on spectral image
        self.direct_markers = pg.ScatterPlotItem()
        self.direct_markers.setData(pxMode=False, symbol='+', size=15, pen='r', brush='r')
        self.direct_imageframe.addItem(self.direct_markers) 

        #################### DIRECT MARKERS ####################

        # Init affine marker on spectral image
        self.direct_circle = pg.ScatterPlotItem()
        self.direct_circle.setData(pxMode=False, symbol='o', size=50, pen='w', width=5, brush=None)
        self.direct_imageframe.addItem(self.direct_circle) 

        #################### INITIALIZE PLOT MOUSE #####################

        self.Plot.scene().sigMouseClicked.connect(self.mouse_clicked)

        #################### SPECTRAL FILE IMAGE VIEW ####################

        # Create the image widget with graphics view
        self.spectral_imagewidget = pg.GraphicsView()        
        # Set Graphics View to ViewBox                               
        self.spectral_imageframe = pg.ViewBox()                  
        # Set Graphics view as ventral widget                           
        self.spectral_imagewidget.setCentralWidget(self.spectral_imageframe)  
        # Lock aspect ratio               
        self.spectral_imageframe.setAspectLocked()     
        # Disable menu                         
        self.spectral_imageframe.setMenuEnabled(False)
        # Invert image frame along the y axis
        self.spectral_imageframe.invertY()
        # Add image item to ViewBox
        self.spectral_image = pg.ImageItem()           
        # Add item to image frame (ViewBox)                                     
        self.spectral_imageframe.addItem(self.spectral_image)                               
        # Location of widget in layout
        self.Spectral_layout.addWidget(self.spectral_imagewidget, 0, 0)              

        #################### SPECTRAL IMAGE HISTOGRAM ####################

        # Create histogram widget
        self.spectral_hist = pg.HistogramLUTWidget()     
        # Connect histogram to image in ViewBox                                   
        self.spectral_hist.setImageItem(self.spectral_image)       
        # Location of widget in layout
        self.Spectral_layout.addWidget(self.spectral_hist, 0, 50)                           

        ################# INITIALIZE SPECTRAL ROI/MOUSE #################

        # Initalize ROI to None
        self.spectral_roi = None
        # Change to crosshair cursor in the spectral image widget
        self.spectral_imagewidget.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

        #################### INITIALIZE BACKGROUND SETS ####################

        # self.Frame1SpectralStart_linedit.insert("0")
        # self.Frame1SpectralEnd_linedit.insert("10")
        # self.Frame2SpectralStart_linedit.insert("50")
        # self.Frame2SpectralEnd_linedit.insert("60")

        #################### SPECTRAL MARKERS ####################

        # Init affine marker on spectral image
        self.affine_markers = pg.ScatterPlotItem()
        # self.affine_markers.setPen('r')
        # self.affine_markers.setSymbol('o')
        self.affine_markers.setData(pxMode=False, symbol='o', size=10, pen='r', brush='r')
        self.spectral_imageframe.addItem(self.affine_markers)

        # Init projected affine marker  on  spectral  image
        self.proj_affine_markers = pg.ScatterPlotItem()
        # self.proj_affine_markers.setPen('b')
        # self.proj_affine_markers.setSymbol('o')
        self.affine_markers.setData(pxMode=False, symbol='+', size=10, pen='b', brush='b')
        self.spectral_imageframe.addItem(self.proj_affine_markers)  
        
        ################# LOAD SPECTRAL FLAT ####################

        # Init file path and name
        # flat_path = self.FlatPath_linedit.text()
        # flat_name = self.FlatName_linedit.text()

        # self.FlatName_linedit.returnPressed.connect(lambda: self.updateFlatName())

        # Call the function to load the flat
        # if flat_name != '':
        #     self.flat_structure  = loadFlat(flat_path, flat_name)

        ###########################################################################################
        ################################# /// BUTTON TRIGGERS /// #################################
        ###########################################################################################

        ################# DIRECT FILE CONTROL BUTTONS #################

        # Upload direct file 
        self.UploadDirect_button.clicked.connect(self.uploadDirectVid)                      
        # Next direct frame        
        self.NextDirect_button.clicked.connect(self.nextDirectFrame)  
        # Jump ahead 5 frames
        self.ForwardFiveDirect_button.clicked.connect(self.forwardFiveDirectFrames)                      
        # Last direct frame        
        self.LastDirect_button.clicked.connect(self.lastDirectFrame)   
        # Jump back 5 frames
        self.BackFiveDirect_button.clicked.connect(self.backFiveDirectFrames)                  
        # Run affine transform        
        self.Affine_button.clicked.connect(self.affineTransform)
        # Update affine transform
        self.UpdateAffine_button.clicked.connect(self.updateTransform)        
        # Next frame (both direct and spectral)       
        self.NextFrame_button.clicked.connect(self.nextFrame)
        # Last frame (both direct and spectral)   
        self.LastFrame_button.clicked.connect(self.lastFrame)  
        # Next frame set that is as close in time as possible
        self.NextTimeFrame_button.clicked.connect(self.nextTimeFrame) 
        # Last frame set that is as close in time as possible
        self.LastTimeFrame_button.clicked.connect(self.lastTimeFrame)

        ################# SPECTRAL FILE CONTROL BUTTONS #################
    
        # Upload spectral file
        self.UploadSpectral_button.clicked.connect(self.uploadSpectralVid)                  
        # Next spectral frame        
        self.NextSpectral_button.clicked.connect(self.nextSpectralFrame)
        # Jump ahead 5 frames
        self.ForwardFiveSpectral_button.clicked.connect(self.forwardFiveSpectralFrames)                    
        # Last spectral frame         
        self.LastSpectral_button.clicked.connect(self.lastSpectralFrame)
        # Jump back 5 frames
        self.BackFiveSpectral_button.clicked.connect(self.backFiveSpectralFrames)              
        # Make ROI box appear        
        self.SelectSpectralRegion_button.clicked.connect(self.spectralROI)                  
        # Displays image background        
        self.CheckSpectralBackground_button.clicked.connect(self.showSpectralBackground)   
        # Displays selected region        
        self.CheckSpectralRegion_button.clicked.connect(self.showSpectralRegion)           
        # Clear ROI box        
        self.ClearSpectralRegion_button.clicked.connect(self.clearSpectralROI)             
        # Clear the affine transform point
        self.ClearAffine_button.clicked.connect(self.clearAffine)
        # Apply the image flat
        self.RemoveFlat_button.clicked.connect(self.removeSpectralFlat)
        # Auto pick ROI
        self.AutoPick_button.clicked.connect(self.autoPickROI)
        # Auto pick meteor
        self.AutoPickDirect_button.clicked.connect(self.autoPickDirect)

        self.AutoTrackDirect_button.clicked.connect(self.autoTrackDirect)

        ##### Flat
        self.UploadSpectralFlat_button.clicked.connect(self.uploadSpectralFlat)

        ################# PLOTTING BUTTONS #################

        # Plot the measured spectrum    
        self.MeasuredSpec_button.clicked.connect(self.plotMeasuredSpec)
        # Calibrate the spectrum
        self.CalibrateSpectrum_button.clicked.connect(lambda: self.calibrationClicked())              
        # Clear the plot    
        self.Clear_button.clicked.connect(self.clearSpec)


        #################### Elemental Abundance Buttons #################

        self.ResetElements_button.clicked.connect(self.clearSpec)

        ######################## Commands Buttons #########################

        self.Extinction_rollbox.valueChanged.connect(lambda: self.updateExtinctionValue())
        self.Roll_rollbox.valueChanged.connect(lambda: self.updateRollValue())
        self.Lmm_rollbox.valueChanged.connect(lambda: self.updateLmmValue())
        self.HighTemp_rollbox.valueChanged.connect(lambda: self.updateHighTempValue())
        self.LowTemp_rollbox.valueChanged.connect(lambda: self.updateLowTempValue())
        self.Sigma_rollbox.valueChanged.connect(lambda: self.updateSigmaValue())
        self.Hot2WarmRatio_rollbox.valueChanged.connect(lambda: self.updateHot2WarmRatio())

        # Element buttons

        self.Na_button.clicked.connect(self.elementButtonClicked)
        self.Mg_button.clicked.connect(self.elementButtonClicked)
        self.Ca_button.clicked.connect(self.elementButtonClicked)
        self.Fe_button.clicked.connect(self.elementButtonClicked)
        self.K_button.clicked.connect(self.elementButtonClicked)
        self.O_button.clicked.connect(self.elementButtonClicked)
        self.N_button.clicked.connect(self.elementButtonClicked)
        self.N2_button.clicked.connect(self.elementButtonClicked)
        self.Si_button.clicked.connect(self.elementButtonClicked)

        # toggle-able command buttons
        self.HotTempOn_button.setCheckable(True)
        self.WarmTempOn_button.setCheckable(True)
        self.Ions_button.setCheckable(True)
        self.Neutral_button.setCheckable(True)
        self.Respon_button.setCheckable(True)
        self.Extinction_button.setCheckable(True)

        self.HotTempOn_button.clicked.connect(lambda: self.hotTempToggle())
        self.WarmTempOn_button.clicked.connect(lambda: self.warmTempToggle())
        self.Ions_button.clicked.connect(lambda: self.ionsToggle())
        self.Neutral_button.clicked.connect(lambda: self.neutralToggle())
        self.Respon_button.clicked.connect(lambda: self.responsivityToggle())
        self.Extinction_button.clicked.connect(lambda: self.extinctionToggle())

        self.RefreshPlot_button.clicked.connect(self.refreshPlot)

        # initialize the GuralSpectral object
        self.spectral = spectral_library.GuralSpectral(10000, 4500, None, None, None, None)

        # initial setup, that isn't quite clear and will require specification of files and settings and such
        # The config file looks something like the following (the variable name are the ones on the right)
        # Version                             =    1.00       spectral.spconfig.version
        # Spectral Order m for Resp/Extn      =      +1       spectral.spconfig.order4spcalib
        # Plus/Minus # Integration Rows       =       4       spectral.spconfig.rowdelta
        # Min Calib Wavelength (nm)           =   350.0       spectral.spconfig.min_cal_wavelength_nm
        # Max Calib Wavelength (nm)           =   650.0       spectral.spconfig.max_cal_wavelength_nm
        # Step Wavelength (nm)                =     0.6       spectral.spconfig.del_wavelength_nm
        # Min Fitting Wavelength (nm)         =   350.0       spectral.spconfig.min_fit_wavelength_nm
        # Max Fitting Wavelength (nm)         =   650.0       spectral.spconfig.max_fit_wavelength_nm
        # Min Bandwidth to use Spectrum (nm)  =   200.0       spectral.spconfig.minspac_wavelength_nm
        # Gauss Smoothing Kernel sigma (nm)   =    20.0       spectral.spconfig.smooth_bandwidth_nm
        # Faintest Star to process (mV)       =     4.5       spectral.spconfig.faintest_star_vmag
        # Airmass Break Pt Respons/Extinct    =     1.5       airmass_limit
        # Fading memory coef                  =    16.0       fading_coef
        # Coincidence time tolerance (sec)    =    60.0       coin_time_tolerance
        # Min low excitation temperature (K)  =  3000.0       min_lo_exc_temp
        # Max low excitation temperature (K)  =  6500.0       max_lo_exc_temp
        # Step low excitation temperature (K) =    10.0       step_lo_exc_temp
        # Nominal low excitation temp (K)     =  4500.0       nominal_lo_exc_temp
        # Nominal high excitation temp (K)    = 10000.0       nominal_hi_exc_temp
        # Nominal broadening sigma (nm)       =     1.5       nominal_sigma0
        # Grating normal to look angle (deg)  =     8.0       grating_offnormal
        # Default grating roll (deg)          =     0.0       default_roll_angle
        # Default grating pitch (deg)         =     0.0       default_pitch_angle
        # Default grating yaw (deg)           =     0.0       default_yaw_deg
        # Default electron density (m^-3)     = 1.0e+13       default_ne
        # Default hot to warm plasma ratio    = 1.0e-04       default_hot2warm
        # Number of Grating Cameras           =       1       ncams_grating

        noise_multiplier = 0.0 # 0 = no noise, 0.1 = defaults

        spectral_library.readSpectralConfig(self.spectral)
        spectral_library.allocMemory(self.spectral)

        # print("Version: %s" % self.spectral.spconfig.version)
        # print("Spectral order: %s" % self.spectral.spconfig.order4spcalib)
        # print('Nominal low excitation temperature: %s' % self.spectral.spconfig.nominal_lo_exc_temp)

        # Assign camera numbers to the grating structure
        for i in range(spectral_library.MAXGRATINGS):
            self.spectral.spcalib.gratinfo[i].camnum = self.spectral.spconfig.camnum[i]

        camos_camera_index = 0;
        self.spectral.spcalib.gratinfo[camos_camera_index].grating_area_scale = math.cos(self.spectral.spconfig.grating_offnormal_deg * 3.141592654 / 180.0)
        self.spectral.spcalib.gratinfo[camos_camera_index].camnum = 101

        spectral_library.readSpectralCALFile(self.spectral)
        spectral_library.loadElementsData(self.spectral)

        # Testing how to access element info after loading
        # print('test')
        # print(self.spectral.elemdata.nneutrals)
        # print(self.spectral.elemdata.neutral_index[36])
        # print(self.spectral.elemdata.els[0])
        # print(str(self.spectral.elemdata.els[1].element_filename))

        # Update controls based on config
        self.SpectralConfigVersion_label.setText(str(self.spectral.spconfig.version))
        self.SpectralConfigOrder_label.setText(str(self.spectral.spconfig.order4spcalib))
        self.SpectralConfigRowDelta_label.setText(str(self.spectral.spconfig.rowdelta))
        self.SpectralConfigMinCalWavelengthNm_label.setText(str(self.spectral.spconfig.min_cal_wavelength_nm))
        self.SpectralConfigMaxCalWavelengthNm_label.setText(str(self.spectral.spconfig.max_cal_wavelength_nm))
        self.SpectralConfigDelWavelengthNm_label.setText(str(self.spectral.spconfig.del_wavelength_nm))
        self.SpectralConfigMinFitWavelengthNm_label.setText(str(self.spectral.spconfig.min_fit_wavelength_nm))
        self.SpectralConfigMaxFitWavelengthNm_label.setText(str(self.spectral.spconfig.max_fit_wavelength_nm))
        self.SpectralConfigMinspacWavelengthNm_label.setText(str(self.spectral.spconfig.minspan_wavelength_nm))
        self.SpectralConfigSmoothBandwidthNm_label.setText(str(self.spectral.spconfig.smooth_bandwidth_nm))
        self.SpectralConfigFaintestStarMag_label.setText(str(self.spectral.spconfig.faintest_star_vmag))
        self.SpectralConfigAirmassLimit_label.setText(str(self.spectral.spconfig.airmass_limit))
        self.SpectralConfigFadingCoef_label.setText(str(self.spectral.spconfig.fading_coef))
        self.SpectralConfigCoinTimeTolerance_label.setText(str(self.spectral.spconfig.coin_time_tolerance))
        self.SpectralConfigMinLoExcTemp_label.setText(str(self.spectral.spconfig.min_lo_exc_temp))
        self.SpectralConfigMaxLoExcTemp_label.setText(str(self.spectral.spconfig.max_lo_exc_temp))
        self.SpectralConfigStepLoExcTemp_label.setText(str(self.spectral.spconfig.step_lo_exc_temp))
        self.SpectralConfigNominalLoExcTemp_label.setText(str(self.spectral.spconfig.nominal_lo_exc_temp))
        self.LowTemp_rollbox.setValue(int(self.spectral.spconfig.nominal_lo_exc_temp))
        self.SpectralConfigNominalHiExcTemp_label.setText(str(self.spectral.spconfig.nominal_hi_exc_temp))
        self.HighTemp_rollbox.setValue(int(self.spectral.spconfig.nominal_hi_exc_temp))
        self.SpectralConfigNominalSigma0_label.setText(str(self.spectral.spconfig.nominal_sigma0))
        self.Sigma_rollbox.setValue(self.spectral.spconfig.nominal_sigma0)
        self.SpectralConfigGratingOffnormal_label.setText(str(self.spectral.spconfig.grating_offnormal_deg))
        self.SpectralConfigDefaultRollAngle_label.setText(str(self.spectral.spconfig.default_roll_deg))
        self.SpectralConfigDefaultPitchAngle_label.setText(str(self.spectral.spconfig.default_pitch_deg))
        self.SpectralConfigDefaultYawDeg_label.setText(str(self.spectral.spconfig.default_yaw_deg))
        self.SpectralConfigDefaultNe_label.setText(str(self.spectral.spconfig.default_ne))
        self.SpectralConfigDefaultHot2warm_label.setText(str(self.spectral.spconfig.default_hot2warm))
        self.Hot2WarmRatio_rollbox.setValue(self.spectral.spconfig.default_hot2warm)
        self.SpectralConfigNcamsGrating_label.setText(str(self.spectral.spconfig.ncams_grating))

        self.elementButtons = []
        self.elementDeets = [] # element name, fit state, atomic number, index
        self.kelem = {}
        self.fitState = {}
        self.elementButtons.append(self.Na_button)
        self.elementDeets.append(['Na',0,11,spectral_library.GuralSpectral.getElementIndex(self.spectral, 11)])
        self.elementButtons.append(self.Mg_button)
        self.elementDeets.append(['Mg',0,12,spectral_library.GuralSpectral.getElementIndex(self.spectral, 12)])
        self.elementButtons.append(self.Ca_button)
        self.elementDeets.append(['Ca',0,20,spectral_library.GuralSpectral.getElementIndex(self.spectral, 20)])
        self.elementButtons.append(self.Fe_button)
        self.elementDeets.append(['Fe',0,26,spectral_library.GuralSpectral.getElementIndex(self.spectral, 26)])
        self.elementButtons.append(self.K_button)
        self.elementDeets.append(['K',0,19,spectral_library.GuralSpectral.getElementIndex(self.spectral, 19)])
        self.elementButtons.append(self.O_button)
        self.elementDeets.append(['O',0,8,spectral_library.GuralSpectral.getElementIndex(self.spectral, 8)])
        self.elementButtons.append(self.N_button)
        self.elementDeets.append(['N',0,7,spectral_library.GuralSpectral.getElementIndex(self.spectral, 7)])
        self.elementButtons.append(self.N2_button)
        self.elementDeets.append(['N2',0,7,spectral_library.GuralSpectral.getElementIndex(self.spectral, 7)])
        self.elementButtons.append(self.Si_button)
        self.elementDeets.append(['Si',0,14,spectral_library.GuralSpectral.getElementIndex(self.spectral, 14)])

        i = 0
        for i in range(len(self.elementDeets)):
            self.kelem[self.elementDeets[i][0]] = self.elementDeets[i][3]

        # ============================================================================
        #    At this stage, you should extract an integrated spectrum from the 
        #       imagery (for a frame or aggregated frames) that is to be fit and
        #       place the spectrum in the vector "spectrum.integ_spec" at the 
        #       corresponding vector of wavelengths of spcal.wavelength_nm.
        #       NOTE: For the purposes of this example we will infill integ_spec
        #             later with a model spectrum plus noise to be fit.
        # 
        #    You will also need the corresponding metadata of the event such as
        #       heights above earth's surface, range to the meteor, the approach 
        #       angle (look direction angle off the radiant), entry velocity, 
        #       altitude angle (elevation above the horizon).   
        # ============================================================================

        # self.vinfinity_kmsec = 40.0     # km/sec
        # self.approach_angle_radians = 55.0 * 3.141592654 / 180.0
        # self.earth_radius_km = 6378.16  # WGS84
        # self.site_height_km = 0.2       # Above WGS84 Earth surface
        # self.meteor_height_km = 85.0    # Above WGS84 Earth surface
        # self.altitude_deg = 45.0        # elevation angle above horizon
        # Rsin = self.earth_radius_km * math.sin(self.altitude_deg * 3.141592654 / 180.0)
        # self.meteor_range_km = math.sqrt( Rsin * Rsin + 2.0 * self.earth_radius_km * self.meteor_height_km + self.meteor_height_km * self.meteor_height_km) - Rsin

        #========== Set the grating camera with its scaling factor based off the config file input. 
        #           CAMO-S has one grating camera so only index [0] is set. 
        #           On other systems this scaling factor varies with each event due the different angle
        #           of incidence of the light path onto the grating.
        camos_camera_index = 0
        self.spectral.spcalib.gratinfo[camos_camera_index].grating_area_scale = math.cos(self.spectral.spconfig.grating_offnormal_deg * 3.141592654 / 180.0)
        # print('Grating area scale: %s' % self.spectral.spcalib.gratinfo[camos_camera_index].grating_area_scale)

        #========== Set user adjustable values in the elemdata structure to their starting defaults
        #              such as sigma, temperatures, electron density, hot-to-warm, airmass factor
        spectral_library.adjustableParametersDefaults(self.spectral)


    ###############################################################################################
    ###################################### /// FUNCTIONS /// ######################################
    ###############################################################################################
    def calibrationClicked(self):
        self.window = QtWidgets.QMainWindow()
        self.ui = Ui_CalibrationDialog()
        self.ui.setupUi(self.window)
        self.ui.CalculateScale_button.clicked.connect(self.calculateScale)
        self.ui.UpdateScale_button.clicked.connect(self.updateScale)
        self.window.show()

    def calculateScale(self):
        print(self.ui.Wave1_edit.text())
        print('Yay!')
        old_scale = 2.85
        w1 = int(self.ui.Wave1_edit.text())
        w2 = int(self.ui.Wave2_edit.text())
        x1 = float(self.ui.CalibX1_label.text())
        x2 = float(self.ui.CalibX2_label.text())
        new_scale = old_scale / np.abs((w2-w1)/(x2-x1))
        self.ui.NewScale_rollbox.setValue(new_scale)
        # self.SpectralScale_rollbox.setValue(new_scale)
        self.ui.UpdateScale_button.setEnabled(True)

    def updateScale(self):
        self.SpectralScale_rollbox.setValue(self.ui.NewScale_rollbox.value())
        self.clearSpec
        self.plotMeasuredSpec

    def mouse_clicked(self, evt):

        vb = self.Plot.plotItem.vb
        scene_coords = evt.scenePos()
        if self.Plot.sceneBoundingRect().contains(scene_coords):
            mouse_point = vb.mapSceneToView(scene_coords)
            print(f'clicked plot X: {mouse_point.x()}, Y: {mouse_point.y()}, event: {evt}')
            self.statusBar.showMessage(f'clicked plot X: {mouse_point.x()}, Y: {mouse_point.y()}')

            try:
                if self.ui.CalibX1_label.text() == 'not set':
                    global num_clicks
                    num_clicks = 0
                if num_clicks == 0:
                    self.ui.CalibX1_label.setText(str(mouse_point.x()))
                    self.statusBar.showMessage('Setting X1 to %f' % mouse_point.x())
                    num_clicks = 1
                else:
                    self.ui.CalibX2_label.setText(str(mouse_point.x()))
                    self.statusBar.showMessage('Setting X2 to %f' % mouse_point.x())
                    num_clicks = 0
            except:
                pass

    def plotElement(self, event):

        scaled_element_array = np.zeros(len(self.element_array))

        # # Scaling parameters
        # s = 2.85 # px/nm
        # nm0 = 410 # nm

        # for i in range(len(scaled_element_array)):
        #     nmt = (((i-self.x) / s) + nm0)
        #     scaled_element_array = np.append(scaled_element_array, nmt)

        # length = len(scaled_element_array)
        # middle_index = length // 2

        # pen = pg.mkPen('b', width=2)
        # self.Plot.plot(self.element_array[:,0], self.element_array[:,1], pen=pg.mkPen('b', width=3))
        # pen = pg.mkPen('r', width=1)

        # Na Element number is 11
        # K Element number is 19
        # Mg Element number is 12
        # O Element number is 8
        # N2 Element number is 7
        # Si Element number is 14
        # Fe Element number is 26
        # Ca Element number is 20
        # N Element number is 7

        if self.elemName == 'Na':
            pen_color = (0,9)
        elif self.elemName == 'K':
            pen_color = (1,9)
        elif self.elemName == 'Mg':
            pen_color = (2,9)
        elif self.elemName == 'O':
            pen_color = (3,9)
        elif self.elemName == 'N2':
            pen_color = (4,9)
        elif self.elemName == 'Si':
            pen_color = (5,9)
        elif self.elemName == 'Fe':
            pen_color = (6,9)
        elif self.elemName == 'Ca':
            pen_color = (7,9)
        elif self.elemName == 'N':
            pen_color = (8,9)
        else:
            pen_color = 'w' 

        plotName = str(self.elemName)

        try: globals()[plotName]
        except KeyError:  globals()[plotName] = None

        if globals()[plotName] is None:
            # print('plotName is undefined')
            globals()[plotName] = self.Plot.plot(self.element_array[:,0], self.element_array[:,2], pen=pg.mkPen(pen_color, width=3))
            # print('Plotting element for the first time... %s' % self.elemName)
        else:
            # print('plotName is defined')
            globals()[plotName].setData(self.element_array[:,0], self.element_array[:,2])
            # print('Updated element data')

        

    def refreshPlot(self):
        # self.spectral.elemdata.
        # print('Hot2Warm: %s' % self.spectral.elemdata.hot2warm)
        self.spectral.spconfig.default_hot2warm = self.Hot2WarmRatio_rollbox.value()
        self.spectral.elemdata.hot2warm = self.Hot2WarmRatio_rollbox.value()

        # print('Hot2Warm: %s' % self.spectral.elemdata.hot2warm)
        # print('Sigma0: %s' % self.spectral.elemdata.sigma0)
        self.spectral.elemdata.sigma0 = self.Sigma_rollbox.value()
        # print('Sigma0: %s' % self.spectral.elemdata.sigma0)
        # self.spectral.changeBroadening(10)

        spectral_library.GuralSpectral.plasmaVolumes(self.spectral)
        spectral_library.GuralSpectral.computeWarmPlasmaSpectrum(self.spectral)
        spectral_library.GuralSpectral.computeHotPlasmaSpectrum(self.spectral)
        spectral_library.GuralSpectral.extinctionModel(self.spectral)
        # spectral_library.GuralSpectral.extinctionModel(self.spectral)

        self.element_array = np.zeros((self.spectral.spcalib.nwavelengths,3))
        for i in range(self.spectral.spcalib.nwavelengths):
            self.element_array[i][0] = self.spectral.spcalib.wavelength_nm[i]
            self.element_array[i][1] = self.spectral.elemdata.els[self.elemIndex].speclo[i]
            self.element_array[i][2] = self.spectral.elemdata.els[self.elemIndex].spechi[i]


        self.element_array[:,1] = self.element_array[:,1] * 10**self.Scale_rollbox.value()
        self.element_array[:,2] = self.element_array[:,2] * 10**self.Scale_rollbox.value()
        # print(np.max(self.element_array[:,0]))
        # print(np.max(self.element_array[:,1]))
        # print(np.max(self.element_array[:,2]))
        # print(np.shape(self.element_array))
        # print(np.max(scaled_spectral_profile))
        # self.calculateElementSpectrum()
        self.plotElement(self)
        # print('Plot refreshed...')
        # print('Max element value: %s %s' % (max(self.element_array[:,1]), max(self.element_array[:,2])))

    def calculateElementSpectrum(self):
        #========== If any of the input arguments in the call below to PlasmaVolumes changes
        #              at a later time, you must call PlasmaVolumes again to infill the  
        #              elemdata structure values for height, range, and volumes. 
        #              For example, a different frame (height and range) is to be 
        #              processed, or the user adjusts the hot-to-warm ratio for 
        #              fitting purposes.
        spectral_library.GuralSpectral.plasmaVolumes(self.spectral)

        #========== Compute the model for extinction and the airmass given the event's metadata.
        #           You may want to update for each altitude change or keep it fixed for all frames.
        spectral_library.GuralSpectral.extinctionModel(self.spectral)

        #========== Zero all the elemental abundances and #atoms
        #           Set all element fitting flags to not selected for fitting = FITLESS 
        #           Compute Jones 1997 fraction of ionized atoms Beta = n+ / ( n+ + no ) = function( Vinf )
        spectral_library.GuralSpectral.resetAllElementalAbudances(self.spectral)

        # #========== Obtain model spectra for warm and hot temperature plasmas
        # # self.spectral.elemdata.els[kelem_Fe].user_fitflag = FITTING
        spectral_library.GuralSpectral.elemFitting(self.spectral, self.elemIndex)
        spectral_library.GuralSpectral.computeWarmPlasmaSpectrum(self.spectral)
        spectral_library.GuralSpectral.computeHotPlasmaSpectrum(self.spectral)

        # spectral_library.WriteSpectrum("spectral_library/DriverOutputFiles/FeModelSpectra_LoHi.txt", self.spectral.spcalib.nwavelengths, self.spectral.spcalib.wavelength_nm, self.spectral.elemdata.els[kelem_Fe].speclo, self.spectral.elemdata.els[kelem_Fe].spechi)
        spectral_library.GuralSpectral.writeSpectrum(self.spectral, self.elemIndex)
        # print(self.spectral.spcalib.nwavelengths)
        # print('test')

        self.element_array = np.zeros((self.spectral.spcalib.nwavelengths,3))
        for i in range(self.spectral.spcalib.nwavelengths):
            self.element_array[i][0] = self.spectral.spcalib.wavelength_nm[i]
            self.element_array[i][1] = self.spectral.elemdata.els[self.elemIndex].speclo[i]
            self.element_array[i][2] = self.spectral.elemdata.els[self.elemIndex].spechi[i]

        # print('Max element value: %s' % max(self.element_array[:,2]))

        # print(self.element_array[300][1])
        # print(self.spectral.elemdata.els[self.elemIndex].speclo[1])
        # print(self.spectral.elemdata.els[self.elemIndex].spechi[1])


    def elementButtonClicked(self):

        # Detect whether shift key is held down
        mods = QtGui.QApplication.keyboardModifiers()
        isShiftPressed = mods & QtCore.Qt.ShiftModifier
        # print("Shift? %s" % bool(isShiftPressed))
        if bool(isShiftPressed) == True:
            self.sender().setStyleSheet('background-color:#FFFFFF;font:bold')

        self.buttonClicked = self.sender().objectName()
      
        self.elemName = str(self.buttonClicked).split('_')[0]
        self.buttonIndex = self.elementButtons.index(self.sender())
        self.elemNumber = self.elementDeets[self.buttonIndex][2]
        self.elemIndex = self.elementDeets[self.buttonIndex][3]

        # print('Button name is %s' % str(self.buttonClicked))
        # # print('Button index is %s' % self.buttonIndex)
        # # print('Element index is %s' % self.elemIndex)
        # print('Element number is %s' % self.elemNumber)

        if self.elementDeets[self.buttonIndex][1] < 2:
            self.elementDeets[self.buttonIndex][1] += 1
        else:
            self.elementDeets[self.buttonIndex][1] = 0
            spectral_library.GuralSpectral.removeElemFromModel(self.spectral, self.elemNumber)
            print('Removed element from Fit')
            self.statusBar.showMessage('Unlocked %s fit' % self.elemName,2000)

        if self.elementDeets[self.buttonIndex][1] == 1:
            self.sender().setStyleSheet('background-color:#FFFF00;color:#000000;')
            self.statusBar.showMessage('Ready to fit %s' % self.elemName,2000)

            #========== Obtain model spectra for Iron for warm and hot temperature plasmas
            # self.spectral.elemdata.els[kelem_Fe].user_fitflag = FITTING
            # spectral_library.GuralSpectral.elemFitting(self.spectral, self.kelem[elemName])
            # spectral_library.GuralSpectral.computeWarmPlasmaSpectrum(self.spectral)
            # spectral_library.GuralSpectral.computeHotPlasmaSpectrum(self.spectral)
            self.calculateElementSpectrum()
            self.plotElement(self)

        elif self.elementDeets[self.buttonIndex][1] == 2:
            self.sender().setStyleSheet('background-color:#00FF00;color:#000000;')
            spectral_library.GuralSpectral.lockElemFit(self.spectral, self.elemNumber)
            print('Added element to Fit')
            self.statusBar.showMessage('Locked %s fit' % self.elemName,2000)
        else:
            self.sender().setStyleSheet('background-color:#FFFFFF;color:#000000;')

        self.fitlessElems = []
        self.fittingElems = []
        self.lockedElems = []

        i = 0
        for i in range(len(self.elementDeets)):
            self.fitState[self.elementDeets[i][0]] = self.elementDeets[i][1]



    ################# DIRECT FILE CONTROL FUNCTIONS #################

    # Upload direct .vid file
    # def uploadDirectVid(self):
    #     """
    #     Uploads the direct video to the GUI.
    #     Uses readVid function from wmpl.
    #     Will display 0th frame first, unless script is changed manually.
    #     """
    
    #     # File path and name
    #     direct_path = self.DirectFilePath_linedit.text()
    #     print('Direct path is %s' % direct_path)
    #     direct_name = self.DirectFileName_linedit.text()
        
    #     # Read in the .vid file
    #     self.direct_vid = readVid(direct_path, direct_name)
    #     # Set frame number to be displayed
    #     self.direct_currentframe = 0
    #     # Define length of video in frames
    #     self.direct_vidlength = len(self.direct_vid.frames)

    #     # Update direct frame image view
    #     self.updateDirectFrames()

    def uploadDirectVid(self):

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)

        if dlg.exec():
            direct_file_name = dlg.selectedFiles()

            if direct_file_name[0].endswith('.vid'):
                # print(direct_file_name)
                direct_path = os.path.split(direct_file_name[0])[0]
                direct_name = os.path.split(direct_file_name[0])[1]

                # self.DirectFilePath_linedit.setText(direct_path)
                # self.DirectFileName_linedit.setText(direct_name)

                self.DirectFileName_label.setText('Direct camera file: ' + os.path.split(direct_file_name[0])[1])

                self.direct_vid = readVid(direct_path, direct_name)
                self.direct_currentframe = int(len(self.direct_vid.frames)/2)
                self.direct_vidlength = len(self.direct_vid.frames)

                self.updateDirectFrames()

                self.AutoPickDirect_button.setEnabled(True)
                self.AutoTrackDirect_button.setEnabled(True)
                self.ManualPickDirect_button.setEnabled(True)
                self.ClearPicksDirect_button.setEnabled(True)
            else:
                pass

    # Update direct frame
    def updateDirectFrames(self):
        """
        Updates frame shown in the direct file image view. 
        Updates time stamp and frame number. 
        Adjusts image levels.
        """

        # Set frame to be displayed
        self.direct_frame = self.direct_vid.frames[self.direct_currentframe]
        self.direct_frame_img = self.direct_frame.img_data

        # Display time
        self.dt = unixTime2Date(self.direct_frame.ts, self.direct_frame.tu, dt_obj=False)
        # print(self.dt)
        # self.dt = str(self.dt)
        self.DirectTime_label.setText(' at ' + str(self.dt[3]) + ':' + str(self.dt[4]) + \
         ':' + str(self.dt[5]) + '.' + str(self.dt[6]) + 'UT on ' + str(self.dt[0]) + '/' + \
         str(self.dt[1]) + '/' + str(self.dt[2]))
        self.update()

        # Display frame number
        # self.DirectFrame_label.setNum(self.direct_currentframe)

        self.DirectFrame_label.setText('Frame # ' + str(self.direct_currentframe))
        # self.DirectFrame_label.setText('Viewing frame #' + self.direct_currentframe)
        self.update()

        # Set image levels
        minv = np.percentile(self.direct_frame_img, 0.1)
        maxv = np.percentile(self.direct_frame_img, 99.95)
        gamma = 1

        # Create an image with properly adjusted levels
        self.direct_frame_img = adjustLevels(self.direct_frame_img, minv, gamma, maxv, scaleto8bits=True)
        
        # Set the image to be displayed
        self.direct_image.setImage(self.direct_frame_img.T)

    # Move to next Direct frame
    def nextDirectFrame(self):
        """
        Increases the direct frame number by 1 frame to show the next frame.
        """

        # Increase frame number by one
        self.direct_currentframe += 1
        self.direct_currentframe = self.direct_currentframe%self.direct_vidlength
        
        # Update frame shown in region
        self.updateDirectFrames()

    def forwardFiveDirectFrames(self):
        """
        Increases the direct frame number by 1 frame to show the next frame.
        """

        # Increase frame number by one
        self.direct_currentframe += 5
        self.direct_currentframe = self.direct_currentframe%self.direct_vidlength
        
        # Update frame shown in region
        self.updateDirectFrames()

    # Move to last Direct frame
    def lastDirectFrame(self):
        """
        Decrease the direct frame number by 1 frame to show the previous frame.
        """

        # Decrease frame number by one
        self.direct_currentframe -= 1
        self.direct_currentframe = self.direct_currentframe%self.direct_vidlength
        
        # Update frame shown in region
        self.updateDirectFrames()

    def backFiveDirectFrames(self):
        """
        Decrease the direct frame number by 1 frame to show the previous frame.
        """

        # Decrease frame number by one
        self.direct_currentframe -= 5
        self.direct_currentframe = self.direct_currentframe%self.direct_vidlength
        
        # Update frame shown in region
        self.updateDirectFrames()

    # Get position of the mouse
    def getDirectPosition(self, event):
        """
        Will display the coordinates of a mouse click in the direct image view.
        Information will be updated each time the mouse is clicked within the direct image.
        """

        # Set x and y coordinates of click
        self.dir_x = event.pos().x()
        self.dir_y = event.pos().y()

        # Update label with new click coordinates
        self.DirectXYCoordsDisplay_label.setText('Mouse coords: ( %d : %d )' % (self.dir_x, self.dir_y))

    # Run the affine transform, plot point on spectral image
    def affineTransform(self):
        """
        Runs affine transform from a given point on the direct image
        to a corresponding point on the spectral image, with information 
        from getDirectPosition. 

        Sets data for the affine_markers, and displays the point on the 
        spectral image.
        """
        dlg = QFileDialog(filter="Affine files (*.aff)")
        dlg.setFileMode(QFileDialog.AnyFile)

        if dlg.exec():
            scale_file_name = dlg.selectedFiles()
            # print(scale_file_name)
        
        # Scale plate file path
        scale_dir_path = "."
        # scale_file_name = "direct_spectral_20210526_02J.aff"

        # Load the scale plate
        self.scale = loadScale(scale_dir_path, scale_file_name[0])

        # Enable the update button
        self.UpdateAffine_button.setEnabled(True)

        # Convert image (X, Y) to encoder (Hu, Hv)
        self.hu, self.hv = plateScaleMap(self.scale, self.dir_x, self.dir_y)

        # Set data for markers and plot on 
        self.affine_markers.setData(x = [self.hu], y = [self.hv])

    def updateTransform(self):
        deltaX = int(self.DeltaX_edit.text())
        deltaY = int(self.DeltaY_edit.text())
        self.hu, self.hv = plateScaleMap(self.scale, self.dir_x + deltaX, self.dir_y + deltaY)
        self.affine_markers.setData(x = [self.hu], y = [self.hv])

    ################# SPECTRAL FILE CONTROL FUNCTIONS #################

    # Upload spectral .vid file
    # def uploadSpectralVid(self):
    #     """
    #     Uploads the direct video to the GUI.
    #     Uses readVid function from wmpl.
    #     Will display 0th frame first, unless script is changed manually.
    #     """

    #     # File path and name
    #     # spectral_path = self.SpectralFilePath_linedit.text()
    #     # spectral_name = self.SpectralFileName_linedit.text()
        
    #     # Read in the .vid file
    #     self.spectral_vid = readVid(spectral_path, spectral_name)

    #     # Initialize the current frame
    #     self.spectral_currentframe = 0
    #     self.spectral_vidlength = len(self.spectral_vid.frames)

    #     # Update display
    #     self.updateSpectralFrames()

    def uploadSpectralFlat(self, dtype=None, byteswap=True, dark=None):

        dlg = QFileDialog(filter='PNG files (*.png)')
        dlg.setFileMode(QFileDialog.AnyFile)

        if dlg.exec():
            flat_file_name = dlg.selectedFiles()
            
            if flat_file_name[0].endswith('.png'):
                # print(flat_file_name[0])
               
                # Load the flat image
                flat_img = loadImage(flat_file_name[0], -1)

                # # Change the file type if given
                # if dtype is not None:
                #     flat_img = flat_img.astype(dtype)
                #  # If the flat isn't a 8 bit integer, convert it to uint16
                # elif flat_img.dtype != np.uint8:
                #     flat_img = flat_img.astype(np.uint16)

                if flat_img.dtype != np.uint8:
                    flat_img = flat_img.astype(np.uint16)

                if byteswap:
                    flat_img = flat_img.byteswap()
            
                # plt.figure()
                # plt.imshow(flat_img)
                # plt.show()

                # Init a new Flat structure
                self.flat_structure = FlatStruct(flat_img, dark=dark)
            else:
                pass

    def uploadSpectralVid(self):

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)

        if dlg.exec():
            spectral_file_name = dlg.selectedFiles()

            if spectral_file_name[0].endswith('.vid'):
                # print(spectral_file_name)
                spectral_path = os.path.split(spectral_file_name[0])[0]
                spectral_name = os.path.split(spectral_file_name[0])[1]

                # self.DirectFilePath_linedit.setText(direct_path)
                # self.DirectFileName_linedit.setText(direct_name)

                self.SpectralFileName_label.setText('Spectral camera file: ' + os.path.split(spectral_file_name[0])[1])

                self.spectral_vid = readVid(spectral_path, spectral_name)
                self.spectral_currentframe = int(len(self.spectral_vid.frames)/2)
                self.spectral_vidlength = len(self.spectral_vid.frames)

                self.updateSpectralFrames()
                self.FlattenSpectral_button.setEnabled(True)
                self.AutoPick_button.setEnabled(True)
                self.AutoTrackSpectral_button.setEnabled(True)
                self.SelectSpectralRegion_button.setEnabled(True)
                self.ClearSpectralRegion_button.setEnabled(True)
                self.CheckSpectralRegion_button.setEnabled(True)
                self.CheckSpectralBackground_button.setEnabled(True)
            else:
                pass

    # Update spectral frame
    def updateSpectralFrames(self):
        """
        Updates frame shown in the direct file image view. 
        Updates time stamp and frame number. 
        Applies image flat.
        """

        # Set frame 
        self.spectral_frame = self.spectral_vid.frames[self.spectral_currentframe]
        self.spectral_frame_img = self.spectral_frame.img_data

        # Display time
        self.st = unixTime2Date(self.spectral_frame.ts, self.spectral_frame.tu, dt_obj=False)
        # self.st = str(self.st)
        # self.SpectralTime_label.setText(self.st)
        self.SpectralTime_label.setText(' at ' + str(self.st[3]) + ':' + str(self.st[4]) + \
         ':' + str(self.st[5]) + '.' + str(self.st[6]) + 'UT on ' + str(self.st[0]) + '/' + \
         str(self.st[1]) + '/' + str(self.st[2]))
        self.update()

        # Display frame number
        # self.SpectralFrame_label.setNum(self.spectral_currentframe)
        self.SpectralFrame_label.setText('Frame # ' + str(self.spectral_currentframe))
        self.update()

        # Call the function to apply the flat
        # if self.flat_structure is not None: 
        #     self.spectral_frame_img = applyFlat(self.spectral_frame_img, self.flat_structure)

        # Set spectral image
        self.spectral_image.setImage(self.spectral_frame_img.T) 

    # Click to next Spectral frame
    def nextSpectralFrame(self):
        """
        Increases the spectral frame number by 1 to show the next frame
        """

        # Increase spectral frame number by 1
        self.spectral_currentframe += 1
        self.spectral_currentframe = self.spectral_currentframe%self.spectral_vidlength
        
        # Update frame shown in region
        self.updateSpectralFrames() 

    def forwardFiveSpectralFrames(self):
        """
        Increases the spectral frame number by 1 to show the next frame
        """

        # Increase spectral frame number by 1
        self.spectral_currentframe += 5
        self.spectral_currentframe = self.spectral_currentframe%self.spectral_vidlength
        
        # Update frame shown in region
        self.updateSpectralFrames() 

    # Click to last Spectral frame
    def lastSpectralFrame(self):
        """
        Decrease the spectral frame number by 1 to show the previous frame.
        """

        # Decrease frame number by 1
        self.spectral_currentframe -= 1
        self.spectral_currentframe = self.spectral_currentframe%self.spectral_vidlength
        
        # Update frame shown in region
        self.updateSpectralFrames()

    def backFiveSpectralFrames(self):
        """
        Decrease the spectral frame number by 1 to show the previous frame.
        """

        # Decrease frame number by 1
        self.spectral_currentframe -= 5
        self.spectral_currentframe = self.spectral_currentframe%self.spectral_vidlength
        
        # Update frame shown in region
        self.updateSpectralFrames()

    # Introduces ROI box
    def spectralROI(self):
        """
        Introduces square ROI box on spectral frame. 
        Includes handles to rotate, scale, or translate the ROI. 
        """

        # Introduce ROI, provided ROI is None 
        if self.spectral_roi is None:
            self.spectral_roi = pg.ROI((0,0), size = (100, 100), angle = 0, invertible = False, \
                maxBounds = None, snapSize = 1, scaleSnap = False, \
                    translateSnap = False, rotateSnap = False, \
                        parent = self.spectral_image, \
                            pen = None, movable = True, \
                            rotatable = True, resizable = True, removable = True)
            self.spectral_roi.addRotateHandle([0.5,0.5], [0.25, 0.25])
            self.spectral_roi.addScaleHandle([1,0.5], [0,0])
            self.spectral_roi.addTranslateHandle([0,0.5],  [0,0])
            self.angle = self.spectral_roi.angle()



    def spectralAutoROI(self,width, height, roll, intercept):
        """
        Introduces square ROI box on spectral frame. 
        Includes handles to rotate, scale, or translate the ROI. 
        """
        if self.spectral_roi is not None:
            self.spectral_roi.deleteLater()
            self.spectral_roi = None


        # Introduce ROI, provided ROI is None 
        if self.spectral_roi is None:
            self.spectral_roi = pg.ROI((0,intercept+1/2*height), size = (width, height), angle = roll, invertible = False, \
                maxBounds = None, snapSize = 1, scaleSnap = False, \
                    translateSnap = False, rotateSnap = False, \
                        parent = self.spectral_image, \
                            pen = None, movable = True, \
                            rotatable = True, resizable = True, removable = True)
            self.spectral_roi.addRotateHandle([0.5,0.5], [0.25, 0.25])
            self.spectral_roi.addScaleHandle([1,0.5], [0,0])
            self.spectral_roi.addTranslateHandle([0,0.5],  [0,0])
            self.angle = self.spectral_roi.angle()
    
    def autoTrackDirect(self):
        
        # Set frame to be displayed
        print(self.direct_currentframe)
        # self.direct_frame = self.direct_vid.frames[self.direct_currentframe]
        # self.direct_frame_img = self.direct_frame.img_data

        dimage = self.direct_vid.frames[23].img_data

        plt.imshow(dimage)
        plt.show()


    def autoPickDirect(self):

        dimage = self.direct_frame_img

        # Calculate the global mean and stddev
        global_mean = np.mean(dimage)
        global_stddev = np.std(dimage)
        
        # Change data type to 32 bit
        data = dimage.astype(np.float32)
        # data = dimage

        # Apply a mean filter
        fx = 3
        fy = 3
        data = scipy.ndimage.filters.convolve(data, weights=np.full((fx,fy), 1.0/4))

        # Locate local maxima
        neighborhood_size = 80
        intensity_threshold = 400
        data_max = scipy.ndimage.filters.maximum_filter(data, neighborhood_size)

        maxima = (data == data_max)
        data_min = scipy.ndimage.filters.minimum_filter(data, neighborhood_size)
        diff = ((data_max - data_min) > intensity_threshold)

        maxima[diff == 0] = 0

        # Find and label the maxima
        labeled, num_objects = scipy.ndimage.label(maxima)

        # Find centres of mass
        xy = np.array(scipy.ndimage.center_of_mass(data, labeled, range(1, num_objects+1)))

        # Unpack coordinates
        y, x = np.hsplit(xy,2)

        x2, y2, amplitude, intensity, sigma_y_fitted, sigma_x_fitted = fitPSF(dimage, global_mean, x, y)

        extractions = np.array(list(zip(x2, y2, amplitude, intensity, sigma_x_fitted, sigma_y_fitted)), dtype=object)

        # np.savetxt('detect.csv', extractions, delimiter=',')

        # # Delete the direct ROI
        # self.direct_roi.deleteLater()

        # # Re-initialize the direct ROI
        # self.direct_roi = None

        self.dir_x = extractions[0,0]
        self.dir_y = extractions[0,1]

        self.direct_markers.setData(x = [self.dir_x], y = [self.dir_y])
        self.direct_circle.setData(x = [self.dir_x], y = [self.dir_y])

        # if self.direct_roi is None:
        #     self.direct_roi = pg.CircleROI((extractions[0,0]-30,extractions[0,1]-30), size = (60, 60), angle = 0, \
        #         maxBounds = None, snapSize = 1, scaleSnap = False, \
        #             translateSnap = False, rotateSnap = False, \
        #                 parent = self.direct_image, \
        #                     pen = None, movable = False, \
        #                     rotatable = False, resizable = False, removable = True)
        # else:
        #     self.direct_roi.deleteLater()
        #     self.direct_roi = None
        #     self.direct_roi = pg.CircleROI((extractions[0,0]-30,extractions[0,1]-30), size = (60, 60), angle = 0, \
        #         maxBounds = None, snapSize = 1, scaleSnap = False, \
        #             translateSnap = False, rotateSnap = False, \
        #                 parent = self.direct_image, \
        #                     pen = None, movable = False, \
        #                     rotatable = False, resizable = False, removable = True)
            # self.direct_roi.addRotateHandle([0.5,0.5], [0.25, 0.25])
            # self.direct_roi.addScaleHandle([1,0.5], [0,0])
            # self.direct_roi.addTranslateHandle([0,0.5],  [0,0])
            # self.angle = self.direct_roi.angle()

        # fig = plt.figure(figsize=(8,4))
        # ax = fig.add_subplot(111)
        # ax.set_xlim(0,dimage.shape[1])
        # ax.set_ylim(0,dimage.shape[0])
        # plt.gca().invert_yaxis()

        # plt.imshow(diff)

        # plt.show()


    def autoPickROI(self):

       # image = imageio.imread('TestSpectrum1.png', as_gray=True)
        image = self.spectral_frame_img

        # fig = plt.figure(figsize=(10,6))
        # ax = fig.add_subplot(111)

        y,x = np.indices(image.shape)

        mae = []
        scores = []
        roll_ransac = []
        m_ransac = []
        b_ransac = []

        for i in range(1,np.amax(image),int(np.amax(image)*0.02)):

            # axins = ax.inset_axes([-0.1,0.8,0.3,0.3])
            # ax.set_xlim(0,image.shape[1])
            # ax.set_ylim(0,image.shape[0])
            # plt.gca().invert_yaxis()

            valid_z = (y.ravel()>0) & (image.ravel()>(400+i))
            x_valid = x.ravel()[valid_z]
            y_valid = y.ravel()[valid_z]
            z_valid = image.ravel()[valid_z]

            if len(z_valid) > 100:
                # sc1 = ax.scatter(x_valid,y_valid, color='yellowgreen', marker='.')
                # sc2 = ax.scatter(x_valid,y_valid, color='gold', marker='.')

                ransac = RANSACRegressor(residual_threshold=5).fit(x_valid.reshape(-1,1), y_valid.reshape(-1,1), sample_weight=z_valid)
                # ransac.fit(x_valid.reshape(-1,1), y_valid.reshape(-1,1), sample_weight=z_valid**2)
                inlier_mask = ransac.inlier_mask_
                outlier_mask = np.logical_not(inlier_mask)

                line_X = np.arange(x_valid.min(), x_valid.max())[:,np.newaxis]
                line_y_ransac = ransac.predict(line_X)

                prediction = ransac.predict(x_valid.reshape(-1,1))

                mae.append(mean_absolute_error(y_valid,prediction))
                scores.append(ransac.score(x_valid.reshape(-1,1), y_valid.reshape(-1,1)))

                # sc1.set_offsets(np.c_[x_valid[inlier_mask], y_valid[inlier_mask]])
                # sc2.set_offsets(np.c_[x_valid[outlier_mask], y_valid[outlier_mask]])

                z = np.polyfit(x_valid,y_valid, w=z_valid, deg=1)
                p = np.poly1d(z)

                x_plot = np.linspace(x_valid.min(), x_valid.max(), 100)
                y_plot = p(x_plot)

                # ax.plot(x_plot, y_plot, '-r', lw=2, label='LR')
                # ax.plot(line_X, line_y_ransac, label='RANSAC')

                # axins.plot(mae, label='MAE')

                # ax.legend(loc='upper right')
                # axins.legend(loc='upper right')

                this_roll = -1*math.degrees(math.atan2((line_y_ransac.max()-line_y_ransac.min()),(line_X.max()-line_X.min())))                
                roll_ransac.append(this_roll)

                this_b = line_y_ransac.max()-((line_y_ransac.max()-line_y_ransac.min())/(line_X.max()-line_X.min()))*line_X.max()
                b_ransac.append(this_b)
                
                # ax.text(int(image.shape[1]/4),-10,f'This roll = {this_roll:.3} degrees')

                if len(mae) > 1:
                    best_roll = roll_ransac[np.argmin(mae)]
                    # ax.text(int(image.shape[1]/2),-10,f'Best roll = {best_roll:.3} degrees')

                    self.Roll_rollbox.setValue(best_roll)

                    x_vals = np.linspace(0,image.shape[1],2)
                    y_vals = b_ransac[np.argmin(mae)]+20+ np.tan(math.radians(best_roll))*x_vals
                    # ax.plot(x_vals, y_vals, '--')

                    self.spectralAutoROI(image.shape[1],20,best_roll,b_ransac[np.argmin(mae)])

            else:
                break
            # print(line_y_ransac.max()-((line_y_ransac.max()-line_y_ransac.min())/(line_X.max()-line_X.min()))*line_X.max())
            # plt.axis('equal')

        #     fig.canvas.draw_idle()
        #     plt.pause(0.01)
        #     ax.cla()

        #     # plt.show()

        # plt.waitforbuttonpress()

        # self.spectralAutoROI(image.shape[1],20,best_roll,b_ransac[np.argmin(mae)])

    # Check image background
    def checkSpectralBackground(self):
        """
        Uses frame sets 1 and 2 to build a spectral background.
        This background will be subtracted from the measured spectrum to reduce noise. 
        Background calculation will include image flat, if one exists. 
        """
        
        # First frame set start
        # self.spectral_background_startframe_beg = int(self.Frame1SpectralStart_linedit.text())
        # # First frame set end
        # self.spectral_background_startframe_end = int(self.Frame1SpectralEnd_linedit.text())
        # # Last frame set start
        # self.spectral_background_lastframe_beg = int(self.Frame2SpectralStart_linedit.text())
        # # Last frame set end
        # self.spectral_background_lastframe_end = int(self.Frame2SpectralEnd_linedit.text())

        self.spectral_background_startframe_beg = 10
        # First frame set end
        self.spectral_background_startframe_end = 20
        # Last frame set start
        self.spectral_background_lastframe_beg = 50
        # Last frame set end
        self.spectral_background_lastframe_end = 60


        # Define frame range
        frame_range = list(range(self.spectral_background_startframe_beg, self.spectral_background_startframe_end))
        frame_range += list(range(self.spectral_background_lastframe_beg, self.spectral_background_lastframe_end))
        
        # Build array 
        self.spectral_background = np.zeros(shape=(len(frame_range), \
            self.spectral_vid.frames[0].img_data.shape[0], self.spectral_vid.frames[0].img_data.shape[1]))

        # Fill array
        for k, i in enumerate(frame_range):
            frame = self.spectral_vid.frames[i].img_data
            self.spectral_background[k] = frame

        # Take median value of each entry, convert to float
        self.spectral_background = np.median(self.spectral_background, axis = 0)
        self.spectral_background = scipy.ndimage.median_filter(self.spectral_background, size = 10)

        # Apply to flat, if flat exists
        if self.flat_structure is not None: 
            self.spectral_background = applyFlat(self.spectral_background.astype(np.uint16), self.flat_structure) 
        
        # Define spectral background array, each entry a float
        self.spectral_background = self.spectral_background.astype(np.float64)

        # plt.figure()
        # plt.imshow(self.spectral_background)
        # plt.show()

    # Makes spectral background appear in a new window
    def showSpectralBackground(self):
        """
        Displays spectral background in a pop-up window for the user. 
        If the user is not satisfied with the background, they can enter
        new frame set numbers and check the background again. 

        This function call is not necessary before plotting. 
        """

        # Calculate spectral background
        self.checkSpectralBackground()

        # Display background in a pop-up window
        # plt.imshow(self.spectral_background, cmap = 'gray')
        # plt.show()

    # Check selected region
    def checkSpectralRegion(self):
        """
        Get the array region in the spectralROI to define the image data.
        """

        # Calculate image background
        self.checkSpectralBackground()

        # Re define image data
        spectral_frame = self.spectral_vid.frames[self.spectral_currentframe]
        spectral_frame_img = spectral_frame.img_data.astype(np.float64) - self.spectral_background
        spectral_frame_img[spectral_frame_img < 0] = 0
        spectral_frame_img = self.spectral_frame_img.astype(np.uint16)

        # Get array region from ROI
        self.spectral_array = self.spectral_roi.getArrayRegion(spectral_frame_img.T, self.spectral_image)

    # Makes ROI appear in a new window
    def showSpectralRegion(self):
        """"
        Displays spectral ROI in a pop-up window for the user. 
        If the user is not satisfied, they can re-adjust the size/angle 
        of the ROI and check again. 

        This function call is not necessary before plotting.
        """

        # Calculate spectral region
        self.checkSpectralRegion()        
        
        # Display region in a pop-up window
        # plt.imshow(self.spectral_array.T,cmap = 'gray')
        # plt.show()

    # Clear ROI box
    def clearSpectralROI(self):
        """
        Clears spectral ROI box from spectral image view. 
        Deletes all associated data. 
        Re-initializes spectral_roi to None, so it can be 
        called again later. 

        This function means only one ROI box can be present
        on the image view at a time.
        """

        # Delete the spectral ROI
        self.spectral_roi.deleteLater()

        # Re-initialize the spectral ROI
        self.spectral_roi = None

    # Clear the affine marker
    def clearAffine(self):
        """
        Clears the affine marker from the spectral image view. 
        Re-initializes the marker so the affine transform function
        can be performed again, with a new marker. 
        """

        # Clear the marker
        self.spectral_imageframe.removeItem(self.affine_markers)

        # Re-initalize
        self.affine_markers = pg.ScatterPlotItem()
        self.affine_markers.setPen('r')
        self.affine_markers.setSymbol('o')
        self.spectral_imageframe.addItem(self.affine_markers)   
    
    # Load spectral flat loadFlat(dir_path, file_name, dtype=None, byteswap=True, dark=None


    # Remove image flat

    def removeSpectralFlat(self):
        """
        Allows user to remove flat from the current frame only. 
        Flat can be restored by moving to next/last frame, and then 
        returning to desired frame. 

        Background and spectrum will still be calculted with flat applied,
        the flat can only be removed for user convenience.
        """

        # Set frame 
        self.spectral_frame = self.spectral_vid.frames[self.spectral_currentframe]
        self.spectral_frame_img = self.spectral_frame.img_data

        # Display time
        self.st = unixTime2Date(self.spectral_frame.ts, self.spectral_frame.tu, dt_obj=False)
        self.st = str(self.st)
        self.SpectralTime_label.setText(self.st)
        self.update()

        # Display frame number
        self.SpectralFrame_label.setNum(self.spectral_currentframe)
        self.update()

        # Set image levels
        minv = np.percentile(self.spectral_frame_img, 0.1)
        maxv = np.percentile(self.spectral_frame_img, 99.95)
        gamma = 1

        # Create an image with properly adjust levels
        spectral_frame_img = adjustLevels(self.spectral_frame_img, minv, gamma, maxv, scaleto8bits=True)

        # Set spectral image
        self.spectral_image.setImage(spectral_frame_img.T)

    ################# JOINT FILE CONTROL FUNCTIONS #################

    # Next frames
    def nextFrame(self):
        """
        Moves both spectral and direct frames forward by 1 frame.
        """

        # Direct frame
        self.nextDirectFrame()

        # Spectral frame
        self.nextSpectralFrame()

    # Last frames
    def lastFrame(self):
        """
        Moves both spectral and direct frames back by 1 frame.
        """
        # Direct frame
        self.lastDirectFrame()

        # Spectral Frame
        self.lastSpectralFrame()

    # Next frames that are as close in time as possible
    def nextTimeFrame(self):
        """
        Finds next frame set that is as close in time as possible.
        Evaluates tenths and hundredths of a second
        portion of timestamp, finds the difference
        between the direct and spectral timestamps, then recognizes the time 
        gap and finds the appropriate method by which to get the next closest
        frames. 

        Does not work if the time gap is too great - user must have the 
        timestamp within 100 milliseconds.
        """

        # Tenths place value of seconds for the direct timestamp
        self.dir_ms_a = int(self.dt[25])
        # Hundredths place value of seconds for the direct timestamp
        self.dir_ms_b = int(self.dt[26])
        # Tenths place value of the seconds for the spectral timestamp
        self.spec_ms_a = int(self.st[25])
        # Hundredths place value of seconds for the spectral timestamp
        self.spec_ms_b = int(self.st[26])

        # Subtract tenths value of direct timestamp from tenths value of spectral timestamp
        self.a = self.dir_ms_a - self.spec_ms_a
        # Repeat above for hundredths
        self.b = self.dir_ms_b - self.spec_ms_b

        # If the tenths values are the same
        if self.a == 0:
            if 0 < self.b < 5:
                self.nextFrame()

            if 5 <= self.b < 9:
                self.nextSpectralFrame()
            
            if 0 >= self.b > -5:
                self.nextSpectralFrame()
                self.nextDirectFrame()
            
            if -5 >= self.b > -10:
                self.nextDirectFrame()
        
        # If the direct timestamp is ahead of the spectral timestamp
        if self.a ==1:

            if self.b == 0:
                self.nextSpectralFrame()
                self.nextSpectralFrame()

            if 0 < self.b < 5:
                self.nextSpectralFrame()
                self.nextSpectralFrame()
            
            if self.b > 5:
                self.nextSpectralFrame()
                self.nextSpectralFrame()
                self.nextSpectralFrame()
            
            if self.b < 0:
                self.nextSpectralFrame()

        # IF the direct timestamp is behind the spectral timestamp
        if self.a == -1:
            
            if self.b == 0:
                self.nextDirectFrame()
                self.nextDirectFrame()

            if 0 < self.b < 5:
                self.nextDirectFrame()
                self.nextDirectFrame()
            
            if self.b > 5:
                self.nextDirectFrame()
                self.nextDirectFrame()
                self.nextDirectFrame()
            
            if self.b < 0:
                self.nextDirectFrame()
        
        # If the direct timestamp is ahead by more than a tenth of a second
        if self.a > 1:

            print ("Time difference too great to apply time lock")

        # If the spectral timestamp is ahead by more than a tenth of a second
        if self.a < -1:
            
            print("Time difference too great to apply time lock")
    
    # Last frames that are as close in time as possible
    def lastTimeFrame(self):
        """
        Finds last frame set that is as close in time as possible.
        Evaluates tenths and hundredths of seconds
        portion of timestamp, finds the difference
        between the direct and spectral timestamps, then recognizes the time 
        gap and finds the appropriate method by which to get the next closest
        frames. 

        Does not work if the time gap is too great - user must have the 
        timestamp within 1 tenth of a second.
        """

        # If the tenths values are the same
        if self.a == 0:

            if 0 < self.b < 5:
                self.lastFrame()

            if 5 <= self.b < 9:
                self.lastSpectralFrame()
            
            if 0 >= self.b > -5:
                self.lastSpectralFrame()
                self.lastDirectFrame()
            
            if -5 >= self.b > -10:
                self.lastDirectFrame()
        
        # If the direct timestamp is ahead of the spectral timestamp
        if self.a ==1:

            if self.b == 0:
                self.lastSpectralFrame()
                self.lastSpectralFrame()

            if 0 < self.b < 5:
                self.lastSpectralFrame()
                self.lastSpectralFrame()
            
            if self.b > 5:
                self.lastSpectralFrame()
                self.lastSpectralFrame()
                self.lastSpectralFrame()
            
            if self.b < 0:
                self.lastSpectralFrame()

        # IF the direct timestamp is behind the spectral timestamp
        if self.a == -1:
            
            if self.b == 0:
                self.lastDirectFrame()
                self.lastDirectFrame()

            if 0 < self.b < 5:
                self.lastDirectFrame()
                self.lastDirectFrame()
            
            if self.b > 5:
                self.lastDirectFrame()
                self.lastDirectFrame()
                self.lastDirectFrame()
            
            if self.b < 0:
                self.lastDirectFrame()
        
        # If the direct timestamp is ahead by more than a tenth of a second
        if self.a > 1:

            print ("Time difference too great to apply time lock")

        # If the spectral timestamp is ahead by more than a tenth of a second
        if self.a < -1:
            
            print("Time difference too great to apply time lock")
           
    ################# PLOTTING FUNCTIONS #################

     # Projects affine marker onto spectrum
    def projectAffine(self):
        """
        Takes the mapped affine marker and projects it onto the spectrum. 
        Uses the scene handles to parameterize the spectrum as a line. 
        """       

        # Obtaion coordinates of ROI handles relative to scene
        self.handles = self.spectral_roi.getSceneHandlePositions()

        # Extract scale and translation  handle information
        scale_handle = list(self.handles[1])
        translate_handle = list(self.handles[2])

        # Extract scale and translation handle positions as QpointF objects
        scale_handle_position  = scale_handle[1]
        translate_handle_position = translate_handle[1]

        # Get equation of line using the two points
        m = (scale_handle_position.y() - translate_handle_position.y() ) / (scale_handle_position.x() - translate_handle_position.x() )

        b1 = scale_handle_position.y() - m*scale_handle_position.x()

        b2 = ((self.hu / m) + self.hv)

        self.x = (b2 - b1) / (m + (1 / m))

        y = m*self.x + b1

    # plot the measured spectrum
    def plotMeasuredSpec(self, event):
        """
        Runs background and region  of interest calculations.
        Converts spectrum from pixels to nanometers. 
        Plots measured spectrum in graph area
        """

        # Check background and set region to be plotted
        self.checkSpectralBackground()
        self.checkSpectralRegion()
        self.projectAffine()
        
        # Set pen  
        pen = pg.mkPen(width = 1)

        # Set spectral profile
        spectral_profile = np.sum(self.spectral_array, axis = 1)
        # print(self.spectral_array.shape)

        # Init array for the scaled profile
        global scaled_spectral_profile
        scaled_spectral_profile = np.zeros(len(spectral_profile))

        # Scaling parameters
        # s = 2.85 # px/nm
        s = self.SpectralScale_rollbox.value() # px/nm
        nm0 = 410 # nm 

        # Calculate wavelength values as they correspond to each pixel
        for i in range(len(scaled_spectral_profile)):
            nmt = (((i - self.x) / s) + nm0)
            scaled_spectral_profile = np.append(scaled_spectral_profile, nmt)

        # Take the part of the array with the desired values
        length = len(scaled_spectral_profile)
        middle_index = length//2
        
        # Reset array
        scaled_spectral_profile = scaled_spectral_profile[middle_index:]

        # Set axis titles 
        self.Plot.setLabel('left', 'Intensity')
        self.Plot.setLabel('bottom', 'Wavelength (nm)')

        # Create the plot
        self.Plot.plot(scaled_spectral_profile, spectral_profile, pen = pen)
        self.Plot.setXRange(np.min(scaled_spectral_profile),np.max(scaled_spectral_profile))
        self.CalibrateSpectrum_button.setEnabled(True)

    # clear the spectrum
    def clearSpec(self,event):
        self.Plot.clear()








    # def updateFlatName(self):
    #     """ update flat structure when FlatName_linedit is selected and enter pressed """
    #     flat_path = self.FlatPath_linedit.text()
    #     flat_name = self.FlatName_linedit.text()

    #     if os.path.exists(os.path.join(flat_path, flat_name)):
    #         self.flat_structure = loadFlat(flat_path, flat_name)



    ##### Command Button Helper Functions  #####

    # def addExtinction(self, increment=0.1):
    #     """ add increment to the current exctinction coefficient value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.AtExtinct_linedit.text()
    #     if not current_value:
    #         current_value = 0.9

    #     # add, while handling variable types and floating point wandering
    #     added_value = float(current_value) + increment
    #     added_value = np.around(added_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.AtExtinct_linedit.setText(str(added_value))
    #     self.updateExtinctionValue()

    # def subExtinction(self, increment=0.1):
    #     """ subtract increment from the current exctinction coefficient value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.AtExtinct_linedit.text()
    #     if not current_value:
    #         current_value = 1.1

    #     # subtract, while handling variable types and floating point wandering
    #     subbed_value = float(current_value) - increment
    #     subbed_value = np.around(subbed_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.AtExtinct_linedit.setText(str(subbed_value))
    #     self.updateExtinctionValue

    # def updateExtinctionValue(self):

    #     extinctionValue = self.AtExtinct_linedit.text()
    #     if extinctionValue:
    #         extinctionValue = float(extinctionValue)
    #     else:
    #         return

        # update GuralSpectral object

    # Modified for spinner - MJM
    def updateExtinctionValue(self):
        self.extinctionValue = self.Extinction_rollbox.value()
        print('Updated extinction vale: %f' % self.extinctionValue)

    # def addRoll(self, increment=0.1):
    #     """ add increment to the current roll value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.Roll_linedit.text()
    #     if not current_value:
    #         current_value = 0.9

    #     # add, while handling variable types and floating point wandering
    #     added_value = float(current_value) + increment
    #     added_value = np.around(added_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.Roll_linedit.setText(str(added_value))
    #     self.updateRollValue()

    # def subRoll(self, increment=0.1):
    #     """ subtract increment from the current roll value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.Roll_linedit.text()
    #     if not current_value:
    #         current_value = 1.1

    #     # subtract, while handling variable types and floating point wandering
    #     subbed_value = float(current_value) - increment
    #     subbed_value = np.around(subbed_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.Roll_linedit.setText(str(subbed_value))
    #     self.updateRollValue()

    # def updateRollValue(self):

    #     rollValue = self.Roll_linedit.text()
    #     if rollValue:
    #         rollValue = float(rollValue)
    #     else:
    #         return

        # update GuralSpectral object

    # Modified for spinner - MJM
    def updateRollValue(self):
        rollValue = self.Roll_rollbox.value()
        # print(rollValue)


    # def addLmm(self, increment=0.1):
    #     """ add increment to the current L/mm value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.Lmm_linedit.text()
    #     if not current_value:
    #         current_value = 0.9

    #     # add, while handling variable types and floating point wandering
    #     added_value = float(current_value) + increment
    #     added_value = np.around(added_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.Lmm_linedit.setText(str(added_value))
    #     self.updateLmmValue()

    # def subLmm(self, increment=0.1):
    #     """ subtract increment from the currentL/mm value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.Lmm_linedit.text()
    #     if not current_value:
    #         current_value = 1.1

    #     # subtract, while handling variable types and floating point wandering
    #     subbed_value = float(current_value) - increment
    #     subbed_value = np.around(subbed_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.Lmm_linedit.setText(str(subbed_value))
    #     self.updateLmmValue()

    # def updateLmmValue(self):

    #     LmmValue = self.Lmm_linedit.text()
    #     if LmmValue:
    #         LmmValue = float(LmmValue)
    #     else:
    #         return

    #     # update GuralSpectral object

    # Modified for spinner - MJM
    def updateLmmValue(self):
        lmmValue = self.Lmm_rollbox.value()
        # print(lmmValue)


    # def addHighTemp(self, increment=100):
    #     """ add increment to the current Temp high value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.HighTemp_linedit.text()
    #     if not current_value:
    #         current_value = 9900

    #     # add, while handling variable types and floating point wandering
    #     added_value = float(current_value) + increment
    #     added_value = np.around(added_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.HighTemp_linedit.setText(str(added_value))
    #     self.updateHighTempValue()

    # def subHighTemp(self, increment=100):
    #     """ subtract increment from the current Temp high value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.HighTemp_linedit.text()
    #     if not current_value:
    #         current_value = 10100

    #     # subtract, while handling variable types and floating point wandering
    #     subbed_value = float(current_value) - increment
    #     subbed_value = np.around(subbed_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.HighTemp_linedit.setText(str(subbed_value))
    #     self.updateHighTempValue()

    # def updateHighTempValue(self):

    #     highTempValue = self.HighTemp_linedit.text()
    #     if highTempValue:
    #         highTempValue = float(highTempValue)
    #     else:
    #         return

    #     # update GuralSpectral object

    # Modified for spinner - MJM
    def updateHighTempValue(self):
        highTempValue = self.HighTemp_rollbox.value()
        # print(highTempValue)


    # def addLowTemp(self, increment=100):
    #     """ add increment to the current Temp low value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.LowTemp_linedit.text()
    #     if not current_value:
    #         current_value = 4400

    #     # add, while handling variable types and floating point wandering
    #     added_value = float(current_value) + increment
    #     added_value = np.around(added_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.LowTemp_linedit.setText(str(added_value))
    #     self.updateLowTempValue()

    # def subLowTemp(self, increment=100):
    #     """ subtract increment from the current Temp low value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.LowTemp_linedit.text()
    #     if not current_value:
    #         current_value = 4600

    #     # subtract, while handling variable types and floating point wandering
    #     subbed_value = float(current_value) - increment
    #     subbed_value = np.around(subbed_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.LowTemp_linedit.setText(str(subbed_value))
    #     self.updateLowTempValue()

    # def updateLowTempValue(self):

    #     lowTempValue = self.LowTemp_linedit.text()
    #     if lowTempValue:
    #         lowTempValue = float(lowTempValue)
    #     else:
    #         return

    #     # update GuralSpectral object

    # Modified for spinner - MJM
    def updateLowTempValue(self):
        lowTempValue = self.LowTemp_rollbox.value()
        # print(lowTempValue)


    # def addSigma(self, increment=0.1):
    #     """ add increment to the current sigma value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.Sigma_linedit.text()
    #     if not current_value:
    #         current_value = 0.9

    #     # add, while handling variable types and floating point wandering
    #     added_value = float(current_value) + increment
    #     added_value = np.around(added_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.Sigma_linedit.setText(str(added_value))
    #     self.updateSigmaValue()

    # def subSigma(self, increment=0.1):
    #     """ subtract increment from the current Sigma value """

    #     # get the current value, and if it is not set, assign it a value
    #     current_value = self.Sigma_linedit.text()
    #     if not current_value:
    #         current_value = 1.1

    #     # subtract, while handling variable types and floating point wandering
    #     subbed_value = float(current_value) - increment
    #     subbed_value = np.around(subbed_value, decimals=6)

    #     # set value and update in GuralSpectral object
    #     self.Sigma_linedit.setText(str(subbed_value))
    #     self.updateSigmaValue()

    # def updateSigmaValue(self):

    #     sigmaValue = self.Sigma_linedit.text()
    #     if sigmaValue:
    #         sigmaValue = float(sigmaValue)
    #     else:
    #         return

    #     # update GuralSpectral object

    def updateSigmaValue(self):
        # self.sigmaValue = self.Sigma_rollbox.value()
        self.spectral.changeBroadening(self.Sigma_rollbox.value())
        # print(self.Sigma_rollbox.value())

    def updateHot2WarmRatio(self):
        self.spectral.changeHot2WarmRatio(self.Hot2WarmRatio_rollbox.value())
        # self.hot2Warm = self.Hot2WarmRatio_rollbox.value()
        # self.spectral.elemdata.hot2warm = self.Hot2WarmRatio_rollbox.value()
        # print(self.spectral.elemdata.hot2warm)


    def hotTempToggle(self):
        """ handle the toggling of the Hot button """
        if self.HotTempOn_button.isChecked():
            pass # do focus
        else:
            pass # do unfocus

    def warmTempToggle(self):
        """ handle the toggling of the Warm button """
        if self.WarmTempOn_button.isChecked():
            pass # do focus
        else:
            pass # do unfocus

    def ionsToggle(self):
        """ handle the toggling of the Ions button """
        if self.Ions_button.isChecked():
            pass # do focus
        else:
            pass # do unfocus

    def neutralToggle(self):
        """ handle the toggling of the Neutral button """
        if self.Neutral_button.isChecked():
            pass # do focus
        else:
            pass # do unfocus

    def responsivityToggle(self):
        """ handle the toggling of the Responsivity button """
        if self.Respon_button.isChecked():
            pass # do focus
        else:
            pass # do unfocus

    def extinctionToggle(self):
        """ handle the toggling of the Extinction button """
        if self.Extinction_button.isChecked():
            pass # do focus
        else:
            pass # do unfocus

###############################################################################################
################################ /// OPEN THE APPLICATION /// #################################
###############################################################################################

app = QtWidgets.QApplication(sys.argv) # create instance of QtWidgets.QApplication
window = Ui()                          # create instance of class
app.exec_()                            # start the application
