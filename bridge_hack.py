#!/usr/bin/python3

from shelly import run, sudo

def main():
    # for n in range(40, 45):
    #     sudo('ip addr add 192.168.1.{} dev eth1'.format(n))
    #
    # run('ip addr')

    sudo('lxd init')
    run('lxc launch ubuntu:14.04 my-ubuntu')
    sudo('ip route add 192.168.1.42 dev lxdbr0  scope link metric 1')
    sudo('sudo ip route add 192.168.1.0/24 dev eth1 metric 99')
    sudo('ip route del 192.168.1.42 dev lxdbr0  scope link')

    # Now for iptables because local routes seem to always win:
    # ubuntu@kaylee:~/jujuWand$ ip route
    # default via 192.168.1.1 dev eth1 onlink
    # 10.224.48.0/24 dev lxdbr0  proto kernel  scope link  src 10.224.48.1
    # 192.168.1.0/24 dev eth1  scope link  metric 99
    # 192.168.1.42 dev lxdbr0  scope link  metric 1

    # ip route show to exact 192.168.1.42
    # 192.168.1.42 dev lxdbr0  scope link  metric 1

    # Looking good, but...
    # ip route get 192.168.1.42
    # local 192.168.1.42 dev lo  src 192.168.1.42
    # cache <local>

    # Nooo!

    # nc -l -p 5242 -v on the host machine picks up messages on 192.168.1.42
    # dooferlad@homework2 ~ $ watch 'echo "hello" | nc 192.168.1.42 5242'

    # So, looks like we need a specific rule to forward dst 192.168.1.42 to the container


if __name__ == '__main__':
    main()
