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
    #print(len(contours))
    
    for cnt in contours:
    #   print(len(cnt))           
        M = cv2.moments(cnt)
        if M['m00'] >  cell_size:   # (M['m00'] gives the contour area, also as cv2.contourArea(cnt)     
            #extracts image center
            cx.append(int(M['m10']/M['m00']))
            cy.append(int(M['m01']/M['m00']))
            area.append(M['m00']) 
            selected_contours.append(cnt)
        
    return cx, cy, selected_contours
        
        
def create_contours(cx,cy, img8bit, cnt, rect_size):        
    """ Input: 
    img8bit: monochrome image, previously converted to 8bit
    cx,cy: list of the coordinates of the centroids  
    cnt: list of the contours.
    rect_size: side of the square to be displayed/extracted  
        Output:
    img: RGB image with annotations
    roi: list of the extracted ROIs  
    
    Note: ROIs are not registered and this might be a problem if one wants to save the stack directly  
    """  
        
    img8bit = cv2.cvtColor(img8bit,cv2.COLOR_GRAY2RGB)      
    
    for indx, val in enumerate(cx):
        
    #x,y,w,h = cv2.boundingRect(cnt)
        x = int(cx[indx] - rect_size/2) 
        y = int(cy[indx] - rect_size/2)
     
        w = h = rect_size 
        
        img8bit = cv2.drawContours(img8bit, [cnt[indx]], 0, (0,256,0), 2) 
        
        if indx == 0:
            color = (0,0,256)    #actually it is (0,0,256)
        else: 
            color = (256,0,128)
        cv2.rectangle(img8bit,(x,y),(x+w,y+h),color,1)    
        
    return img8bit


def roi_creation (img16bit, cx, cy, rect_size):
    l = img16bit.shape
    roi = []
    for indx, val in enumerate(cx):
        x = int(cx[indx] - rect_size/2) 
        y = int(cy[indx] - rect_size/2)
        w = h = rect_size
        if x>0 and y>0 and x+w<l[1]-1 and y+h<l[0]-1:
            detail = img16bit [y:y+h, x:x+w]
            roi.append(detail)
            #se siamo troppo al bordo lui blocca l'acquisizione!!!(non salva piu)
    
    return roi



def save_stack (stack):
    for index, val in enumerate(stack):
        if index==2:
            newstack=np.reshape(stack[index],(1,RECT_SIZE,RECT_SIZE))
        if index>2:
            newstack=np.concatenate((newstack,np.reshape(stack[index],(1,RECT_SIZE,RECT_SIZE))))
    newstack=newstack.astype('uint16')
    return newstack




RANGE=20
RECT_SIZE = 120 #side of ROI that are extracted
MIN_CELL_SIZE = 40*40 #cell area must be at least MIN_CELL_SIZE (px^2) to be detected as a cell
ROI_SCALING = 2 #rescaling factor applied to the ROIs for displaying them larger
path = 'C:\\Users\Mattia Cattaneo\Desktop\Polimi\Magistrale\Tesi\Python\Codes\\'
filename = 'selected_stack'


im = Image.open(path+filename+'.tif')
#im = Image.open('membrane_substack.tif')
h,w = np.shape(im)
tiffarray = np.zeros((im.n_frames,h,w))    #or limited number of images

shown_rois = 0
number_of_roi = 0    #only to giva the correct name to the saved tif


stacks=[]
old_len=[]


try: #the try block lets you test a block of code for errors
    
    for i in range(im.n_frames-1):        
        im.seek(i)
        im_in = np.array(im)
        elaborated_im = im_in
        elaborated_im = (elaborated_im/256).astype('uint8') 
        t0 = time.time()
        cx, cy, cnts = find_cell(elaborated_im, MIN_CELL_SIZE)
        #print('x positions of the centroids', cx)
        #print('elapsed time: ', time.time()-t0)      
        
        #im_out = im_in
        
        # put im_in if you want to try with 16bit version (it seems not work!), elaborated_im for 8bit
        im_out = create_contours(cx, cy, elaborated_im, cnts, RECT_SIZE)
        rois = roi_creation(im_in, cx, cy, RECT_SIZE)
        
        
        
        for index, val in enumerate(cx):
            for index2, val2 in enumerate(stacks):
                # comparison between cell centre
                if cx[index] in range(stacks[index2][0]-RANGE,stacks[index2][0]+RANGE) and cy[index] in range(stacks[index2][1]-RANGE,stacks[index2][1]+RANGE):
                    stacks[index2].append(rois[index])
                    del rois[index]; del cx[index]; del cy[index]
                    index-=1
                    if cx==[]:
                        break
                    
        i=len(stacks)
        
        for index, val in enumerate(rois):    
            stacks.append([cx[index]])     #here we need square brakets (first element)
            stacks[i].append(cy[index])    #no square brakets otherwise considered as a list
            stacks[i].append(rois[index])
            i+1
        
        min_len=min(len(stacks),len(old_len))
        
        for index in range(min_len-1):    #ho messo -1 ma non so perchè
            if len(stacks[index]) == old_len[index]:    
                newstack=save_stack(stacks[index])
                imageio.mimwrite('roi' + str(number_of_roi) + '.tif', newstack)
                number_of_roi+=1
                del stacks[index]; del old_len[index]
                index-=1
            else:
                old_len[index]=len(stacks[index])
        
        # print(index)    #only to control the code...
        
        if len(stacks)>len(old_len):
            for index in range (len(stacks)-len(old_len)):
                position=len(old_len)
                old_len.append([len(stacks[position])])    #old_len can be thought as a simple numpy array...
        else:
            for index in range(len(old_len)-len(stacks)):
                position=len(stacks)
                del old_len[position]
        
        
        
        
        
        
        print('elapsed time: ', time.time()-t0) 
        
        cv2.imshow('Acquired data', im_out )
        
        tiffarray[i,:,:] = im_in    # to save the original acquired images
        
        #This would save the annotated images in the subfolder \Annotated, that must be created
        #cv2.imwrite(path+'Annotated'+'\\'+filename+'\\out\\out'+ str(i)+'.tif', im_out)
            
        
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
              
        
        cv2.waitKey(100) # waits the specified ms. Value 0 would stop until key is hitten
        
    
finally: #the finally block lets you execute code, regardless of the result of the try and except blocks.
    
    cv2.destroyAllWindows()

    # tiffarray=tiffarray.astype('uint8')
        
    # im=Image.fromarray(tiffarray)
    # im.save('prova8bit.tif')
    
    # imageio.mimwrite('prova8bit.tif', tiffarray)