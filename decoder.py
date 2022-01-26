import code_t as cd
import DC,numpy as np
import cv2 as cv
size=[int(288/8),int(512/8),2]
frame=np.zeros((288,512,2))
preframe=np.zeros((288,512,2))
p=[0,0]
def decode_bks(s):
    global frame,p,size,preframe
    bks_count=0
    b=cd.read_file(s)
        #print(b[:64])
    c = cd.split(b)
    #print(len(c))
    blk=np.zeros((8,8,2))
    while len(c)>0:
        #if c[0]: print("I-frame")
        #else: print("P-frame")
        #c.pop(0)
        r=0
        count=0
        while r==0:
            #print("block:",count,end='\r',flush=True)
            for i in range(2):
                blk[:,:,i],c=return_frame(c)
                #blk=np.stack((idct, uv), axis=2)
            r=rebuild(blk)
            count+=1
            DC.show(frame,m=1,s=1,sc=2)
            #r=cd.decode_mv(c)
            #print(r)
        reset()
        #preframe=frame
def reset():
    global frame,p
    p=[0,0]
    #frame=np.zeros((72,128,2))
def rebuild(blk):
    global frame,size,p
    #print(p[0],size[0])
    if p[0]==size[0]: return 1
    #print(blk)
    frame[  p[0]*8:(p[0]+1)*8 , p[1]*8:(p[1]+1)*8 ,:]+=blk
    p[1]+=1  
    if p[1] >= size[1]: p[1]=0; p[0]+=1
    return 0
def return_frame(c):
    pre=len(c)
    r=cd.decode_analyze(c)
    c = r
    c=c[(8-(pre-len(c))%8):]
    #print('d',pre-len(c))
    cd.rebuild.resize(64)
    #print(cd.rebuild)
    bks=dezigzag(cd.rebuild,(8,8))
    cd.rebuild=np.int32([])
    dQa = DC.deQ(bks)
    idct =cv.idct(dQa)
    return idct,c
def dezigzag(arr,blocksize,func=print):
    N=blocksize[0]#方形適用
    i,j,d=0,0,False
    bks,c=np.zeros(blocksize),0
    def set(i,j,c):
        bks[i,j]=arr[c]
        return c+1
    for n in range(N):
      c=set(i,j,c)
      for s in range(n):
        i+= 1 if d else -1
        j+= -1  if d else 1
        c=set(i,j,c)
      if d: i+=1
      else: j+=1
      d= not d
    i+= 1 if d else -1
    j+= -1  if d else 1
    for n in range(N-2,-1,-1):
      c=set(i,j,c)
      for s in range(n):
        i+= 1 if d else -1
        j+= -1  if d else 1
        c=set(i,j,c)
      if d: j+=1
      else: i+=1
      d= not d
    #print(bks)
    return bks
decode_bks("test.bin")