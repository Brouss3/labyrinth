#!/usr/bin/python3
# coding: utf-8

# Author    : https://github.com/Brouss3
# Date start: 2018/04/14
# Version st: 2018/05/12
# Date end  : 2018/05/27
# Version   : 0.0.5
# system    : linux only.

import curses
from os import system as bash
from os.path import isfile
from locale import setlocale, LC_ALL
from math import sin,cos, acos, pi, ceil, floor, sqrt, inf, log, pow
from time import sleep,time
setlocale(LC_ALL, '')

epsilon=10**-9  #math constant

#math funcs
sign = lambda x   : x and (1, -1)[x < 0]
addV = lambda x,y : (x[0]+y[0],x[1]+y[1])
subV = lambda x,y : (x[0]-y[0],x[1]-y[1])
smulV= lambda x,y : (x*y[0],x*y[1])
dist2= lambda x,y : (y[0]-x[0])**2+(y[1]-x[1])**2
dirs=[(-1,0),(0,-1),(1,0),(0,1)]

#world constants
#relative to special bash characters and colors
Cl_Blk  = 0
Cl_Red  = 1
Cl_Grn  = 2
Cl_Ylw  = 3
Cl_Blu  = 4
Cl_Prp  = 5
Cl_Tea  = 6
Cl_Wht  = 7
As_BG   = 40    
As_FG   = 30
As_Lgt  = 60
targetFPS=20.0    #limit it to 40 or the keyboard buffer will empty faster than it fills
sqSize=200.0
foc=90.0        #focal distance. variable
speedMax=400.0/targetFPS
drag=pow(0.40,1/targetFPS)
burst=pow(2**16,1/targetFPS)
angSpeed=1.0/targetFPS
printableSpeed = lambda v : "%05.1f"%(sqrt(v[0]**2+v[1]**2)*targetFPS)
printableTime  = lambda t : "%02d:%04.1f"%divmod(t,60)
#HUD constants:
alphabet={}
alphabet["0"]=alphabet[0]=[14, 17, 14]
alphabet["1"]=alphabet[1]=[18, 31, 16]
alphabet["2"]=alphabet[2]=[26,21,22]
alphabet["3"]=alphabet[3]=[21,21,10]
alphabet["4"]=alphabet[4]=[7,4,31]
alphabet["5"]=alphabet[5]=[23,21,9]
alphabet["6"]=alphabet[6]=[14,21,9]
alphabet["7"]=alphabet[7]=[25,5,3]
alphabet["8"]=alphabet[8]=[10,21,10]
alphabet["9"]=alphabet[9]=[18,21,14]
alphabet[":"]=[10]
alphabet["."]=[8]


class MMap:
    def __init__(self,sz,labsz,pos):
        self.size=tuple(sz)
        self.labsz=tuple(labsz)
        self.known=[]   #known map cells
        for x in range(labsz[0]):
            self.known.append([False]*labsz[1])
        self.setPos(pos)
    def setPos(self,pos):
        orig=[]
        for i in range(2):
            ori=pos[i]-floor(self.size[i]/2)
            if ori<0:
                ori=0
            elif ori+self.size[i]>self.labsz[i]:
                ori=self.labsz[i]-self.size[i]
            orig.append(ori)
        self.pos=pos
        self.orig=tuple(orig)
        self.learn(pos)
        for d in dirs:
            self.learn(addV(pos,d))
            
    def learn(self,pos):
        try:
            self.known[pos[0]][pos[1]]=True
        except:
            pass #cant learn what's out of lab map.
    
    def embedClnImage(self,lab,img,mmpos):
        for j in range(self.size[1]):
            y=self.orig[1]+j
            for i in range(self.size[0]):
                x=self.orig[0]+i
                if (x,y)==self.pos:
                    img[j+mmpos[1]][i+mmpos[0]]=Cl_Red
                elif self.known[x][y]:
                    img[j+mmpos[1]][i+mmpos[0]]= Cl_Blu if lab[x][y]==1 else (Cl_Wht+As_Lgt)
                elif img[j+mmpos[1]][i+mmpos[0]]<As_Lgt:
                    img[j+mmpos[1]][i+mmpos[0]]+=As_Lgt

#Game specific variables # Unpacked, the lab is as: (0,0) up left. (1,0) is southnward. (0,1) is eastward #value= 0 -> corridor / 1 -> wall. 
pos=orient=None #are in the packed lab. Just initialized here
#lab=[65535, 34835, 33748, 51749, 37513, 43261, 44805, 32885, 49049, 37027, 54807, 37829, 55853, 34985, 41571, 65535, 14, 11, -1.57]
#lab=[4087, 2565, 2777, 2091, 3713, 2261, 3433, 3851, 3153, 2725, 2057, 4095, 10, 8, -1.57]
#lab=[65535, 42103, 37155, 42313, 37469, 42319, 43284, 41669, 38961, 49997, 37969, 43461, 35347, 42405, 37009, 65535, 14, 11, -1.57]
lab=[65535, 42103, 37155, 42313, 37469, 42319, 43284, 41669, 38961, 49997, 37969, 43461, 35347, 42405, 37009, 65535, 14, 10, -0.785]
lab=[65535, 32845, 56017, 35467, 54353, 37511, 54489, 38421, 49985, 46231, 41292, 43605, 35669, 46337, 32939, 65535, 14, 13, 1.5707963267948966]
lab=[65535, 38437, 41097, 38227, 50005, 60417, 50109, 40099, 49684, 54613, 34965, 54737, 33925, 43629, 41097, 65535, 14, 12, -0.7853981633974484]

def getSquare(pos):
    global sqSize
    return(floor(pos[0]/sqSize),floor(pos[1]/sqSize))

def getLab(pos):
    global lab
    if type(pos[0])==float:
        pos=getSquare(pos)
    x,y=pos
    if (x<0 or y<0):
        return(-1)
    try:
        return(lab[x][y])
    except:
        return(-1)

def unpack(n,b):
    ret=[]
    for i in range(b):
        n,p=divmod(n,2)
        ret.append(p)
    return(ret)

def unpackLab(lab):
    global pos,orient,sqSize
    orient=lab.pop()
    pos=tuple(lab.pop()*sqSize+sqSize/2 for i in range(2))
    ln=ceil(log(max(lab),2))
    for i in range(len(lab)):
        lab[i]=unpack(lab[i],ln)

def line(pos,dir,nv,sec=False): #secondary param can be int -> nv,sec=maxnewx,maxnewy or bool to get 1 coord from the other
    if type(sec) in (int,float):  # (nv,sec) are x0,y0 -> search (x1,y1) as (x0,y1) and (x1,y0) in L(pos,dir). Return the nearer.
        ka=(nv -pos[0])/dir[0]
        kb=(sec-pos[1])/dir[1]  #No divide by zero check done
        k= ka if abs(ka)<abs(kb) else kb     #chooses the nearer collision.
    else:           #should be bool
        i=int(sec)                                      #ex: basic -> reverse=False -> i=0 (else True -> 1)
        k=(nv-pos[i])/dir[i] #Wish you didnt divide by 0 ;) #ex: nv is 1st coord, x, vert (else 2nd, y, hor)
    return(addV(pos,smulV(k,dir))) #returns collide point

def raytraceScene(posMax,scrWid,alphas,pos,orient,mmap):	#posMax is floorSize to calc square positions. TODO:Should use labSize
    global lab,sqSize
    prevContact=None    #used to determine tile change hence display tile bound in lighter color.
    colors=[0]*scrWid	#color of wall (depending on gameplay. V0-> wall orientation)
    dists=[inf]*scrWid	#zbuffer
    for cln in range(scrWid):		#for each screen column 
        ax=orient+alphas[cln]			# (associated with an angle and line on the floor map)
        vw=[cos(ax),sin(ax)]	        # normalized view vector
        if vw[0]>epsilon:				#if southward: set values
            px1=ceil(pos[0]/sqSize)*sqSize + 2*epsilon      #1st x on next square. as float cause pos
            col=Cl_Blk
            inc=sqSize                          #to south
        elif vw[0] < -epsilon:
            px1=floor(pos[0]/sqSize)*sqSize-2*epsilon		#if northward: set values
            col=Cl_Ylw
            inc=-sqSize
        else:
            vw[0]=0.0
            px1=-2
        if px1>-2:				# if can hit horizontal line
            p1=line(pos,vw,px1)
            while 0<=p1[0]<posMax[0] and 0<=p1[1]<posMax[1]:	#move along viewline 1 square up/down till exit lab
                if getLab(p1)==1:	#is wall?
                    dists[cln]=dist2(pos,p1)
                    colors[cln]=col
                    contact=(col,getSquare(p1)) #is a tuple (wall facing direction , (square.x , square.y) )
                    break						#store collision data and break north/south view loop.
                px1+=inc             
                p1=line(pos,vw,px1)
        if vw[1]>epsilon:           # if eastward
            py1=ceil(pos[1]/sqSize)*sqSize +2*epsilon
            col=Cl_Red
            inc=sqSize
        elif vw[1]<-epsilon:
            py1=pos[1]//sqSize*sqSize-2*epsilon
            col=Cl_Prp
            inc=-sqSize
        else:
            vw[0]=0.0
            py1=-2
        if py1>-2:
            p1=line(pos,vw,py1,True)
            while 0<=p1[0]<posMax[0] and 0<=p1[1]<posMax[1]:	#move along viewline 1 square left/right till exit lab
                d2=dist2(pos,p1)			
                if d2>dists[cln]:		#do not test further than dist already found.
                    break
                if getLab(p1)==1:
                    dists[cln]=d2
                    colors[cln]=col
                    contact=(col,getSquare(p1))
                    break
                py1+=inc             
                p1=line(pos,vw,py1,True)
        if dists[cln]==inf:
            contact=None
        if contact!=prevContact and contact!=None: 
            #TODO: learn mmap? dist max? ex 3 cases=600 square it ->360000
            if cln>0 and (dists[cln-1] < dists[cln]) and colors[cln-1]<As_Lgt:
                colors[cln-1]+=As_Lgt
            elif cln>0 and colors[cln]<As_Lgt:
                colors[cln]+=As_Lgt
        prevContact=contact
    return(colors,dists)	

def buildScreenAsClns(scrSize,colors,dists):	
    global foc
    scrHei,scrWid=scrSize
    scrHei*=2   #half chr heigh
    scn=[]
    for cln in range(scrWid):
        if dists[cln]!=inf:
            h = foc*sqSize/(foc+sqrt(dists[cln]))
            h=int(min(h,scrHei))
        else:
            h=0
        r=(scrHei-h)//2
        L=[Cl_Blu+As_Lgt]*r+[colors[cln]]*h+[Cl_Grn]*(scrHei-h-r)    #list of colors entries
        scn.append(L)
    return(scn)

def addText(img,startPos,color,txt):
    chrHei=5
    cln=startPos[1]
    for s in txt:       #for each letter
        if s==" ":
            cln+=4
            continue
        tab=alphabet[s]
        i=0
        for compact in tab: #for each column of the letter
            icln=img[cln]
            for j in range(chrHei):
                if compact%2:
                    icln[startPos[0]+j]=color
                compact>>=1
            cln+=1
        cln+=1

def buildScrStr(scn,scrSize,scr=None):  #as Lines
    dsiplay="\r" if scr else ""
    c=lg=i=-1
    scrHei,scrWid=scrSize
    colds=[-1]*2        #color code of the last two charxels
    for lg in range(scrHei):
        for c in range(scrWid):
            cols=list(scn[c][2*lg+i] for i in range(2)) #SMART: since scn needs to be transposed: c <-> 2*lg+i
            if cols[0]==cols[1]:
                if cols[0]==colds[0]:
                    dsiplay+=" "
                elif cols[0]==colds[1]:
                    dsiplay+=chr(9608)
                else:
                    dsiplay+="\033[%im "%(cols[0]+As_BG)
                    colds[0]=cols[0]
            else:
                if cols==colds:
                    dsiplay+=chr(9604)#colds[0] up
                elif cols[0]==colds[1] and cols[1]==colds[0]:
                    dsiplay+=chr(9600)#colds[0] down
#                    colds[0]=cols[0]
                else:
                    dsiplay+="\033[%im\033[%im▄"%(cols[0]+As_BG,cols[1]+As_FG)
                    colds[0:2]=cols[0:2]
        if scr==None:
            colds=[-1]*2
            dsiplay+="\033[0m\n"
    dsiplay+="\033[0m\x1b[1A\x1b[1A" if scr else ""    #go up 2 lines with \x1b[1A to avoid a black line with cursor
    return(dsiplay)

def testCld(pos,npos,rad):
    if (pos==npos):   #no move, no colllide
        return(npos)
    sq=getSquare(pos)
    delta=subV(npos,pos)
    dsq= (sign(delta[0]) , sign(delta[1]))
    bx= sqSize*sq[0]+ (rad if delta[0]<0 else sqSize -rad)  #square boundary before...
    by= sqSize*sq[1]+ (rad if delta[1]<0 else sqSize -rad)  #   collide test needed
    isInboundx= (delta[0]>=0) == (npos[0]<=bx)  #bool: did movement go... 
    isInboundy= (delta[1]>=0) == (npos[1]<=by)  #      beyond boundary
    if isInboundx and isInboundy:   #remain inside boundaries. Cannot collide
        return(npos)
    wallx=getLab( addV(sq,(dsq[0],0)))== 1      #bool: is there a wall... 
    wally=getLab( addV(sq,(0,dsq[1])))== 1      #   beyond the boundary
    if wallx or wally:  #if a wall is found, correct pos if collide and return.
        npx=npos[0] if isInboundx or not wallx else bx
        npy=npos[1] if isInboundy or not wally else by
        return((npx,npy))
    if isInboundx or isInboundy or getLab(addV(sq,dsq))!=1:     #Chk 4 collide by an angle
        return(npos)                                                        #nope. Go ahead
    #decide which side to slide
    p1=(npos[0],by)
    p2=(bx,npos[1])
    return p1 if  dist2(pos,p1) > dist2(pos,p2)  else p2

def move(pos,speed,accel,rad):
    global drag
    if speed==(0,0) and not accel:
        return(pos,speed)
    if accel:
        speed=addV(speed,accel)
    speed=smulV(drag,speed)
    npos=addV(pos,speed)
    scalSpeed=sqrt(sum(speed[i]**2 for i in range(2)))
    if scalSpeed>speedMax:
        speed=smulV(speedMax/scalSpeed,speed)
        npos=addV(pos,speed)
    npos=testCld(pos,npos,rad)
    speed=subV(npos,pos)
    return(npos,speed)
    
def calcAlphas(foc,scrWid):     #precalc anglestoCam depending on foc and scrWid
    deltalpha=acos(foc/(foc**2+(scrWid/2)**2)**0.5)
    return(list(2*deltalpha*c/(scrWid-1)-deltalpha for c in range(scrWid-1,-1,-1)))

def main(stdscr):
    global foc,sqSize,targetFPS  #game variables
    global lab,pos,orient                   #world variables
    #init curses screen
    curses.noecho()		#dont echo on getch/str
    curses.cbreak()		#dont wait for \n on getch/str
    curses.curs_set(0)
    stdscr.nodelay(True)	# dont wait for ch in getch/str
    stdscr.keypad(True)		# map arrow keys to special values
    bash("xset r rate 50 25") #fasten then keyboard pepeat latency
    #init sizes depending on lab and window
    unpackLab(lab)
    labSize=(len(lab),len(lab[0]))
    floorSize=(sqSize*labSize[0],sqSize*labSize[1])
    screenSize = (scrHei,scrWid) = stdscr.getmaxyx() 
    npos=pos    #future pos is pos
    speed=(0.0,0.0)
    c=-1	#last ascii read = None
    cldRad=5.0      #collide radius
    alphas=calcAlphas(foc,scrWid)   #init  cam
    sq=getSquare(pos)
    map=MMap((9,9),labSize,sq)
    playLoops=0
    while (113!=c):      #############  main loop #################
        t=time()    #start mesure time 
        #read keyboard and change cam data accordingly.
        c = stdscr.getch()
        stdscr.getstr() #empty buffer
        vw=(cos(orient),sin(orient))
        accel=False
        if 260==c:      # key left-> turn left
            orient+=angSpeed
        elif 261==c:    # key right->turn right
            orient-=angSpeed
        elif 259==c:    #key up -> forward
            accel=smulV(burst,vw)
        elif 258==c:    #key down -> backward
            accel=smulV(-burst,vw)
            stdscr.getstr() #empty buffer bc strangely "backawrd" is not flushed previously.
        elif 97==c: # "a" to zoom out
            foc-=0 if foc<=30 else 5 if foc <=100 else 10
            alphas=calcAlphas(foc,scrWid)
        elif 122==c: # "z" to zoom in
            foc+=5 if foc<=100 else 10 if foc<=250 else 0
            alphas=calcAlphas(foc,scrWid)
        elif 112==c: # "p" to print screen
            f=open("lab.screenshot.txt","w")
            f.write(buildScrStr( scrAsClns ,screenSize))
            f.close()
        #acceleration, drag, chk wall collision.
        pos,speed=move(pos,speed,accel,cldRad)
        nsq=getSquare(pos)
        if nsq!=sq:         #update mmap according to new square
            map.setPos(nsq)
            sq=nsq
        #calc new screen values and display
        Lclr,Ldist2=raytraceScene(floorSize,scrWid,alphas,pos,orient,map)
        scrAsClns=buildScreenAsClns(screenSize,Lclr,Ldist2)     #build screen image
        map.embedClnImage(lab,scrAsClns,(scrHei*2-10,scrWid-10))  #add minimap to image
        addText(scrAsClns,(1,1),Cl_Wht,printableSpeed(speed))
        addText(scrAsClns,(1,scrWid-24),Cl_Wht,printableTime(playLoops/targetFPS))   # will crash after an hour haha!
        print(buildScrStr( scrAsClns ,screenSize ,stdscr))
        stdscr.move(0,0)
        stdscr.refresh()
        if not((0<=pos[0]<floorSize[0]) and (0<=pos[1]<floorSize[1])):
            finalTime=playLoops/targetFPS
            s="%02i:%5.2f"%divmod(finalTime,60)
            addText(scrAsClns,(10,3),Cl_Wht,s)
            addText(scrAsClns,(11,2),Cl_Wht,s)
            addText(scrAsClns,(11,3),Cl_Wht,s)
            addText(scrAsClns,(10,2),Cl_Blk,s)
            print(buildScrStr( scrAsClns ,screenSize ,stdscr))
            bash("xset r rate 660 25") #restore default linux keyboard repeat delays 660ms to start repeats at 25 chr per sec
            c=stdscr.getstr()
            stdscr.nodelay(False)
            stdscr.refresh()
            c=stdscr.getstr()
            return
        playLoops+=1
        sleep(max(0, (1.0/targetFPS)+t-time() ))
    stdscr.getstr()
    stdscr.nodelay(False)
    bash("xset r rate 660 25") #when exit main loop

try:
    if isfile("notice.txt"):
       bash("more notice.txt") 
       c=input()
    curses.wrapper(main)
finally:
    bash("xset r rate 660 25") #restore default linux keyboard repeat delays 660ms to start repeats at 25 chr per sec
