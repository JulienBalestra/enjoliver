#!/dgr/bin/bats

@test "cni is well installed" {
  [ -x /usr/bin/bridge ]
  [ -x /usr/bin/cnitool ]
  [ -x /usr/bin/dhcp ]
  [ -x /usr/bin/flannel ]
  [ -x /usr/bin/host-local ]
  [ -x /usr/bin/ipvlan ]
  [ -x /usr/bin/loopback ]
  [ -x /usr/bin/macvlan ]
}

