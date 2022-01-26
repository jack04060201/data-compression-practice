import numpy as np,math,struct
z_count=0
#DC:127  \ 7 
#AC:+-64 / bits
EOB=8
cb={
'0':1,
'10':2,
'110':3,
'1110':4,
'11110':5,
'111110':6, #BLOCK為8*8，連續0長度最多63
'1111110':7, #DC最高127
'11111110':EOB #EOB
}
temp=''
test='101011010101110100001001'
fin=''
bks=[]
frame=[]
ct=0
mv=[]
testbks=np.int32([59,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0])
rebuild=np.int32([])
#I-frame 傳I->傳DC值->傳差異值
#P-frame 傳P->傳差異值                                            2bs | x2 | 3bs| 5  | 1bs| x1 | 3bs| 4  | 1bs| x0 | 2bs| -2 |
#傳差異值 傳0位數bits數->傳0位數->傳數值bits數->傳數值 00504-2 -> 10  | 10 | 110| 101| 0  | 1  | 110| 100| 0  | 0  | 10 | 01 | 24bits
#                          DC                    AC
def code_reset():
    global bks,temp,z_count
    bks=[]
    temp=''
    z_count=0
def split(s):
    return [char for char in s]
def code_block(bk,m=0):
    global ct,fin
    ct =0
    #print(bk)
    for c in bk:
        ct+=1
        send_code(code(c))
    #print(ct)
    #if ct<64:
     #   print(ct)
    send_code(list(cb)[EOB-1])#EOB
    if len(fin)%8 != 0:
        send_code((8-(len(fin)%8))*'1')
def code_mv(mv):
    global fin
    send_code(code(mv[0],sk_z=True))
    send_code(code(mv[1],sk_z=True))
    send_code(list(cb)[EOB-1])#EOB
    if len(fin)%8 != 0:
        send_code((8-(len(fin)%8))*'1')
def code(N,m=0,sk_z=False):
    global z_count,fin,cb
    #print(N,m)
    if m==2:
        return list(cb)[N-1]
    if N==0 and m==0: 
        if m==0: z_count+=1; return -1
    else:
        if N==0 and sk_z and m==1: send_code('00'); return -1
        r=int(math.log2(abs(N)))+1
        if not sk_z:
            send_code(code(z_count,m=1,sk_z=True))
            z_count=0
        send_code(code(r,m=2))
        b=(pow(2,r)-1-abs(N)) if (N < 0 and m==0) else N
    return format(b, '0'+str(r)+'b')
def send_code(b):
    global fin
    #print(b)
    if b != -1 : fin += str(b); #print(str(b))
def match(b):
    global temp,cb
    #print('t',temp[:10],b)
    temp+=b
    if temp in cb:
        c=cb[temp]
        #print("bits:",c)
        temp=''
        return c
    return -1
def decode(code,m=0):
    global rebuild,mv
    l=len(code)
    b=int(code,2)
    b=-(pow(2,l)-b-1) if code[0] == '0' and m==0 else b
    #print(code,b)
    if m==0: rebuild=np.hstack([rebuild , int(b)])
    elif m==2: mv=np.hstack([mv , [0 for i in range(b)]]);print(mv)
    else: rebuild=np.hstack([rebuild , [0 for i in range(b)]])
def decode_analyze(c):
    global fin,temp
    z=True
    count=0
    #print(c[:30])
    while len(c)>0:
        if count==64: 
            #print("EOB")
            return c #EOB
        r=match(c[0]) #解析bits數
        if r==EOB: 
            #print("EOB")
            return c #EOB
        #if not r ==-1: print(r)
        c.pop(0)
        #print(c)
        #print('r',r)
        if r > 0:
            #print(z)
            count+=1
            decode(''.join(c[:r]),m=z)
            c=c[r:]
            z=not z
    temp=''
    return c
def decode_mv(c):
    global fin,temp,mv
    count=0
    while len(c)>0:
        if count==2: 
            #print("EOB")
            return c #EOB
        r=match(c[0]) #解析bits數
        print(r,count)
        if r==EOB: 
            #print("EOB")
            return c #EOB
        c.pop(0)
        if r > 0:
            count+=1
            decode(''.join(c[:r]),m=2)
            c=c[r:]
    temp=''
    return c
def clear_file():
    bin = open("test.bin", "wb")
    bin.close()
def write_file(input):
    bin = open("test.bin", "ab")
    byte = int(input,2).to_bytes((len(input) + 7) // 8, byteorder='big')
    bin.write(byte)
    bin.close()
def read_file(f_name):
    f = open(f_name, "rb")
    b=f.read()
    b=format(int.from_bytes(b, byteorder='big'),'0'+str(8*len(b))+'b')
    print(b[:64])
    b=split(str(b))
    return b
def main():
    global testbks,fin
    code_block(testbks)
    print('finally:',fin,'\nsize:',len(fin))
    clear_file()
    write_file(fin)
    #print(fin)
    
    b=read_file("test.bin")
    #print(b)
    #print(' '.join(map(lambda x: '{:08b}'.format(x), b)))
    #print(format(int.from_bytes(b, byteorder='big'),'b'))
    c = split(b)
    decode_analyze(c)
    print('Origin :',testbks)
    rebuild.resize(64)
    print('rebuild:',rebuild.astype(np.int32))
    print('Same',np.all(testbks==rebuild))
    
if __name__ == "__main__":
    main()
