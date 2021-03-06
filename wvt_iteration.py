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

def next_iteration2(target,signal,var,geocarray,scalearray,weighting=True):
    ## generate all of the pixels to be slotted into a bin determined by the generators
    #allpix=[(y,x) for y in range(signal.shape[0]) for x in range(signal.shape[1]) ]
    
    #assign=[-1 for _ in range(len(allpix))]
    assign=np.full_like(signal,-1,dtype=int)
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
    while checkneg(assign) or viabunempty(viable):
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
                    else:
                        pass
    binlist=[ [] for _ in range(len(geocarray)) ]
    for j in range(len(assign)):
        for i in range(len(assign[0])):
            binlist[assign[j][i]].append((j,i))
    '''
    cancelled=0
    
    for r in range(len(binlist)):
        if len(binlist[r])==0:
            print("empty index"+str(r))
            cancelled+=1
    if cancelled>0:
        binl=[]
        for r in range(len(binlist)):
            if len(binlist[r])==0:
                pass
            else:
                binl.append(binlist[r])
        geocarray,scalearray=functions.calculate_scales(target,binl,signal,var)
        return binl,geocarray,scalearray
    else:
        geocarray,scalearray=functions.calculate_scales(target,binlist,signal,var)
        return binlist,geocarray,scalearray
    '''
    binlist,geocarray,scalearray=functions.calculate_scales(target,binlist,signal,var)
    return binlist,geocarray,scalearray

    

def checkneg(assign):
    num=np.count_nonzero(assign==-1)
    #print(num)
    if num>0:
        return True
    else:
        return False

def viabunempty(viable):
    for binn in viable:
        if len(binn)>0:
            return True
    return False

def append_validate(candidate,target,check):
    try:
        check[candidate[0]][candidate[1]]
        if candidate[0]<0 or candidate[0]>=len(check) or candidate[1]<0 or candidate[1]>=len(check[0]):
            raise NameError("brrr overflow bro")
        target.append(candidate)
    except:
        pass

def iteration_func(target,signal,var,geocarray,scalearray,epsilon,weighting=True,displaywvt=False):
    wvt=np.zeros_like(signal)
    
    start=time.time()
    ## have to manually kill terminal is does not converge
    difference=2*epsilon
    diflist=[]
    repeat=True
    numit=0

    while repeat:
        print("another iteration")
        wvt2=np.copy(wvt)
        binlist,geocarray,scalearray=next_iteration2(target,signal,var,geocarray,scalearray)
        wvt,ston=functions.generate_wvt3(binlist,signal,var,scalearray,displayWVT=displaywvt)
        difference=np.sqrt(np.sum((wvt-wvt2)**2)/np.sum(var))
        print("dif",difference)

        if epsilon<0:
            numit+=1
            if numit+epsilon>=0:
                repeat=False
        else:
            diflist.append(difference)
            repeat=difference>epsilon

    print("elapsed time "+str(time.time()-start))
    return binlist,diflist

def iteration_funcc(target,signal,var,binlist,epsilon,weighting=True,displaywvt=False):
    wvt=np.zeros_like(signal)
    
    start=time.time()
    ## have to manually kill terminal is does not converge
    difference=2*epsilon

    repeat=True
    numit=0

    density=signal**2/var

    while repeat:
        print("another iteration")
        wvt2=np.copy(wvt)
        
        carray=[]
        for binnn in binlist:
            x=0
            y=0
            su=0
            for point in binnn:
                y+=point[0]*density[point[0]][point[1]]
                x+=point[1]*density[point[0]][point[1]]
                su+=density[point[0]][point[1]]
            carray.append((y/su,x/su))
        
        scalearray=[1]*len(binlist)
        wvt,ston=functions.generate_wvt3(binlist,signal,var,scalearray,displayWVT=displaywvt)
        difference=np.sqrt(np.sum((wvt-wvt2)**2)/np.sum(var))
        print("dif",difference)

        if epsilon<0:
            numit+=1
            if numit+epsilon>=0:
                repeat=False
        else:
            repeat=difference>epsilon

    print("elapsed time "+str(time.time()-start))
    return binlist


if __name__ == "__main__":
    '''
    wcsx,signal,var,sourcedir,objname=bin_accretion.initialize(enternew=True)
    geocarray=initialize(enternew=True)
    scalearray=np.full(len(geocarray),1)
    target=5
    '''
    wcsx,signal,var,sourcedir,objname=bin_accretion.initialize(enternew=True)
    target=400
    binlist,geocarray,scalearray=bin_accretion.cc_accretion(signal,var,target)
    density=signal**2/var
    carray=[]
    for binnn in binlist:
        x=0
        y=0
        su=0
        for point in binnn:
            y+=point[0]*density[point[0]][point[1]]
            x+=point[1]*density[point[0]][point[1]]
            su+=density[point[0]][point[1]]
        carray.append((y/su,x/su))
    scalearray=[1]*len(binlist)
    epsilon=100
    binlist=iteration_funcc(target,signal,var,binlist,-10,displaywvt=False)
    wvt,ston=functions.generate_wvt4(binlist,signal,var,[1]*len(binlist),displayWVT=True)
    wvt,ston=functions.generate_wvt3(binlist,signal,var,[1]*len(binlist),displayWVT=True)
    """
    fig,ax=plt.subplots()
    image=ax.imshow(wvt,cmap="cubehelix")
    fig.colorbar(image)
    plt.show()
    np.save(sourcedir+"/iterated_gcenters2",geocarray)
    header=wcsx.to_header()
    hdu = fits.PrimaryHDU(wvt,header=header)
    hdul = fits.HDUList([hdu])
    hdul.writeto(sourcedir+"/iterated_wvt2.fits",overwrite=True)
    """