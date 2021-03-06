import numpy as np
import matplotlib.pyplot as plt
import tkinter
from tkinter.filedialog import askopenfilename
from astropy.io import fits
import bin_accretion,functions
from astropy import wcs
from radial_profile import getcenter
def trim(lis,targ):
    other=[]
    for i in range(len(lis)):
        if lis[i]<=targ:
            other.append(lis[i])
    return other

def trim2(lis,lis2):
    other=[]
    for i in range(len(lis)):
        if lis2[i]>1:
            other.append(lis[i])
    return other

'''
# make sig noise -> ston
root=tkinter.Tk()
root.withdraw()
signalname= askopenfilename(message="Select unbinned ston")
root.update()
root.destroy()
'''

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

wcsx,signal,var,sourcedir,objname=bin_accretion.initialize(enternew=True)
ston=signal/np.sqrt(var)


fig,ax=plt.subplots()
xun=[]
yun=[]
'''
with fits.open(signalname) as hdul:
    ston=np.flipud(hdul[0].data)
    wcsx=wcs.WCS(hdul[0].header)
'''

center=getcenter(np.ma.masked_where(np.isnan(ston),ston)) #as usual is (y,x)


for y in range(len(ston)):
    for x in range(len(ston[0])):
        if not np.isnan(ston[y][x]):
            xun.append(np.sqrt((y-center[0])**2+(x-center[1])**2))
            yun.append(ston[y][x])
ax.plot(xun,yun,linewidth=0,marker=".",label="unbinned")
ax.set_xlabel("Radius from center")
ax.set_ylabel("Signal-to-noise from center")

target=[3,5,10]
xes=[]
yes=[]
aes=[]

'''
source="/".join(signalname.split("/")[:-2])
objname=signalname.split("/")[-1]
stonfits=".".join(objname.split(".")[:-1])+"_wit.fits"
'''
source="/".join(sourcedir.split("/")[:-1])
stonfits="zston_"+"_".join(objname.split("_")[:-1])+".fits"
assfits="z_"+"_".join(objname.split("_")[:-1])+"_assigned.fits"

ybin=[]


for t in range(len(target)):
    xes.append([])
    yes.append([])
    aes.append([])
    ybin.append([])
    signalname=source+"/target"+str(target[t])+"/"+stonfits
    print(signalname)
    with fits.open(signalname) as hdul:
        ston=np.flipud(hdul[0].data)
        wcsx=hdul[0].header
    signalname=source+"/target"+str(target[t])+"/"+assfits
    print(signalname)
    with fits.open(signalname) as hdul:
        ass=np.flipud(hdul[0].data.astype(int))
        wcsx=hdul[0].header

    bins=int(np.nanmax(ass)-np.nanmin(ass))
    bcenters=[[0,0] for i in range(bins)]

    binlist=[0 for i in range(bins)]
    for y in range(len(ass)):
        for x in range(len(ass[y])):
            try:
                binlist[ass[y][x]-1]+=1
                bcenters[ass[y][x]-1][0]+=y
                bcenters[ass[y][x]-1][1]+=x
            except:
                print(ass[y][x]-1)
                print(np.nanmax(ass))
                print(np.nanmin(ass))
        #print(str(y/len(ass))+" through stage 1")
    for l in range(len(binlist)):
        if binlist[l]>0:
            bcenters[l][0]/=binlist[l]
            bcenters[l][1]/=binlist[l]

    center=getcenter(ston) #as usual is (y,x)

    for point in range(len(bcenters)):
        x=int(bcenters[point][1])
        y=int(bcenters[point][0])
        if not np.isnan(ston[y][x]):
                aes[t].append(binlist[point])
                xes[t].append(np.sqrt((y-center[0])**2+(x-center[1])**2))
                yes[t].append(ston[y][x])
    ax.plot(xes[t],yes[t],linewidth=0,marker=".",label="target"+str(target[t]))
    for y in range(len(ston)):
        for x in range(len(ston[0])):
            if not np.isnan(ston[y][x]):
                ybin[t].append(ston[y][x])

plt.legend()

continuous=False
minhis=[]

if continuous:
    fig,ax=plt.subplots()
    x=np.array(range(len(ybin[0])))
    y=np.sort(ybin[0])
    ax.plot(x,y,color="blue",label="target")

    fig,ax=plt.subplots(1,len(target))
    for t in range(len(target)):
        x=np.array(range(len(ybin[t])))
        y=np.sort(ybin[t])
        dy=functions.smoother(y,3)
        dyx=functions.numdif(x,dy)
        dyx=[i*200 for i in dyx]
        ax[t].plot(x,y,color="blue",label="target")
        ax[t].plot(x,dyx,color="red",label="derivative")
        start=int(len(dyx)/10)
        end=int(9*len(dyx)/10)
        for zz in range(len(y)):
            if y[zz]>target[t]:
                end=zz
                break
        ax[t].plot([x[end],x[end]],[0,100],linestyle="dashed",color="green")
        ax[t].plot([x[start],x[start]],[0,100],linestyle="dashed",color="green")
        ax[t].plot(x[start:end],dyx[start:end],color="green")
        maxint=np.argmax(dyx[start:end])+start
        minhis.append(y[maxint])
        print("target: "+str(target[t])+" minhis: "+str(y[maxint]))
        ax[t].plot([x[maxint],x[maxint]],[0,100],linestyle="dashed",color="black")
        #ax[t].plot(functions.numdif(y,x),y,color="green")
        ax[t].set_xlabel(str(target[t]))
        plt.legend()
    #plt.show()

fig,ax=plt.subplots(len(target)+1,1)

binsz=200

ax[0].hist(trim(yun,100),binsz,label="unbinned")

negacc=0

for t in (range(len(target))):
    nn,bins,patches=ax[t+1].hist(trim(ybin[t],100),binsz,alpha=0.5)
    if not continuous:
        minb=np.argmax(nn)
        for c in range(len(nn)):
            if bins[c]>=target[t]:
                break
            elif bins[c+1]<=0:
                negacc+=nn[c]
            else:
                if negacc>0:
                    negacc*=0.95
                    negacc-=nn[c]
                elif nn[c]<nn[minb]:
                    minb=c
        if bins[minb+2]>=target[t] and nn[minb+2]<=nn[minb]:
            while bins[minb]>0 and nn[minb-1]>nn[minb]:
                minb-=1
        ## this is a minimum
        minhis.append(0.5*(bins[minb]+bins[minb+1]))

    ax[t+1].plot([target[t],target[t]],[0,2000],linestyle="dashed",color="green",label="target")
    ax[t+1].plot([minhis[t],minhis[t]],[0,2000],linestyle="dashed",color="black",label="cutoff")
    plt.legend()
plt.show()

