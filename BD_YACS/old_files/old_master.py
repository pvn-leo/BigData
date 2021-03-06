import json
import sys
from socket import *
import time
import random
import threading
from datetime import datetime
import os
import csv

# dt_object = datetime.fromtimestamp(arrival_time)
'''
arguments are parsed here
'''
try:
	config_path = sys.argv[1]
except IndexError:
	print("Config path not passed as arg")
	print("Exiting ......")
	exit()

try:
	schedule_algo = sys.argv[2]
except IndexError:
	print("Scheduling algorithm not specified - [RANDOM, RR, LL]")
	print("Exiting ......")
	exit()

with open(config_path) as f:
	summary = json.load(f)
f.close()

if(os.path.isfile("logs/job_log.csv") and os.path.isfile("logs/task_log.csv")):
	os.remove("logs/job_log.csv")
	os.remove("logs/task_log.csv")
'''
done
'''
def logger(mssg,what):
	#with open("log.json") as r:
	#	old = json.load(r)
	#old.update(mssg)
	if(what == 'jobs'):
		filename = "logs/job_log.csv"
		column_name = ["algo", "job_id", "map_tasks_done", "reduce_tasks_done", "arrival_time", "end_time", "job_done"]
	else:
		filename = "logs/task_log.csv"
		column_name = ["algo", "job_id", "worker_id", "task_id", "arrival_time", "end_time", "duration", "done"]

	file_exists = os.path.isfile(filename)
	mssg["algo"] = schedule_algo
	with open(filename, 'a') as file:
		writer = csv.DictWriter(file, delimiter=',', lineterminator='\n',fieldnames=column_name)

		if (not file_exists):
			writer.writeheader()

		writer.writerow(mssg)
	file.close()


'''
class definitions
'''

class worker:
	def __init__(self, wid, slot, port):
		self.id = wid
		self.slot = slot
		self.occupied_slots = 0
		self.port = port
		self.mutex = threading.Semaphore(1)
	def print(self):
		print("--> Status of worker")
		print(f"	worker id: {self.id}, worker total slots: {self.slot}, worker occupied slots: {self.occupied_slots} , worker port: {self.port}")


class task:
	def __init__(self, task_id, duration):
		self.task_id = task_id
		self.duration = duration
		self.done = False
		self.arrival_time = -1
		self.end_time = -1
	def print(self):
		#print("task_id:  1_M2   duration:  4    status:  True")
		print("task_id: {0} | duration: {1} | status: {2} ".format(self.task_id, self.duration, self.done))
		#print("task_id: ", self.task_id, "  duration: ", self.duration, "   status: ", self.done)
	def to_json(self, job_id, worker_id):
		temp = {"job_id": job_id, "worker_id": worker_id, "task_id": self.task_id, "duration":self.duration, "done":self.done}
		return temp

class job:
	def __init__(self, job_id):
		self.job_id = job_id
		self.map_tasks = []
		self.reduce_tasks = []
		self.map_tasks_done = 0 #count number of map_task.done == True
		self.reduce_tasks_done = 0 #count number of red_task.done == True
		self.job_done = False #true only when (map_tasks_done = True and reduce_tasks_done = True)
		self.arrival_time = datetime.now().timestamp()
		self.end_time = -1
	def print(self):
		print("Job          : ", self.job_id, "\t status: ", self.job_done)
		print("map_tasks    : ", len(self.map_tasks),"       map_task_done: ", self.map_tasks_done)
		print("-------------------------------------------")
		for i in self.map_tasks:
			i.print()
		print("-------------------------------------------")
		print("reduce_tasks : ", len(self.reduce_tasks),"       red_task_done: ", self.reduce_tasks_done)
		print("-------------------------------------------")
		for i in self.reduce_tasks:
			i.print()
		print("-------------------------------------------")
	def to_json(self):
		temp = {"job_id": self.job_id,"map_tasks_done":self.map_tasks_done, "reduce_tasks_done":self.reduce_tasks_done, "arrival_time":self.arrival_time,"end_time":self.end_time,  "job_done":self.job_done}
		return temp
'''
done
'''

'''
global variables are declared here
'''
workers = [] #list of worker objects
num_workers = 0

jobs = []
num_jobs = 0
'''
done
'''

'''
all semaphores are declared here
'''
lock = threading.Semaphore(1)
'''
done
'''

print('Workers init started......')
for line in summary['workers']:
	workers.append(worker(line['worker_id'], line['slots'], line['port']))

for  i in workers:
	worker.print(i)
num_workers = len(workers)
print('Workers init ended......')

'''
function definitions
'''
def scheduling_algo():
	if schedule_algo == 'RANDOM':
		while True:
			# listen_updates()

			i = random.randrange(0, len(workers))

			if workers[i].occupied_slots < workers[i].slot:
				return i

	if schedule_algo == 'RR':
		workers_sorted = sorted(workers, key=lambda worker: worker.id)
		num_workers = len(workers)
		i = 0

		while True:
			if workers_sorted[i].occupied_slots < workers_sorted[i].slot:
				for idx in range(len(workers)):
					if workers_sorted[i] == workers[idx]:
						return idx

			i = (i + 1)%(num_workers - 1)

	if schedule_algo == 'LL':
		while True:
			least_loaded = sorted(workers, key = lambda worker: worker.slot - worker.occupied_slots)

			if least_loaded[0].occupied_slots < least_loaded[0].slot:
				for idx in range(len(workers)):
					if least_loaded[0] == workers[idx]:
						return idx

			time.sleep(1)

def send_task_to_worker(task,job_id):
	#call this under listen_to_worker since they are in the same thread

	print("\nSending task to worker...")
	i = scheduling_algo()
	workers[i].mutex.acquire()
	port = workers[i].port #eventually do this
	workers[i].occupied_slots+=1
	workers[i].print()
	with socket(AF_INET, SOCK_STREAM) as s:
		s.connect(("localhost", port))
		send_task = task.to_json(job_id, i)
		message=json.dumps(send_task)
		s.send(message.encode())
	workers[i].mutex.release()


def listen_to_requests():
	#opening this will make port 5000 active and recieve requests from requests.py
	request = socket(AF_INET,SOCK_STREAM) #init a TCP socket
	request.bind(('',5000)) #listen on port 5000, from requests.py
	request.listen(3)
	print("Master ready to recieve job requests from requests.py")
	k = 0 #as of for now only 3, dont know how to take as many as needed
	while True:
		# lock.acquire()
		connectionSocket, addr = request.accept()
		message = connectionSocket.recv(2048) # recieve max of 2048 bytes
		print("Received job request from requests.py : ", addr)
		mssg = json.loads(message)


		j = job(mssg['job_id']) #init a job
		for maps_i in mssg['map_tasks']:
			j.map_tasks.append(task(maps_i['task_id'], maps_i['duration'])) #append all map_tasks of a job, by initing task
		for reds_i in mssg['reduce_tasks']:
			j.reduce_tasks.append(task(reds_i['task_id'], reds_i['duration']))#append all red_tasks of a job, by initing task
		lock.acquire()
		jobs.append(j) #add to list of jobs
		lock.release()

		for t in j.map_tasks:
			# # send_task_to_worker(t, j.job_id)
			# sender_thread = threading.Thread(target=send_task_to_worker,args=(t,j.job_id,))
			# sender_thread.start()
			# sender_thread.join()
			send_task_to_worker(t,j.job_id)
		# lock.release()
	request.close()


def listen_updates():
	#opening this will make port 5001 active and recieve updates from worker.py
	update = socket(AF_INET, SOCK_STREAM) #init a TCP socket
	update.bind(('', 5001))
	update.listen(3)
	print("Master ready to recieve task updates from worker.py")

	while True:
		worker_id=None
		connectionSocket, addr = update.accept()
		message = connectionSocket.recv(2048) # recieve max of 2048 bytes
		mssg = json.loads(message)
		# lock.acquire()

		# taking in the necessary values inorder to increase the slot count and to check if a job has finished executing.
		print("\n\n")
		print(mssg)
		task_id = mssg['task_id']
		worker_id = mssg['worker_id']
		done_flag = mssg['done']
		arrival_time = mssg['arrival_time']
		end_time = mssg['end_time']

		if done_flag == False:
			if '_M' in task_id:
				print("\nMap task with taskid ", task_id, " has failed.",end = '\n')
			else:
				print("\nReduce task with taskid ", task_id, " has failed.",end = '\n')
			return

		job_id = task_id.split('_')[0]

		if '_M' in task_id: # The task that got completed is a map task

			for job in jobs:
				if(job.job_id == job_id): # Finding the parent job of the map task
					for m_task in job.map_tasks:
						if m_task.task_id == task_id:
							# lock.acquire()
							m_task.done = True # Updating the map task's done is True
							m_task.arrival_time = arrival_time
							m_task.end_time = end_time
							job.map_tasks_done += 1 # Incrementing the number of map tasks completed for that particular job
							logger(mssg, 'tasks')
							# lock.release()
							break

					#this is to send reduce tasks if all map tasks wer completed
					if((job.map_tasks_done == len(job.map_tasks)) and (job.job_done == False)):
						# send_task_to_worker(t, j.job_id)
						for t in job.reduce_tasks:
							# sender_thread1 = threading.Thread(target=send_task_to_worker,args=(t,job.job_id,))
							# sender_thread1.start()
							# sender_thread1.join()
							send_task_to_worker(t,job.job_id)
			for worker in workers:
				if worker.id == worker_id:
					worker.mutex.acquire()
					# Since the task got completed, the slot that was occupied with this task will be free now.
					print("\nRecieved Task update from worker....")
					# if worker.occupied_slots!=0:
					worker.occupied_slots -= 1
					worker.print()
					worker.mutex.release()
			# jobs[int(job_id)].print() #added this to check i real task.done is getting updated

		else:
			for job in jobs:
				if(job.job_id == job_id): # Finding the parent job of the reduce task
					for r_task in job.reduce_tasks:
						if r_task.task_id == task_id:
							# lock.acquire()
							r_task.done = True #  Checking if the reduce task's done is True
							r_task.arrival_time = arrival_time
							r_task.end_time = end_time
							job.reduce_tasks_done += 1 # Incrementing the number of reduce tasks completed for that particular job
							logger(mssg, 'tasks')
							if( (len(job.map_tasks) == job.map_tasks_done) and (len(job.reduce_tasks) == job.reduce_tasks_done)): # To check if the entire job is done
								job.job_done = True # Updating the job's done to True
								#job.end_time = datetime.fromtimestamp(r_task.end_time)
								job.end_time = r_task.end_time
								temp = job.to_json()
								logger(temp,'jobs')
								print('Job ', job_id, ' was processed successfully', end = '\n')
								print("Arrival: {0}    End: {1}".format(job.arrival_time, job.end_time))
							# lock.release()
							for worker in workers:
								if worker.id == worker_id:
									worker.mutex.acquire()
									# Since the task got completed, the slot that was occupied with this task will be free now.
									print("\nRecieved Task update from worker....")
									# if worker.occupied_slots!=0:
									worker.occupied_slots -= 1
									worker.print()
									worker.mutex.release()
							break

			# jobs[int(job_id)].print()
		# if worker_id:
		# 	for worker in workers:
		# 		if worker.id == worker_id:
		# 			worker.mutex.acquire()
		# 			# Since the task got completed, the slot that was occupied with this task will be free now.
		# 			print("\nRecieved Task update from worker....")
		# 			# if worker.occupied_slots!=0:
		# 			worker.occupied_slots -= 1
		# 			worker.print()
		# 			worker.mutex.release()
		# # lock.release()
	update.close()
'''
done
'''

'''
running master
'''

listening_requests = threading.Thread(target = listen_to_requests)
listening_worker = threading.Thread(target = listen_updates)

listening_requests.start()
# time.sleep(5)
listening_worker.start()
'''
t1.join()
t2.join()
listen_to_requests()
send_task_to_worker()
listen_updates()
'''
num_jobs = len(jobs)
for i in range(num_jobs):
	print('---------------------------------')
	jobs[i].print()

time.sleep(10)
