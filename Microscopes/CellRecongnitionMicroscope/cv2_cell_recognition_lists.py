'''
@author: Mattia Cattaneo
'''

import cv2
import time
from PIL import Image
import numpy as np
import imageio


def find_cell(img8bit, cell_size): 
    """ 
        Input:
    img8bit: monochrome image, previously converted to 8bit (img8bit)
    cell_size: minimum area of the object to be detected.
        Output:
    cx,cy : list of the coordinates of the centroids of the detected objects 
    selected_contours: list of contours of the detected object (no child contours are detected).  
    """               
    _ret,thresh_pre = cv2.threshold(img8bit,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # ret is the threshold that was used, thresh is the thresholded image.     
    cv2.imshow('thresholded image',thresh_pre)
    kernel  = np.ones((3,3),np.uint8)
    thresh = cv2.morphologyEx(thresh_pre,cv2.MORPH_OPEN, kernel, iterations = 2)
    # morphological opening (remove noise)
    contours, _hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cx = []
    cy = []            
    area = []
    selected_contours =[]
    
    for cnt in contours:
        M = cv2.moments(cnt)
        if M['m00'] >  cell_size:   # (M['m00'] gives the contour area, also as cv2.contourArea(cnt)     
            #extracts image center
            cx.append(int(M['m10']/M['m00']))
            cy.append(int(M['m01']/M['m00']))
            area.append(M['m00']) 
            selected_contours.append(cnt)
        
    return cx, cy, selected_contours
        
        
def create_contours(img8bit, cx, cy, cnt, rect_size):        
    """ Input: 
    img8bit: monochrome image, previously converted to 8bit but with "AUTOLEVELS"
    cx,cy: list of the coordinates of the centroids  
    cnt: list of the contours.
    rect_size: side of the square to be displayed/extracted  
        Output:
    img8bit: RGB image with annotations
    """  
        
    img8bit = cv2.cvtColor(img8bit,cv2.COLOR_GRAY2RGB)      
    
    for indx, val in enumerate(cx):
        
        x = int(cx[indx] - rect_size/2) 
        y = int(cy[indx] - rect_size/2)
     
        w = h = rect_size 
        
        img8bit = cv2.drawContours(img8bit, [cnt[indx]], 0, (0,256,0), 2) 
        
        if indx == 0:
            color = (0,0,256)
        else: 
            color = (256,0,128)
        cv2.rectangle(img8bit,(x,y),(x+w,y+h),color,1)    
        
    return img8bit


def roi_creation (img16bit, cx, cy, rect_size):
    """ Input: 
    img16bit: monochrome (original) image
    cx,cy: list of the coordinates of the centroids  
    rect_size: side of the square to be displayed/extracted  
        Output:
    roi: list of rois
    cx,cy
    """  
    l = img16bit.shape
    roi = []
    indx = 0
    while indx < len(cx):
        x = int(cx[indx] - rect_size/2) 
        y = int(cy[indx] - rect_size/2)
        w = h = rect_size
        
        if x>0 and y>0 and x+w<l[1]-1 and y+h<l[0]-1:
            detail = img16bit [y:y+h, x:x+w]
            roi.append(detail)
            #if the roi is too close to the boundary, it is not saved
            indx+=1
        else:
            del cx[indx]; del cy[indx]
        
    return roi,cx,cy



def create_stack (stack):
    """ Input: 
    stack: series of images to be concatenated to form a real stack (3D numpy matrix)
        Output:
    newstack: the 3D roi of interest ready to be saved
    """  
    for index, val in enumerate(stack):
        if index==2:
            newstack=np.reshape(stack[index],(1,RECT_SIZE,RECT_SIZE))
        if index>2:    # first two elements of the list are not images (they are cx and cy)
            newstack=np.concatenate((newstack,np.reshape(stack[index],(1,RECT_SIZE,RECT_SIZE))))
    return np.uint16(newstack)






RANGE=20    # max tollerable value of the centroids position shift to identify same cells at different frames
RECT_SIZE = 120    # side of ROI that are extracted
MIN_CELL_SIZE = 40*40    # cell area must be at least MIN_CELL_SIZE (px^2) to be detected as a cell
ROI_SCALING = 2    # rescaling factor applied to the ROIs for displaying them larger
path = 'C:\\Users\Mattia Cattaneo\Desktop\Polimi\Magistrale\Tesi\Python\Codes\\'
filename = 'selected_stack'


im = Image.open(path+filename+'.tif')
#im = Image.open('membrane_substack.tif')
h,w = np.shape(im)
#tiffarray = np.zeros((im.n_frames,h,w))

#shown_rois = 0
number_of_roi = 0    # only to give the correct name to the saved tif


stacks=[]    # list of rois to be saved
old_len=[]   # lenght of the roi stacks at the previous cycle


try: #the try block lets you test a block of code for errors
    
    for i in range(im.n_frames-1):
        
        print(i)
        im.seek(i)    # select the image of the stack on which we want to work
        
        im_in = np.array(im)
        elaborated_im = im_in
        elaborated_im = (elaborated_im/256).astype('uint8') 
        
        #t0 = time.time()
        cx, cy, cnts = find_cell(elaborated_im, MIN_CELL_SIZE)
        im_out = create_contours(elaborated_im, cx, cy, cnts, RECT_SIZE)
        rois, cx, cy = roi_creation(im_in, cx, cy, RECT_SIZE)
                
        cv2.imshow('Acquired data', im_out )
        
        
        index=0
        
        # comparison between cell centre
        while index<len(cx):
            index2=0
            while index2<len(stacks):
                if cx[index] in range(stacks[index2][0]-RANGE,stacks[index2][0]+RANGE) and cy[index] in range(stacks[index2][1]-RANGE,stacks[index2][1]+RANGE):
                    stacks[index2].append(rois[index])
                    del rois[index]; del cx[index]; del cy[index]
                    if index2==len(stacks):
                        index-=1
                    if cx==[]:
                        break
                index2+=1
            index+=1
        

    
                    
        lenght = len(stacks)
        
        # new stacks (sub-lists) creation
        for index, val in enumerate(rois):
            stacks.append([cx[index]])     # here we need square brakets (first element)
            stacks[lenght].append(cy[index])    # here no square brakets needed otherwise the element is considered as a list
            stacks[lenght].append(rois[index])
            lenght+=1
        
        
        
        min_len=min(len(stacks),len(old_len))
        index=0

        # save the stacks which didn't change from the previous cycle
        while index < min(len(stacks),len(old_len)):
            if len(stacks[index]) == old_len[index]:    # saving condition    
                newstack=create_stack(stacks[index])
                imageio.mimwrite('roi' + str(number_of_roi) + '.tif', newstack)
                number_of_roi+=1
                del stacks[index]; del old_len[index]
            else:
                old_len[index]=len(stacks[index])    # values update
                index+=1
        
        
        
        oldLenght=len(old_len)
        newLenght=len(stacks)
        
        # old_len values update
        if newLenght > oldLenght:
            for index in range (newLenght-oldLenght):
                position=len(old_len)
                old_len.append(len(stacks[position]))
        # else:
        #     for index in range(oldLenght-newLenght):
        #         position=len(stacks)
        #         del old_len[position]
        
        
        

        #print('elapsed time: ', time.time()-t0) 
        
        
        
        #tiffarray[i,:,:] = im_in    # to save the original acquired images
        
        #This would save the annotated images in the subfolder \Annotated, that must be created
        #cv2.imwrite(path+'Annotated'+'\\'+filename+'\\out\\out'+ str(i)+'.tif', im_out)
            
        '''
        # ROI VISUALIZATION
        if len(rois) == 0:
            roi_resized = np.zeros((ROI_SCALING*RECT_SIZE,ROI_SCALING*RECT_SIZE), dtype ='uint8') # for saving only
            
                
        for index, roi in enumerate(rois):
            
            roi = (roi/256).astype('uint8')

            dim = (int(ROI_SCALING*RECT_SIZE) , int(ROI_SCALING*RECT_SIZE))
        
            brightness = 3    # 3 for selected_stack, 7 for membrane_substack
            contrast = 20     # 20 for selected_stack, 10 for membrane_substack
            roi_rescaled = np.clip(roi.astype('float')*brightness, contrast, 255).astype('uint8')
            #The image is multipliplied by brightness and thresolded at contrast
            #for better visualization only
            
            roi_resized = cv2.resize(roi_rescaled, dim, interpolation = cv2.INTER_AREA)        
            
            win_name = 'roi_' + str(index)
            
            cv2.imshow(win_name,roi_resized)
        
        #This would save the ROIS in the subfolder \Annotated, that must be created
        #cv2.imwrite(path+'Annotated'+'\\'+filename+'\\roi0'+ str(i)+'.tif', roi_resized)
             
        num_rois = len(rois)
        
        # ROIs can be more than 1. The first one [0] is always displayed. 
        # The others are shown only while the cell is detected 
        if num_rois <= shown_rois:
            for index in range(num_rois, shown_rois):
                if index > 0: 
                    cv2.destroyWindow('roi_' + str(index))    
        shown_rois = num_rois
        '''      
        
        cv2.waitKey(10)    # waits the specified ms. Value 0 would stop until key is hitten
        
    
finally:    # the finally block lets you execute code, regardless of the result of the try and except blocks.
    
    cv2.destroyAllWindows()

    # tiffarray=tiffarray.astype('uint8')
    # imageio.mimwrite('prova8bit.tif', tiffarray)