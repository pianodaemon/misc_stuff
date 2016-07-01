#!/bin/sh

set -x
set -v

PF=`which iptables`
PUB_NIC_0=eth0
PUB_IP_0="`ifconfig $PUB_NIC_0 | awk -F: '/inet /{print $2}' | awk '{print $1}'`"


set_non_builtin_chains () {
    $PF -N CATCH_FORBIDDEN_CONN
    $PF -A CATCH_FORBIDDEN_CONN -j LOG --log-prefix 'PF_CATCH_FORBIDDEN_CONN ' --log-level 4 
    $PF -A CATCH_FORBIDDEN_CONN -j DROP

    $PF -N CATCH_FAKE_PACKET
    $PF -A CATCH_FAKE_PACKET -j LOG --log-prefix 'PF_CATCH_FAKE_PACKET ' --log-level 4
    $PF -A CATCH_FAKE_CONN -j DROP

    $PF -N CATCH_DOS_ATTACK
    $PF -A CATCH_DOS_ATTACK -j LOG --log-prefix 'PF_CATCH_DOS_ATTACK ' --log-level 4
    $PF -A CATCH_DOS_ATTACK -j DROP
}

reset_pf () {
    #Flushes all the chains in filter table
    $PF -F

    #Deletes every non-builtin chain in filter table
    $PF -X

    #Zero  the  packet  and  byte counters in all chains
    $PF -Z
}


set_default_policies () {
    $PF -P INPUT DROP 
    $PF -P OUTPUT DROP
    $PF -P FORWARD DROP

    #Everything is allowed for loopback interface
    $PF -A INPUT -i lo -j ACCEPT
    $PF -A OUTPUT -o lo -j ACCEPT
}


set_obscure_flags () {
    #Disable ping
    echo 1 > /proc/sys/net/ipv4/icmp_echo_ignore_all

    #Enable TCP SYN Cookie Protection
    echo 1 > /proc/sys/net/ipv4/tcp_syncookies

    #Disable kernel ip routing
    echo 0 > /proc/sys/net/ipv4/ip_forward

    # To not route packets which don't belong to your network
    for i in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 1 > $i;done    
}


set_common_nic_rules () {
    #To catch port scanner packets
    $PF -A INPUT -p tcp ! --syn -m state --state NEW -j CATCH_FAKE_PACKET

    #To avoid syn-flood
    $PF -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 4 -j CATCH_DOS_ATTACK
}

set_glassfish_rules () {
    OG_PORT=80

    #Limits the incoming connections from per minute
    #And sets a limit burst 
    $PF -A INPUT -i $PUB_NIC_0 -p tcp --dport $OG_PORT -m limit --limit 50/minute --limit-burst 100 -j ACCEPT

    #Allow incoming http/web traffic at OG_PORT
    $PF -A INPUT -p tcp -s 0/0 --sport 1024:65535 -d $PUB_IP_0 --dport $OG_PORT -m state --state NEW,ESTABLISHED -j ACCEPT

    $PF -A OUTPUT -p tcp -s $PUB_IP_0 --sport $OG_PORT -d 0/0 --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT
}

set_ssh_rules () {
    SSH_PORT=22

    #Limit the Number of Concurrent Connections per IP Address
    $PF -A INPUT -p tcp --syn --dport $SSH_PORT -m connlimit --connlimit-above 1 -j CATCH_FORBIDDEN_CONN

    #Allow incoming ssh  traffic at SSH_PORT
    $PF -A INPUT -p tcp -s 0/0 -d $PUB_IP_0 --sport 513:65535 --dport $SSH_PORT -m state --state NEW,ESTABLISHED -m recent --set -j ACCEPT
    $PF -A OUTPUT -p tcp -s $PUB_IP_0 -d 0/0 --sport $SSH_PORT --dport 513:65535 -m state --state ESTABLISHED -j ACCEPT 
}


set_resolver_rules () {
    $PF -A OUTPUT -p udp -o $PUB_NIC_0 --dport 53 -j ACCEPT
    $PF -A INPUT -p udp -i $PUB_NIC_0 --sport 53 -j ACCEPT
}

## -- MAXIMA FIREWALL --
## -- Created by The Enygma <j4nusx@yahoo.com>

reset_pf
set_non_builtin_chains
set_default_policies

set_obscure_flags
set_resolver_rules
set_ssh_rules
set_glassfish_rules

set_common_nic_rules
