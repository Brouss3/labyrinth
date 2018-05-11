#!/usr/bin/python3
# coding: utf-8

####################
# Author    : https://github.com/Brouss3
# Date start: 2018/04/14
# Version st: 2018/05/03
# Date end  : 2018/05/10
# Version   : 0.0.3
# system    : linux only.

import curses
from os import system as bash
from os.path import isfile
from locale import setlocale, LC_ALL
from math import sin,cos, acos, pi, ceil,floor, sqrt, inf, log
from time import sleep,time

setlocale(LC_ALL, '')

#math constants
epsilon=10**-9

#math funcs
sign = lambda x   : x and (1, -1)[x < 0]
addV = lambda x,y : (x[0]+y[0],x[1]+y[1])
subV = lambda x,y : (x[0]-y[0],x[1]-y[1])
smulV= lambda x,y : (x*y[0],x*y[1])
dist2= lambda x,y : (y[0]-x[0])**2+(y[1]-x[1])**2

#worldview constants
sqSize=200.0
foc=90     #in fact, is a variable
clut=[62,64,0,3,1,5] # grn, blu, grey,yelo,red, grue. Note that 'Light" (+60) included in gnd/sky = clut[0/1].

#Game specific variables # Unpacked, the lab is as: (0,0) up left. (1,0) is southnward. (0,1) is eastward #value= 0 -> corridor / 1 -> wall. 
pos=orient=None #are in the packed lab. Just initialized here
lab=[65535, 34835, 33748, 51749, 37513, 43261, 44805, 32885, 49049, 37027, 54807, 37829, 55853, 34985, 41571, 65535, 2900.0, 2300.0, -1.57]

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
    global pos,orient
    orient=lab.pop()
    pos=lab.pop(),lab.pop()
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

def raytraceScene(posMax,scrWid,alphas,pos,orient):	#posMax is floorSize to calc square positions. TODO:Should use labSize
    global lab,sqSize
    prevContact=None    #used to determine tile change hence display tile bound in lighter color.
    colors=[0]*scrWid	#color of wall (depending on gameplay. V0-> wall orientation)
    dists=[inf]*scrWid	#zbuffer
    for cln in range(scrWid):		#for each screen column 
        ax=orient+alphas[cln]			# (associated with an angle and line on the floor map)
        vw=[cos(ax),sin(ax)]	        # normalized view vector
        if vw[0]>epsilon:				#if southward: set values
            px1=ceil(pos[0]/sqSize)*sqSize      #1st x on next square. as float cause pos
            col=2
            inc=sqSize                          #to south
        elif vw[0] < -epsilon:
            px1=floor(pos[0]/sqSize)*sqSize-2*epsilon		#if northward: set values
            col=3
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
            py1=ceil(pos[1]/sqSize)*sqSize
            col=4
            inc=sqSize
        elif vw[1]<-epsilon:
            py1=pos[1]//sqSize*sqSize-2*epsilon
            col=5
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
        if contact!=prevContact and cln!=0 and contact!=None: 
            if colors[cln-1]>5 and colors[cln-2]==colors[cln]:#patch against "see throu diagonals". TODO: better that
            #if(False):
                colors[cln-1]=colors[cln]+4
            else:
                colors[cln]+=4
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
        L=[1]*r+[colors[cln]]*h+[0]*(scrHei-h-r)    #list of clut entries
        scn.append(L)
    return(scn)

def buildScrStr(scn,scrSize,scr=None):  #as Lines
    dsiplay="\r" if scr else ""
    c=lg=i=-1
    scrHei,scrWid=scrSize
    for lg in range(scrHei):
        for c in range(scrWid):
            cols=list(scn[c][2*lg+i] for i in range(2)) #SMART: since scn needs to be transposed: c <-> 2*lg+i
            if cols[0]==cols[1]:
                dsiplay+="\033[%im "%(clut[cols[0]]+40)
            else:
                dsiplay+="\033[%im\033[%im▄"%(clut[cols[0]]+40,clut[cols[1]]+30)
        dsiplay+="" if scr else "\033[0m\n"
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

def calcAlphas(foc,scrWid):     #precalc anglestoCam depending on foc and scrWid
    deltalpha=acos(foc/(foc**2+(scrWid/2)**2)**0.5)
    return(list(2*deltalpha*c/(scrWid-1)-deltalpha for c in range(scrWid-1,-1,-1)))

def main(stdscr):
    global lab,foc,sqSize,clut  #game variables
    global lab,pos,orient       #world variables
    #init curses screen
    curses.noecho()		#dont echo on getch/str
    curses.cbreak()		#dont wait for \n on getch/str
    stdscr.nodelay(True)	# dont wait for ch in getch/str
    stdscr.keypad(True)		# map arrow keys to special values
    bash("xset r rate 50 25") #fasten then keyboard pepeat latency
    for i in range(2,6):    #enhance CLUT: add lighter colors
        clut.append(clut[i]+60)
    #init sizes depending on lab and window
    unpackLab(lab)
    labSize=(len(lab),len(lab[0]))
    floorSize=(sqSize*labSize[0],sqSize*labSize[1])
    screenSize = (scrHei,scrWid) = stdscr.getmaxyx() 
    npos=pos    #future pos is pos
    c=-1	#last ascii read = None
    cldRad=5.0      #collide radius
    alphas=calcAlphas(foc,scrWid)   #init  cam
    #mainloop
    while (113!=c):
        #read keyboard and change cam data accordingly.
        c = stdscr.getch()
        stdscr.getstr() #empty buffer
        vw=(cos(orient),sin(orient))
        if c==260:      # key left-> turn left
            orient+=0.07
        elif c==261:    # key right->turn right
            orient-=0.07
        elif c==259:    #key up -> forward
            npos=addV(pos,smulV(10,vw))
        elif c==258:    #key down -> backward
            npos=subV(pos,smulV(10,vw))
            stdscr.getstr() #empty buffer bc strangely "backawrd" is not flushed previously.
        elif c==97: # "a" to zoom out
            foc-=0 if foc<=30 else 5 if foc <=100 else 10
            alphas=calcAlphas(foc,scrWid)
        elif c==122: # "z" to zoom in
            foc+=5 if foc<=100 else 10 if foc<=250 else 0
            alphas=calcAlphas(foc,scrWid)
        elif c==112: # "p" to print screen
            f=open("lab.screenshot.txt","w")
            f.write(buildScrStr( scrAsClns ,screenSize))
            f.close()
        t=time()    #mesure time to mod sleep time and stabilize framerate
        #chk wall collision & correct pos accordingly.
        npos=testCld(pos,npos,cldRad)
        pos=npos
        #calc new screen values and display
        Lclr,Ldist2=raytraceScene(floorSize,scrWid,alphas,pos,orient)
        scrAsClns=buildScreenAsClns(screenSize,Lclr,Ldist2)
        print(buildScrStr( scrAsClns ,screenSize ,stdscr))
        stdscr.move(0,0)
        stdscr.refresh()
        if not((0<=pos[0]<floorSize[0]) and (0<=pos[1]<floorSize[1])):
            print("\rVictory. Now you can rule the world and marry princess Irulz. That or go back to work.")
            sleep(2)
            c=stdscr.getstr()
            stdscr.nodelay(False)
            stdscr.refresh()
            c=stdscr.getstr()
            break
        t-=time()
        sleep(max(0,0.1+t))
    stdscr.getstr()
    bash("xset r rate 660 25") #when exit main loop
    stdscr.getstr()

try:
    if isfile("notice.txt"):
       bash("more notice.txt") 
       c=input()
    curses.wrapper(main)
finally:
    bash("xset r rate 660 25") #restore default linux keyboard repeat delays 660ms to start repeats at 25 chr per sec













