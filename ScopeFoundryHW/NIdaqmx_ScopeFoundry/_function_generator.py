# -*- coding: utf-8 -*-
"""
Created on Sat Mar 13 23:29:33 2021

@author: andrea
"""

import numpy as np
from matplotlib import pyplot as plt


freq = 100 # Hz 
rate = freq * 10

Ncycles = 6

Nsamples = Ncycles * (rate//freq)  
dt = 1/rate
print('dt:',dt)
T = 1/ freq 

epsilon = 1e-9 # 1ns to avoid approximation error in rect and step function
t = np.arange(0, Ncycles*T, dt) + epsilon

# sinusoid repeated Ncyles  
y_sin = np.sin(2*np.pi*freq*t)

plt.figure() 
plt.plot(t, y_sin)

# each cycle is a step of duration 1/freq
# Ncycles should be multiple of Nsteps
Nsteps = 3 # number of steps
deltaAmp = 3.5 # V
y_step =  deltaAmp * (t // T % Nsteps)

spikeAmp = 0.002 # V
spikeT = 0.0005 #s
spikeT = 0.05/freq # percentage of the step duration
y_spikes = spikeAmp * (t % T < spikeT)

plt.figure() 
plt.plot(t, y_spikes+y_step)

width = 0.5
deltaAmp = 3.5 # V
#y_rect =  deltaAmp * ( ( t // (width*T))  )

y_rect = deltaAmp * ((t) % T < (width*T))

print('y',len(y_rect))
print('y>0:', sum(y_rect>0))
print('y==0:', sum(y_rect==0))

plt.figure() 
plt.plot(y_rect)
plt.grid()

# array=np.linspace(start=0, stop=2*np.pi*Ncycles, num=Nsamples, endpoint=False) 
# samples=np.sin(array)
# plt.figure() 
# plt.plot(array, samples) 