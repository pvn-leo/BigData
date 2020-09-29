#!/usr/bin/python3
import sys
current=None
add=None
for line in sys.stdin:
	line = line.strip()
	
	k,v=line.split(',') # v will contain the sum of contributions of every node that links to k
	k=k.strip("\'")
	if current==k:
		add+=float(v)
	else:
		
		if current!=None:
			add=0.15+(0.85*add) # calculating new rank
			add="{:.5f}".format(add)
			print(current,add,sep=',')
		current=k
		add=float(v)
if current==k:
	add=0.15+(0.85*add)
	add="{:.5f}".format(add)
	print(current,add,sep=',')
