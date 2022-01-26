import cv2 as cv,numpy as np, copy, time
#from sklearn.cluster import KMeans
from matplotlib import pyplot as plt
import code_t as cd
############### 
blocksize =[8,8]
Q_m=np.float32(
    [[  [16,11,10,16,24,40,51,61],
        [12,12,14,19,26,58,60,55],
        [14,13,16,24,40,57,69,56],
        [14,17,22,29,51,87,80,62],
        [18,22,37,56,68,109,103,77],
        [24,35,55,64,81,104,113,92],
        [49,64,78,87,103,121,120,101],
        [72,92,95,98,112,100,103,99]],##Y
    [   [17,18,24,47,99,99,99,99],
        [18,21,26,66,99,99,99,99],
        [24,26,56,99,99,99,99,99],
        [47,66,99,99,99,99,99,99],
        [99,99,99,99,99,99,99,99],
        [99,99,99,99,99,99,99,99],
        [99,99,99,99,99,99,99,99],
        [99,99,99,99,99,99,99,99]]])##UV
frame_global=np.float32([])       
M=0
#intra frame
#inter frame
n_mv=(0,0)
n_d=10000
my,mx=0,0
set={'dc':[],'ac':[]}
###############
def find_mv(block,x,y,p=0):
    global frame_global,n_mv,n_d,my,mx
    br,bc,bch=np.int32(block.shape)
    r,c,clrc= np.int32(frame_global.shape)-np.int32(block.shape)
    #print(r,c) #64-120
    for i in range((y-1)*br,(y+1)*br):
        for j in range((x-1)*bc,(x+1)*bc):
            if(i >= 0 and j >= 0 and i < r and j<c):
                #print(frame_global[i:i+br,j:j+bc,:]-block)
                d = np.sum(np.abs(frame_global[i:i+br,j:j+bc,:]-block))
                if n_d > d:
                    n_d = d
                    mx=j
                    my=i
                    n_mv=(y*blocksize[0]-my,x*blocksize[1]-mx)
                    if p==1: print(n_d,n_mv,(my,mx))
    #return my,mx
def nearest_mv(mv,d,my,mx):
    global n_mv,n_d
    r=False
    if d < n_d:
        n_mv = mv
        n_d = d
        print(n_d,mv,my,mx)#x:bks,y:bks,mv:pixel
        r=True
    return n_d,r
def bksp(frame,bksize,funcs):
    global n_mv,n_d,my,mx
    if funcs[0]== find_mv: n_d=10000
    m=1 if remix in funcs else 0
    r,c,clrc= np.int32(np.array(frame.shape)/[bksize[0],bksize[1],1])
    #print(r,c)
    for i in range(0,r):
        print('\t\t\t\t\t',i,'/',r-1,end='\r', flush=True)
        for j in range(0,c):
            p=0;
            bk=frame[bksize[0]*i:bksize[0]*(i+1),bksize[1]*j:bksize[1]*(j+1),:]
            if i==j and j==2:
                p=0
            for func in funcs:
                if func==DCT:   bk=func(bk,p=0,m=m)
                elif (func == rebuild) or func == remix: func(idct=bk,i=i,j=j,bksize=bksize)
                elif func == find_mv: func(bk,x=j,y=i,p=0)
    '''if funcs[0]== find_mv: 
        print("n_mv",n_mv)
        print("(my,mx)",(my,mx))
        print("frame_global",np.array([my,mx]),np.array([my,mx])+np.array(bksize))
        print("frame",np.array([my,mx])-np.array(n_mv),np.array([my,mx])-np.array(n_mv)+np.array(bksize))
        show(frame_global[my:(my+bksize[0]),mx:(mx+bksize[1]),:],m=1,t=1,sc=40,s=1)
        show(frame[my-n_mv[0]:(my+bksize[0])-n_mv[0],mx-n_mv[1]:(mx+bksize[1])-n_mv[1]],m=1,t=2,sc=40)'''
def shift(frame):
    global n_mv
    #print("shift",n_mv)
    #show(frame,m=1,t=1)
    frames=copy.deepcopy(frame)
    #show(frames,m=1,t=2)
    w,h,chl=frame.shape
    ty=n_mv[0] if n_mv[0] >= 0 else 0
    by=w if n_mv[0] >= 0 else n_mv[0] + w
    lx=n_mv[1] if n_mv[1] >= 0 else 0
    rx=h if n_mv[1] >= 0 else n_mv[1] + h 
    frames[ty:by,lx:rx,:]=frame[ty-n_mv[0]:by-n_mv[0],lx-n_mv[1]:rx-n_mv[1],:]
#    show(frames,m=1,t=3)
    return frames
def show(frame,s=None,t="T",m=0,sc=1):
    r,c,chl=frame.shape
    if m==1:
        frame=cv.cvtColor(frame.astype('uint8'), cv.COLOR_YUV2BGR_YUY2)
    if sc!=1:
        frame=cv.resize(frame,(int(sc*c),int(sc*r)),interpolation=cv.INTER_LINEAR)
    cv.imshow(str(t),frame)
    cv.waitKey(s)
def DCT(bk,p=0,m=0):
    r,c,chl = np.int32(bk.shape)
    dct,idct,Qa,dQa=np.zeros([r,c,chl]),np.zeros([r,c,chl]),np.zeros([r,c,chl]),np.zeros([r,c,chl]);
    for i in range(0,chl):
        dct[:,:,i]=cv.dct(bk[:,:,i])
        Qa[:,:,i]=np.int32(Q(dct[:,:,i],l=i))
        f=Qa[:,:,i].flatten()
        if m>=0:
            #code(f[0],"ac")
            #f=np.delete(f,0)
            #print(f)
            cd.code_reset()
            zigzag(Qa[:,:,i].astype(np.int32),(r,c),cd.bks.append)
            #print(cd.bks)
            cd.code_block(np.int32(cd.bks))
            #print('\t\t\tsize:',len(cd.fin),end='\r',flush=True)
            #if len(cd.fin)<200: print(cd.fin)
        #else:
        dQa[:,:,i]=deQ(Qa[:,:,i],l=i)
        idct[:,:,i]=cv.idct(dQa[:,:,i])
    if p==1:
        print(dct[:,:,0])
        print(Qa[:,:,0])
        print(dQa[:,:,0])
        print(idct[:,:,0])
    return idct
def Q(dct,l=0):
    return dct/Q_m[l]
def deQ(Qa,l=0):
    return Qa*Q_m[l]
def rebuild(idct,i,j,bksize):
    global frame_global
    frame_global[bksize[0]*i:bksize[0]*(i+1),bksize[1]*j:bksize[1]*(j+1),:]=idct
def remix(idct,i,j,bksize):
    global frame_global
    frame_global[bksize[0]*i:bksize[0]*(i+1),bksize[1]*j:bksize[1]*(j+1),:]=idct+frame_global[bksize[0]*i:bksize[0]*(i+1),bksize[1]*j:bksize[1]*(j+1),:]
def YUV422(frame):#
    r,c,chl = np.int32(frame.shape)
    uv=np.zeros([r,c])
    y,u,v=cv.split(frame)
    u = cv.resize(u, (c//2, r), interpolation=cv.INTER_LINEAR)
    v = cv.resize(v, (c//2, r), interpolation=cv.INTER_LINEAR)
    y = np.round(y).astype(np.uint8)
    u = np.round(np.clip(u, 0, 255)).astype(np.uint8)
    v = np.round(np.clip(v, 0, 255)).astype(np.uint8)
    uv[:, 0::2] = u
    uv[:, 1::2] = v
    return np.dstack((y, uv)).astype('uint8')
def zigzag(arr,blocksize,func=print):
    N=blocksize[0]#方形適用
    i,j,d=0,0,False
    for n in range(N):
      func(arr[i,j])
      for s in range(n):
        i+= 1 if d else -1
        j+= -1  if d else 1
        func(arr[i,j])
      if d: i+=1
      else: j+=1
      d= not d
    i+= 1 if d else -1
    j+= -1  if d else 1
    for n in range(N-2,-1,-1):
      func(arr[i,j])
      for s in range(n):
        i+= 1 if d else -1
        j+= -1  if d else 1
        func(arr[i,j])
      if d: j+=1
      else: i+=1
      d= not d
############################################################
def main():
    global frame_global,M
    cam = cv.VideoCapture('MOV10s.mp4')
    f_c=0
    cd.clear_file()
    while cam.isOpened():
        ret,frame = cam.read()#BGR
        if not ret: break
        f_c+=1
    #for f in range(0,2):###############
        
        #print(f)if M==0:
     #   frame=cv.imread(str(f)+'.jpg') #<-------
        frame = cv.resize(frame, (512, 288))
        #frame = cv.resize(frame, (128, 72))
        print("第",f_c,"幀,","%.2f" %(f_c/30),"秒",flush=True)
        #show(frame,t="1")
        frame=YUV422(cv.cvtColor(frame, cv.COLOR_BGR2YUV))
        frame_global.resize(frame.shape)
        if M==1:
            #print("Find")
            bksp(frame,blocksize,[find_mv])
            #show(frame,m=1,t=2) #<-------
            #show(shift(frame),m=1,t=1) #<-------
            #print("Shift")
            framesh=shift(frame)
            frame=framesh-frame_global
            #print(np.sum(frame))
            #if np.sum(frame) > frame.shape[0]*frame.shape[1]*64:#1/4
            #    M=0
            #else:
                #print("P-frame")
            #cd.code_mv(n_mv)
            bksp(frame.astype(np.float32),blocksize,[DCT,remix])
        if M==0:
            #print("I-frame")
            frame=np.float32(frame)
            bksp(frame,blocksize,[DCT,rebuild])
            #M=1
        cd.write_file(cd.fin)
        cd.fin=''
        #show(frame_global,m=1,s=1,sc=10)
if __name__ == "__main__":
    main()