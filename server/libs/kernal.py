import resource
import os

def chkernal():
    resource.setrlimit(resource.RLIMIT_NOFILE,(1000000,1000000))

    os.system('sysctl -w net.ipv4.ip_local_port_range="1025 65535"')
    os.system('sysctl -w net.ipv4.tcp_rmem="4096 4096 16777216"')
    os.system('sysctl -w net.ipv4.tcp_wmem="4096 4096 16777216"')
    os.system('sysctl -w net.netfilter.nf_conntrack_max=250000') 
    #os.system('sysctl -p')
