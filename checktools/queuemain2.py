import bin_accretion,main,functions,wvt_iteration
import numpy as np
import matplotlib.pyplot as plt
import time,os
import scipy.spatial as sp

##this is very similar to queuemain.py though we have to include a bunch of modified function
## to support expansion method. but like mainfunc looks the same, but we have to include it because we needed to change bin accretion because we needed to change calculate_scales

SMALL_SIZE=14
MEDIUM_SIZE=16
BIGGER_SIZE=20

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title


def calculate_scales(target,binlist,signal,var,scalarray,edgelist):
    unlisted=[]
    geomcentres=[]
    scalelengths=[]
    binlist2=[]
    n2=[]
    for bindex in range(len(binlist)):
        if len(binlist[bindex])==0:
            pass
        else:
            

            StoN=functions.calculate_SN(binlist[bindex],signal,var)
            geoc=functions.geometric_center(binlist[bindex])
            

            ## Define q to be some constant. Acc to Diehl&Statler, should not have effect
            q=np.pi ## for circular bins, which is generally what we are trying to achieve
            delta=np.sqrt(len(binlist[bindex])*target/(q*StoN))
            if np.isinf(delta):
                delta=np.nan

            ## this is to check to see if we should crush individual pixels that sit entirely within other bins. BAD! We hate that
            if len(binlist[bindex])==1:
                ## check if swallowed pixel
                swallowed=False
                pix,piy=binlist[bindex][0]
                ##find first pixel to right
                if pix+1>=len(signal[0]) or piy+1>=len(signal) or piy-1<0 or pix-1<0:
                    pass
                else:
                    for binn in binlist:
                        if ((pix+1,piy) in binn) and ((pix,piy+1) in binn) and ((pix-1,piy) in binn) and ((pix,piy-1) in binn):
                            swallowed=True
                            break

                if StoN<target and swallowed and(np.isnan(delta) or delta==scalarray[bindex]):
                    unlisted.append(binlist[bindex][0])
                else:
                    scalelengths.append(delta)
                    geomcentres.append(geoc)
                    binlist2.append(binlist[bindex])
                    n2.append(bindex)
            else:
                if np.isnan(delta) or delta<0:
                    if edgelist[bindex]:
                            scalelengths.append(scalarray[bindex])
                    else:
                        ## if a bin cannot meet minimum StoN and is in the middle of the image, we want to grow it
                        scalelengths.append(1.1*scalarray[bindex])
                else:
                    scalelengths.append(delta)
                geomcentres.append(geoc)
                binlist2.append(binlist[bindex])
                n2.append(bindex)
            

    geocarray=np.array(geomcentres)
    scalearray=np.array(scalelengths)
    
    for point in unlisted:
        i=functions.closest_index(point,geocarray,np.full((len(signal),len(signal[0])),1))
        binlist2[i].append(point)
    
    
    return binlist2,geocarray,scalearray

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
        wvt_iteration.append_validate((point[0]+1,point[1]),viable[g],assign)
        wvt_iteration.append_validate((point[0]-1,point[1]),viable[g],assign)
        wvt_iteration.append_validate((point[0],point[1]+1),viable[g],assign)
        wvt_iteration.append_validate((point[0],point[1]-1),viable[g],assign)
        #print(str(int(g*100/len(geocarray)))+" percent done with init pass")
    while wvt_iteration.checkneg(assign) or wvt_iteration.viabunempty(viable):
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
                    wvt_iteration.append_validate((point[0]+1,point[1]),viable[g],assign)
                    wvt_iteration.append_validate((point[0]-1,point[1]),viable[g],assign)
                    wvt_iteration.append_validate((point[0],point[1]+1),viable[g],assign)
                    wvt_iteration.append_validate((point[0],point[1]-1),viable[g],assign)
                else:
                    if ((geocarray[g][0]-point[0])**2+(geocarray[g][1]-point[1])**2)/(scalearray[g]**2)<((geocarray[assign[point[0]][point[1]]][0]-point[0])**2+(geocarray[assign[point[0]][point[1]]][1]-point[1])**2)/(scalearray[assign[point[0]][point[1]]]**2):
                        assign[point[0]][point[1]]=g
                        wvt_iteration.append_validate((point[0]+1,point[1]),viable[g],assign)
                        wvt_iteration.append_validate((point[0]-1,point[1]),viable[g],assign)
                        wvt_iteration.append_validate((point[0],point[1]+1),viable[g],assign)
                        wvt_iteration.append_validate((point[0],point[1]-1),viable[g],assign)
                    else:
                        pass
    binlist=[ [] for _ in range(len(geocarray)) ]
    edgelist=[False]*len(geocarray)
    for j in range(len(assign)):
        for i in range(len(assign[0])):
            binlist[assign[j][i]].append((j,i))
            if i==0 or j==0 or i==len(assign[0])-1 or j==len(assign)-1:
                edgelist[assign[j][i]]=True
    
    binlist,geocarray,scalearray=calculate_scales(target,binlist,signal,var,scalearray,edgelist)
    return binlist,geocarray,scalearray

def shermanantitrust(target,signal,var,ston,binlist,geocarray,scalearray):
    trust=[]
    ## are there any bins big enough to warrant cutting them in half?
    for b in range(len(binlist)):
        point=binlist[b][0]
        if len(binlist[b])>1 and ston[point[0]][point[1]]>2*target:
            trust.append(b)
    ## with list of bustable bins, in each we want to 
    ## 1. find the point most distant from the geocenter
    ## 2. find the point most distant from that point
    ## cut the bin in half by assigning all the the points to either distant point based on closeness
    bin2s=[]
    geo2s=[]
    sca2s=[]
    for b in trust:
        ind=sp.distance.cdist([geocarray[b]],binlist[b]).argmax()
        point1=binlist[b][ind]
        ind=sp.distance.cdist([point1],binlist[b]).argmax()
        point2=binlist[b][ind]
        dist=sp.distance.cdist([point1,point2],binlist[b])
        bin1=[]
        bin2=[]
        for p in range(len(binlist[b])):
            if dist[0][p]<=dist[1][p]:
                bin1.append(binlist[b][p])
            else:
                bin2.append(binlist[b][p])
        ## both bins must be big enough to stand alone
        StoN1=functions.calculate_SN(bin1,signal,var)
        if StoN1>=target:
            StoN2=functions.calculate_SN(bin2,signal,var)
            if StoN2>=target:
                geoc1=functions.geometric_center(bin1)
                geoc2=functions.geometric_center(bin2)
                bin2s.append(bin2)
                geo2s.append(geoc2)
                sca2s.append(scalearray[b])
                geocarray[b]=geoc1
                binlist[b]=bin1
    ## if any of the split bins were viable, extend the binlist
    
    if len(bin2s)>0:
        bl=[]
        gc=[]
        sl=[]
        for i in range(len(binlist)):
            bl.append(binlist[i])
            gc.append(geocarray[i])
            sl.append(scalearray[i])
        for b in range(len(bin2s)):
            bl.append(bin2s[b])
            gc.append(geo2s[b])
            sl.append(sca2s[b])
        binlist=np.array(bl)
        geocarray=np.array(gc)
        scalearray=np.array(sl)





def iteration_func(target,signal,var,geocarray,scalearray,epsilon,weighting=True,displaywvt=False):
    wvt=np.zeros_like(signal)
    
    start=time.time()
    ## have to manually kill terminal is does not converge
    difference=2*epsilon

    repeat=True
    numit=0

    differences=[]

    while repeat:
        print("another iteration")
        wvt2=np.copy(wvt)
        binlist,geocarray,scalearray=next_iteration2(target,signal,var,geocarray,scalearray)
        wvt,ston=functions.generate_wvt3(binlist,signal,var,scalearray,displayWVT=displaywvt)
        difference=np.sqrt(np.sum((wvt-wvt2)**2)/np.sum(var))
        print("dif",difference)
        
        '''
        if difference<2*epsilon and difference>epsilon:
            shermanantitrust(target,signal,var,ston,binlist,geocarray,scalearray)
        '''
        if epsilon<0:
            numit+=1
            if numit+epsilon>=0:
                repeat=False
        else:
            differences.append(difference)
            repeat=difference>epsilon

    print("elapsed time "+str(time.time()-start))

    return binlist,differences

def cc_accretion(signal,var,target):

    ## this is the signal-to-noise for each pixel
    ston=signal/np.sqrt(np.abs(var))
    ston=np.where(np.equal(signal,np.zeros_like(signal)),signal,ston)
    assign=np.full_like(ston,-1)
            
    #density=ston*np.abs(ston)
    density=ston*ston
    cellsleft=np.count_nonzero(assign == -1)
    print(cellsleft)

    supercentroid=np.unravel_index(ston.argmax(),ston.shape)
    supermass=density[supercentroid[0]][supercentroid[1]]
    
    viable=[]
    bin_accretion.validateappend(viable,(supercentroid[0],supercentroid[1]),assign)
    binlist=[]
    bcentroids=[]
    rcentroids=[]
    rebinlist=[]
    
    ## in case this borks np.count_nonzero(array == value) to return -1 in assign
    while len(viable)>0:
        centroid=functions.closest_point(supercentroid,viable,density)
        current=[]
        current.append(centroid)
        viable.remove(centroid)
        assign[centroid[0]][centroid[1]]=0
        viablecell=[]
        bin_accretion.validateappend(viablecell,(centroid[0]+1,centroid[1]),assign)
        bin_accretion.validateappend(viablecell,(centroid[0]-1,centroid[1]),assign)
        bin_accretion.validateappend(viablecell,(centroid[0],centroid[1]+1),assign)
        bin_accretion.validateappend(viablecell,(centroid[0],centroid[1]-1),assign)
        binmass=density[centroid[0]][centroid[1]]
        accrete=binmass<target**2 and len(viablecell)>0
        while accrete:
            nextpoint=functions.closest_point(centroid,viablecell,density)

            Rmax=0.3
            newbin=current+[nextpoint]
            nmass=binmass+density[nextpoint[0]][nextpoint[1]]
            ## replacing weighted centroids with geometric centers as suggested by Diehl 
            ## in Cappellari's implementation to address negative data
            ncentroid=functions.geometric_center(newbin)
            rmax=sp.distance.cdist([ncentroid],newbin).max()
            R=rmax*np.sqrt(np.pi/len(newbin))-1
            #if R<=Rmax and np.abs(binmass-target**2)>np.abs(nmass-target**2): here we are saying that the new mass brings the bin closer to the target
            if R<=Rmax and not np.isnan(nmass) and np.abs(binmass-target**2)>=np.abs(nmass-target**2):
                current.append(nextpoint)
                viablecell.remove(nextpoint)
                if viable.count(nextpoint)>0:
                    viable.remove(nextpoint)
                assign[nextpoint[0]][nextpoint[1]]=0
                binmass=nmass
                centroid=ncentroid
                bin_accretion.validateappend(viablecell,(nextpoint[0]+1,nextpoint[1]),assign)
                bin_accretion.validateappend(viablecell,(nextpoint[0]-1,nextpoint[1]),assign)
                bin_accretion.validateappend(viablecell,(nextpoint[0],nextpoint[1]+1),assign)
                bin_accretion.validateappend(viablecell,(nextpoint[0],nextpoint[1]-1),assign)
                accrete= len(viablecell)>0
            else: 
                accrete=False
                
        success=0.8
        if binmass/(target**2)<success or np.isnan(binmass):
            rebinlist.append(current)
            rcentroids.append(centroid)
        else:
            binlist.append(current)
            bcentroids.append(centroid)
            
        supercentroid=((supercentroid[0]*supermass+centroid[0]*binmass)/(supermass+binmass),(supercentroid[1]*supermass+centroid[1]*binmass)/(supermass+binmass))
        supermass=supermass+binmass
        viable.extend([v for v in viablecell if not v in viable])
        print(np.count_nonzero(assign == -1))

    print("Redistribution time")

    #wvt,ston=functions.generate_wvt3(binlist+rebinlist,signal,var,np.full(len(binlist)+len(rebinlist),1),True)

    ## Then we assign each unsuccessfully binned pixel to a successfully bin
    functions.redistribute(binlist,rebinlist,bcentroids,density)
    ## At this point, binlist should contain all of the original points
    ## Now I want to iterate through binlist to get the list of generators. This is really what this was for
    ## Though now is as good of a time as any to create the CVT
    binlist,geocarray,scalearray=calculate_scales(target,binlist,signal,var,[1]*len(binlist),[False]*len(binlist))
    
    #wvt,ston=functions.generate_wvt3(binlist,signal,var,scalearray,True)
    
    return binlist,geocarray,scalearray

def mainfunc(signal,var,target,weighting=True,displayWVT=True,epsilon=10):
    binlist,init_generators,init_scalelengths=cc_accretion(signal,var,target)
    binlist,diflist=iteration_func(target,signal,var,init_generators,init_scalelengths,epsilon,displaywvt=displayWVT)
    wvt,ston=functions.generate_wvt2(binlist,signal,var,displayWVT)
    vwvt=functions.generate_wvt(binlist,var)
    if displayWVT:
        main.maketargetscatter(target,binlist,signal,var)
    #blockout(target,wvt,ston)
    return binlist,diflist

if __name__ == "__main__":
    ## this is just a very straightforward we set up all the files and pass them through the algorithm and save it
    targhold=0
    targlist=[]
    wcsxlist,siglist,varlist,sourcelist,objlist=bin_accretion.minitialize()
    contqueue=True
    while contqueue:
        try:
            target=main.gettarget(targhold)
            targlist.append(target)
        except:
            contqueue=False
    print("Files loaded!")
    for i in range(len(sourcelist)):
        for m in range(len(targlist)):
            
            wcsx=wcsxlist[i]
            signal=siglist[i]
            var=varlist[i]
            objname="_".join(objlist[i].split("_")[:-1])
            sourcedir="/".join(sourcelist[i].split("/")[:-1])
            target=targlist[m]

            subfolder="target"+str(target)
            #main.saveston(wscxlist[i],siglist[i],varlist[i],sourcelist[i],objlist[i],subfolder="unbinned")
            eps=0.1
            binlist,diflist=mainfunc(signal,var,target,displayWVT=False,epsilon=eps)
            
            #main.saveblockoutfits(targlist[m],binlist,wscxlist[i],siglist[i],varlist[i],objlist[i],sourcelist[i],subfolder=subfolder)
            #wvt,ston=functions.generate_wvt2(binlist,siglist[i],varlist[i])
            wvt,ston=functions.generate_wvt3(binlist,signal,var,np.full(len(binlist),1))
            vwvt=functions.generate_wvt(binlist,var)
            main.saveiteratedfits(target,wcsx,wvt,vwvt,objname,sourcedir,subfolder=subfolder)
            functions.convergence(eps,diflist,sourcedir,objname,subfolder=subfolder)
            main.saveblockoutfits(target,ston,wcsx,wvt,vwvt,objname,sourcedir,subfolder=subfolder)
            main.saveston(wcsx,ston,sourcedir,objname,subfolder=subfolder)
            assign=functions.assign(binlist,target,ston,signal)
            main.saveassign(wcsx,assign,sourcedir,objname,subfolder=subfolder)
    
    '''
    fig,ax=plt.subplots()
    for differences in range(len(superdif)):
        ax.plot(range(1,len(superdif[differences])),superdif[differences][1:],marker=".",label=difnames[differences])
    ax.set_xlabel("number of iterations")
    ax.set_ylabel("normalized difference")
    fig.legend()
    plt.show()
    '''

    print("Bye Bye!")