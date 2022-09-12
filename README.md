# peerOptimizer
Filter Peers By Latency and Stake

peerOptimizer allows a Cardano Stake pool operator to generate a custom topology.json file optimising for latency and stake. The create_relay_list() routine in peerOptimise.py has 3 variables which you can configure to generate your desired pool list:

rttconfig = 750
stakeconfig =    100000000000000
stakeconfigmin = 20000000000000

The defaults are 750ms rtt and stake between 20M and 100M ADA default units in lovelace. 

First run poolListGenerator.py to generate the current list of stakepools. This will create a pooldetails.json file. Then you can run peerOptimise which will parse and perform checks on to ensure the pool meets your configured thresholds. 

 ./peer_optimise.py -h                                                                                             
usage: peer_optimise.py [-h] [--peersfile PEERSFILE] [--rtt | --stake | --random] [--cncli]

optional arguments:
  -h, --help            show this help message and exit
  --peersfile PEERSFILE, -f PEERSFILE
                        Static peers file
  --rtt, -t             Sort by round trip time
  --stake, -s           Sort by stake
  --random, -r          Want to try a randomly sorted topology
  --cncli, -c           Add cncli check, default is socket check
  
 
If you want to propogate transactions quickly to the network the pools which you connect to can be important.

The concept and original two scripts for this tool were conceived and written by STLL pool. COINZ pool contributed to the final version of these scripts by taking the original rough version and refactoring them into more pythonic function driven routines.

