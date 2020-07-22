import numpy as np
import matplotlib.pyplot as plt 
import tkinter
from tkinter.filedialog import askopenfilename
from astropy.io import fits
import functions,bin_accretion
import scipy.spatial as sp
import time


def initialize(enternew=False):
    

    ##First let's select a signal file
    if enternew:
        ## this is to obtain a file
        tkinter.Tk().withdraw()
        geocenters = askopenfilename()
    else:
        geocenters="/Users/pierre/Downloads/gcenters_of_the_image.npy"

    ## to get the directory of the file so that we can save new files there

    ##filename is a string locating the selected file
    geocarray=np.load(geocenters)
    return geocarray
def next_iteration(target,signal,var,geocarray,scalearray,wvt,displaywvt=False):
    ## generate all of the pixels to be slotted into a bin determined by the generators
    binlist=[ [] for _ in range(len(geocarray)) ]
    for y in range(len(signal)):
        print("line"+str(y))        
        for x in range(len(signal[y])):
            pixel=(y,x)
            
            ## assign pixel to the generator with the minimum scaled length
            binlist[functions.scaled_closest(pixel,geocarray,scalearray)].append(pixel)
    print("image scanned")
    wvt,geocarray2,scalearray2=functions.calculate_scales(target,binlist,signal,var,wvt,displaywvt)
    for r in range(len(binlist)):
        if binlist[r]==[]:
            geocarray2[r]=geocarray[r]
            scalearray2[r]=scalearray[r]
    return wvt,geocarray2,scalearray2

def next_iteration2(target,signal,var,geocarray,scalearray,wvt,displaywvt=False):
    ## generate all of the pixels to be slotted into a bin determined by the generators
    #allpix=[(y,x) for y in range(signal.shape[0]) for x in range(signal.shape[1]) ]
    
    #assign=[-1 for _ in range(len(allpix))]
    assign=np.full_like(signal,-1)
    viable=[]
    for g in range(len(geocarray)):
        point=(int(geocarray[g][0]),int(geocarray[g][1]))
        try:
            assign[point[0]][point[1]]=g
        except:
            print(point)
            print(geocarray[g])
            print(g)
            raise NameError("ouchi")
        viable.append([])
        append_validate((point[0]+1,point[1]),viable[g],assign)
        append_validate((point[0]-1,point[1]),viable[g],assign)
        append_validate((point[0],point[1]+1),viable[g],assign)
        append_validate((point[0],point[1]-1),viable[g],assign)
        #print(str(int(g*100/len(geocarray)))+" percent done with init pass")
    while checkneg(assign) or viabempty(viable):
        for g in range(len(geocarray)):
            prune=True
            while prune and len(viable[g])>0:
                point=viable[g].pop(0)
                if assign[point[0]][point[1]]==g:
                    prune=True
                else:
                    prune=False
            if len(viable[g])>0:
                if assign[point[0]][point[1]]==-1:
                    assign[point[0]][point[1]]=g
                    append_validate((point[0]+1,point[1]),viable[g],assign)
                    append_validate((point[0]-1,point[1]),viable[g],assign)
                    append_validate((point[0],point[1]+1),viable[g],assign)
                    append_validate((point[0],point[1]-1),viable[g],assign)
                else:
                    if ((geocarray[g][0]-point[0])**2+(geocarray[g][1]-point[1])**2)/(scalearray[g]**2)<((geocarray[assign[point[0]][point[1]]][0]-point[0])**2+(geocarray[assign[point[0]][point[1]]][1]-point[1])**2)/(scalearray[assign[point[0]][point[1]]]**2):
                        assign[point[0]][point[1]]=g
                        append_validate((point[0]+1,point[1]),viable[g],assign)
                        append_validate((point[0]-1,point[1]),viable[g],assign)
                        append_validate((point[0],point[1]+1),viable[g],assign)
                        append_validate((point[0],point[1]-1),viable[g],assign)
    binlist=[ [] for _ in range(len(geocarray)) ]
    for j in range(len(assign)):
        for i in range(len(assign[0])):
            binlist[assign[j][i]].append((j,i))
    wvt,geocarray2,scalearray2=functions.calculate_scales(target,binlist,signal,var,wvt,displaywvt)
    for r in range(len(binlist)):
        if len(binlist[r])==0:
            print("empty index"+str(r))
            geocarray2[r]=geocarray[r]
            scalearray2[r]=scalearray[r]
    return wvt,geocarray2,scalearray2

def checkneg(assign):
    '''try:
        assign.index(-1)
        print(min(assign))
        return True
    except ValueError:
        print("failed :(")
        return False'''
    num=np.count_nonzero(assign==-1)
    print(num)
    if num>0:
        return True
    else:
        return False

def viabempty(viable):
    for binn in viable:
        if len(binn)>0:
            return True
        else: 
            return False

def append_validate(candidate,target,check):
    try:
        check[candidate[0]][candidate[1]]
        if candidate[0]<0 or candidate[0]>=len(check) or candidate[1]<0 or candidate[1]>=len(check[0]):
            raise NameError("brrr overflow bro")
        target.append(candidate)
    except:
        pass

def iteration_func(target,signal,var,geocarray,scalearray,epsilon,displaywvt=False):
    wvt=np.zeros_like(signal)
    target=5
    start=time.time()
    ## have to manually kill terminal is does not converge
    difference=2*epsilon

    

    while difference>epsilon:
        print("another iteration")
        wvt2=np.copy(wvt)
        wvt,geocarray,scalearray=next_iteration2(target,signal,var,geocarray,scalearray,wvt,displaywvt)
        
        difference=np.sqrt(np.sum((wvt-wvt2)**2))
        print("dif",difference)

    print("elapsed time "+str(time.time()-start))
    return wvt
    
def iteration_func0(target,signal,var,geocarray,scalearray,epsilon,displaywvt=False):
    wvt=np.zeros_like(signal)
    target=5
    start=time.time()
    ## have to manually kill terminal is does not converge
    epsilon=10
    difference=2*epsilon

    

    while difference>epsilon:
        print("another iteration")
        wvt2=np.copy(wvt)
        wvt,geocarray,scalearray=next_iteration(target,signal,var,geocarray,scalearray,wvt,displaywvt)
        
        difference=np.sqrt(np.sum((wvt-wvt2)**2))
        print("dif",difference)

    print("elapsed time "+str(time.time()-start))
    return wvt

if __name__ == "__main__":
    sourcedir,signal,var=bin_accretion.initialize(enternew=True)
    geocarray=initialize(enternew=True)
    scalearray=np.full(len(geocarray),1)
    target=5
    epsilon=100
    wvt=iteration_func(target,signal,var,geocarray,scalearray,epsilon,displaywvt=True)

    fig,ax=plt.subplots()
    image=ax.imshow(wvt,cmap="cubehelix")
    fig.colorbar(image)
    plt.show()
    np.save(sourcedir+"/iterated_gcenters2",geocarray)
    hdu = fits.PrimaryHDU(wvt)
    hdul = fits.HDUList([hdu])
    hdul.writeto(sourcedir+"/iterated_wvt2.fits",overwrite=True)