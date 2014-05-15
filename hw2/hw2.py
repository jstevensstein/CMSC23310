import sys

NEXT_PROP = None
PROPOSERS = None
ACCEPTORS = None
N = None
T_OUTPUT = None
T = None
QORUM = None

class Computer:
	def __init__(self, ID):
		self.ID = ID
		self.failed = False

class Proposer(Computer):
	def __init__(self, ID):
		Computer.__init__(self, ID)
		self.prop_num = None
		self.prop_val = None
		self.n_promise = None
		self.n_rejected = None
		self.n_accepted = None
		self.first_prop_val = None
		self.greatest_promise_prior_prop_n = None #the greatest prop number returned in a promise
		self.greatest_promise_prior_prop_n_val = None #the corresponding value
	def newProposal(self, prop_val):
		global NEXT_PROP
		global ACCEPTORS
		self.greatest_promise_prior_prop_n = self.prop_num 
		self.prop_num = NEXT_PROP
		NEXT_PROP += 1
		if (self.first_prop_val == None):
			self.first_prop_val = prop_val
		self.prop_val = prop_val
		self.n_promise = 0
		self.n_rejected = 0
		self.n_accepted = 0
		for a in ACCEPTORS.values():
			new_m = Message(self, a, "PREPARE", None, self.prop_num, None)
			N.queueMessage(new_m)
	def processMessage(self, m):
		global N
		global QORUM
		global ACCEPTORS
		if (m.typ_str == "PROPOSE"):
			self.newProposal(m.val)
		elif (m.typ_str == "PROMISE" and m.prop_num == self.prop_num):
			self.n_promise += 1
			if (m.prior[0] != None and m.prior[0] > self.greatest_promise_prior_prop_n):
				self.greatest_promise_prior_prop_n = m.prior[0]
				self.greatest_promise_prior_prop_n_val = m.prior[1]
			if (self.n_promise == QORUM):
				if (self.greatest_promise_prior_prop_n_val != None):
					self.prop_val = self.greatest_promise_prior_prop_n_val
				for a in ACCEPTORS.values():
					new_m = Message(self, a, "ACCEPT", self.prop_val, self.prop_num, None)
					N.queueMessage(new_m)
		elif (m.typ_str == "REJECTED" and m.prop_num == self.prop_num):
			self.n_rejected += 1
			if (self.n_rejected == QORUM): #ERROR IN SPEC, WILL NOT WORK IN BORDER CASE OF EVEN NUMBER OF ACCEPTORS 
			#AND EXACTLY HALF REJECTING/ACCEPTING
				self.newProposal(self.prop_val)
		elif (m.typ_str == "ACCEPTED" and m.prop_num == self.prop_num):
			self.n_accepted += 1
		return

class Acceptor(Computer):
	def __init__(self, ID):
		Computer.__init__(self, ID)
		self.ID = ID
		self.greatest_prep_prop_num = 0
		self.accepted_prop_num = None
		self.val = None
		self.rejected_props = []
	def processMessage(self, m):
		global N
		if (m.typ_str == "PREPARE"):
			if (m.prop_num > self.greatest_prep_prop_num):
				new_m = Message(self, m.src, "PROMISE", None, m.prop_num, [self.accepted_prop_num, self.val])
				self.greatest_prep_prop_num = m.prop_num
				N.queueMessage(new_m)
			else:
				self.rejected_props.append(m.prop_num)
				new_m = Message(self, m.src, "REJECTED", None, m.prop_num, None)
				N.queueMessage(new_m)
		elif (m.typ_str == "ACCEPT"):
			if (m.prop_num == self.greatest_prep_prop_num):
				self.accepted_prop_num = m.prop_num
				self.val = m.val
				new_m = Message(self, m.src, "ACCEPTED", self.val, m.prop_num, None)
				N.queueMessage(new_m)
			elif (m.prop_num < self.greatest_prep_prop_num and m.prop_num not in self.rejected_props): #so that prop not rejected twice
				self.rejected_props.append(m.prop_num)
				new_m = Message(self, m.src, "REJECTED", None, m.prop_num, None)
				N.queueMessage(new_m)
		return



class Message:
	def __init__(self, src, dst, typ_str, val, prop_num, prior):
		self.src = src
		self.dst = dst
		self.typ_str = typ_str
		self.val = val
		self.prop_num = prop_num
		self.prior = prior #a list of two elts, the prior prop n and the corresponding value

class Network:
	def __init__(self):
		self.queue = []
	def queueMessage(self, m):
		self.queue.append(m)
	def extractMessage(self):
		n = len(self.queue)
		for i in range(0, n):
			m = self.queue[i]
			if (m.src.failed == False and m.dst.failed == False):
				return self.queue.pop(i)
		return None
	def deliverMessage(self, dst, m):
		global T_OUTPUT
		global T
		#code for producing output
		if (m.typ_str == "PROPOSE"):
			temp = (str(T) + ":").rjust(4) + ("  " + " -> P" + str(m.dst.ID)).rjust(9) + ("  PROPOSE v=" + str(m.val))
			T_OUTPUT.append(temp)
		elif (m.typ_str == "PREPARE"):
			temp = (str(T) + ":").rjust(4) + ("P" + str(m.src.ID) + " -> A" + str(m.dst.ID)).rjust(9) + ("  PREPARE n=" + str(m.prop_num))
			T_OUTPUT.append(temp)
		elif (m.typ_str == "REJECTED"):
			temp = (str(T) + ":").rjust(4) + ("A" + str(m.src.ID) + " -> P" + str(m.dst.ID)).rjust(9) + ("  REJECTED n=" + str(m.prop_num))
			T_OUTPUT.append(temp)
		elif (m.typ_str == "PROMISE"):
			temp2= " (Prior: "
			if m.prior[0] != None:
				temp2 += "n=" + str(m.prior[0]) +", v=" + str(m.prior[1]) + ")"
			else: temp2 += "None)"
			temp = (str(T) + ":").rjust(4) + ("A" + str(m.src.ID) + " -> P" + str(m.dst.ID)).rjust(9) + ("  PROMISE n=" + str(m.prop_num) + temp2)
			T_OUTPUT.append(temp)
		elif (m.typ_str == "ACCEPT"):
			temp = (str(T) + ":").rjust(4) + ("P" + str(m.src.ID) + " -> A" + str(m.dst.ID)).rjust(9) + ("  ACCEPT n=" + str(m.prop_num) + " v=" + str(m.val))
			T_OUTPUT.append(temp)
		elif (m.typ_str == "ACCEPTED"):
			temp = (str(T) + ":").rjust(4) + ("A" + str(m.src.ID) + " -> P" + str(m.dst.ID)).rjust(9) + ("  ACCEPTED n=" + str(m.prop_num) + " v=" + str(m.val))
			T_OUTPUT.append(temp)
		#delivers message and hands control to src object
		dst.processMessage(m)



class Simulation:
	def __init__(self, np, na, t_max, E):
		self.np = np
		self.na = na
		self.t_max = t_max
		self.E = E

class Event:
	def __init__(self, t):
		self.t = t
		self.F = {"P":[], "A":[]}
		self.R = {"P":[], "A":[]}
		self.p = None
		self.v = None


def parseInput(sim_input):
	temp = sim_input[0].split()
	np = int(temp[0])
	na = int(temp[1])
	t_max = int(temp[2])
	Events = parseInputEvents(sim_input[1:])
	return Simulation(np, na, t_max, Events)


def parseInputEvents(events_input):
	E = {}
	for line in events_input:
		temp = line.split()
		t = int(temp[0])
		if not E.has_key(t):
			E[t] = Event(t)
		if temp[1] == "PROPOSE":
			E[t].p = int(temp[2])
			E[t].v = int(temp[3])
		elif temp[1] == "FAIL":
			if temp[2] == "PROPOSER":
				E[t].F["P"].append(int(temp[3]))
			elif temp[2] == "ACCEPTOR":
				E[t].F["A"].append(int(temp[3]))
		elif temp[1] == "RECOVER":
			if temp[2] == "PROPOSER":
				E[t].R["P"].append(int(temp[3]))
			elif temp[2] == "ACCEPTOR":
				E[t].R["A"].append(int(temp[3]))
	return E

def Simulate(sim):
	#setup
	global NEXT_PROP
	NEXT_PROP = 1
	global PROPOSERS
	PROPOSERS = {}
	global ACCEPTORS
	ACCEPTORS = {}
	for i in range(1, sim.np + 1):
		PROPOSERS[i] = Proposer(i)
	for i in range(1, sim.na + 1):
		ACCEPTORS[i] = Acceptor(i)
	global N
	N = Network()
	global T_OUTPUT
	T_OUTPUT = []
	global T
	T = 0
	global QORUM
	QORUM = sim.na/2 + 1
	E = sim.E
	t_max = sim.t_max
	while (T <= t_max):
		if (N.queue == [] and sim.E.items() == []):
			break
		if E.has_key(T):
			e = E.pop(T)
			#process e
			for n in e.F['P']:
				PROPOSERS[n].failed = True
				temp = (str(T) + ":").rjust(4) + " ** P" + str(n) + " FAILS **"
				T_OUTPUT.append (temp)
			for n in e.F['A']:
				ACCEPTORS[n].failed = True
				temp = (str(T) + ":").rjust(4) + " ** A" + str(n) + " FAILS **"
				T_OUTPUT.append (temp)
			for n in e.R['P']:
				PROPOSERS[n].failed = False
				temp = (str(T) + ":").rjust(4) + " ** P" + str(n) + " RECOVERS **"
				T_OUTPUT.append (temp)
			for n in e.R['A']:
				ACCEPTORS[n].failed = False
				temp = (str(T) + ":").rjust(4) + " ** A" + str(n) + " RECOVERS **"
				T_OUTPUT.append (temp)
			if (e.p != None and e.v != None):
				m = Message(None, PROPOSERS[e.p], "PROPOSE", e.v, None, None)
				N.deliverMessage(m.dst, m)
			else:
				m = N.extractMessage()
				if m != None:
					N.deliverMessage(m.dst, m)
		else:
			m = N.extractMessage()
			if m != None:
				N.deliverMessage(m.dst, m)
		#not part of sim, just printing output
		if (T_OUTPUT == []):
			T_OUTPUT.append((str(T) + ":").rjust(4))
		for line in T_OUTPUT:
			print line
		T_OUTPUT = []
		T += 1
	print('\n')
	for p in PROPOSERS.values():
		if (p.n_accepted < QORUM):
			print("P" + str(p.ID) + " did not reach consensus")
		else:
			print("P" + str(p.ID) + " has reached consensus (proposed " + str(p.first_prop_val) + 
				", accepted " + str(p.prop_val) + ")")
	return

def main():
	sim_input = []
	while ((True)):
		line = sys.stdin.readline().strip('\r\n')
		if (line == "0 END"):
			break
		else:
			sim_input.append(line)
	#parse lines into sim structure
	#run simulation
	sim = parseInput(sim_input)
	Simulate(sim)
	return

main()