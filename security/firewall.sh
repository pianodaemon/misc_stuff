#!/bin/sh
#

INTIF="eth0"
INTIP="192.168.1.1"
INTNET="192.168.1.0/24"
EXTIF="ppp0"
EXTIP="`ifconfig $EXTIF | awk -F: '/inet /{print $2}' | awk '{print
$1}'`"
UNIVERSE="0.0.0.0/0"
IPTABLES="/sbin/iptables"

for i in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 1 > $i;done
echo "1" > /proc/sys/net/ipv4/tcp_syncookies
echo "1" > /proc/sys/net/ipv4/ip_forward
echo "1" > /proc/sys/net/ipv4/ip_dynaddr

$IPTABLES -F
$IPTABLES -X
$IPTABLES -Z

$IPTABLES -P INPUT DROP
$IPTABLES -P OUTPUT DROP
$IPTABLES -P FORWARD DROP

$IPTABLES -N drop-and-log-it
$IPTABLES -A drop-and-log-it -j LOG --log-level info 
$IPTABLES -A drop-and-log-it -j REJECT

#######################################################################
# INPUT:
#
$IPTABLES -A INPUT -i lo -s $UNIVERSE -d $UNIVERSE -j ACCEPT
$IPTABLES -A INPUT -i $INTIF -s $INTNET -d $UNIVERSE -j ACCEPT
$IPTABLES -A INPUT -i $EXTIF -s $INTNET -d $UNIVERSE -j drop-and-log-it
$IPTABLES -A INPUT -i $EXTIF -p ICMP -s $UNIVERSE -d $EXTIP -j ACCEPT
$IPTABLES -A INPUT -i $EXTIF -s $UNIVERSE -d $EXTIP -m state --state ESTABLISHED,RELATED -j ACCEPT
$IPTABLES -A INPUT -s $UNIVERSE -d $UNIVERSE -j drop-and-log-it

#######################################################################
# OUTPUT:
#
$IPTABLES -A OUTPUT -o lo -s $UNIVERSE -d $UNIVERSE -j ACCEPT
$IPTABLES -A OUTPUT -o $INTIF -s $EXTIP -d $INTNET -j ACCEPT
$IPTABLES -A OUTPUT -o $INTIF -s $INTIP -d $INTNET -j ACCEPT
$IPTABLES -A OUTPUT -o $EXTIF -s $UNIVERSE -d $INTNET -j drop-and-log-it
$IPTABLES -A OUTPUT -o $EXTIF -s $EXTIP -d $UNIVERSE -j ACCEPT
$IPTABLES -A OUTPUT -s $UNIVERSE -d $UNIVERSE -j drop-and-log-it

#######################################################################
# FORWARD:
#
$IPTABLES -A FORWARD -i $EXTIF -o $INTIF -m state --state \
ESTABLISHED,RELATED -j ACCEPT
$IPTABLES -A FORWARD -i $INTIF -o $EXTIF -j ACCEPT
$IPTABLES -A FORWARD -j drop-and-log-it
$IPTABLES -t nat -A POSTROUTING -o $EXTIF -j SNAT --to $EXTIP

#######################################################################
