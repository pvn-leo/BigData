#!/usr/bin/python3
import sys

path=''
if sys.argv[1]:
    path = sys.argv[1]  # will hold the path to the file v

rank_vector=dict() # will hold current page rank  

v_file=open(path,"r")

if v_file:

	lines=v_file.readlines()
	
	for line in lines:
		line=line.strip()
		key,value=line.split(',')
		if key not in rank_vector:
			rank_vector[key]=float(value) # the rank is updated

new_vector=dict() # will hold the sum of contributions of each node that links to respective key
for line in sys.stdin:
	
	line = line.strip()
	key,value=line.split('\t')
	
	value=value.strip('[') # processing string
	value=value.strip(']')
	
	value=value.split(',') # converting to list
	n=len(value)
	
	add=rank_vector[key]/n 
	add=float("{:.2f}".format(add)) #calculating contribution of key to every node it points to 
	
	
	for val in value: # updating sum of contributions
		val=val.strip()
		if val not in new_vector:
			new_vector[val]=add
		else:
			new_vector[val]+=add

for key in new_vector:
	print(key,new_vector[key],sep=',') #printing
	
	
