import bin_accretion,main,functions
import numpy as np



if __name__ == "__main__":
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
            target=targlist[m]
            sourcedir=sourcelist[i]
            subfolder=main.makesubfolder(sourcedir,target)
            #main.saveston(wscxlist[i],siglist[i],varlist[i],sourcelist[i],objlist[i],subfolder="unbinned")

            ## this is us applying the data mask. We block out negative values and then run the binning algorithm on it
            signal2=np.copy(signal)
            var2=np.copy(var)
            #var2[signal2<=0]=1e10
            signal2[signal2<=0]=0
            eps=0.1

            binlist,diflist=main.mainfunc(signal2,var2,target,displayWVT=False,epsilon=eps)
            
            #main.saveblockoutfits(targlist[m],binlist,wscxlist[i],siglist[i],varlist[i],objlist[i],sourcelist[i],subfolder=subfolder)
            #wvt,ston=functions.generate_wvt2(binlist,siglist[i],varlist[i])
            ## then we apply the bins to the actual data and save all our files.
            wvt,ston=functions.generate_wvt3(binlist,signal,var,np.full(len(binlist),1))
            vwvt=functions.generate_wvt(binlist,var)
            #main.saveiteratedfits(target,wcsx,wvt,vwvt,objname,sourcedir,subfolder=subfolder)
            #functions.convergence(eps,diflist,sourcedir,objname,subfolder=subfolder)
            main.saveblockoutfits(target,ston,wcsx,wvt,vwvt,objname,sourcedir,subfolder=subfolder)
            #main.saveblockoutoldfits(target,ston,wcsx,wvt,vwvt,objname,sourcedir,subfolder=subfolder)
            main.saveston(wcsx,ston,sourcedir,objname,subfolder=subfolder)
            assign=functions.assign(binlist,target,ston)
            main.saveassign(wcsx,assign,sourcedir,objname,subfolder=subfolder)
    print("Bye bye")