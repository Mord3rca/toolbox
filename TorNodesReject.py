#!/usr/bin/env python3

#A python script to add all TOR Exit Nodes in iptables
#All exit nodes are listed here: https://check.torproject.org/exit-addresses

import os
import sys
import http.client

print("[+] Connection to check.torproject.org...")
conn = http.client.HTTPSConnection("check.torproject.org")
conn.request("GET", "/exit-addresses")

r1 = conn.getresponse()
if(r1.status != 200):
	print("[-] Can't connect to check.torproject.org", file=sys.stderr)
	print("\tHTTP Error code: %i" % r1.status, file=sys.stderr)
	sys.exit()

print("[+] Reading Exit Nodes IPs...")
ips = []
while not r1.closed:
	line, splitted = [r1.readline(), []]
	if(line==b''):
		r1.close()
	else:
		splitted = line.strip().split()
		if( splitted[0] == b'ExitAddress' ):
			ips.append(str(splitted[1])[2:-1])

#This need to be root...
print("[+] Adding %i IPs to reject rule..." % len(ips))

if(os.getuid() != 0):
	print("[-] Not enough privilege: You must be root.", file=sys.stderr)
	sys.exit()

#CleanUp existing chain
os.system("iptables -D INPUT -j torExitNodes 2> /dev/null") #Removing from INPUT rules
os.system("iptables -F torExitNodes 2> /dev/null") #Flushing IPs in chain
os.system("iptables -X torExitNodes 2> /dev/null") #Deleting chain

#Setup a group for Nodes.
os.system("iptables -N torExitNodes") # (Re)Creating Nodes chain
for i in ips:
	os.system("iptables -A torExitNodes -p tcp -s %s -j DROP" % i) #Adding IPs
#Register chain into INPUT table
os.system("iptables -A INPUT -j torExitNodes")

print("[+] Script terminated successfully.")
sys.exit()

