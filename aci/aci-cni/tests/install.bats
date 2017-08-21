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
  [ -x /usr/bin/noop ]
  [ -x /usr/bin/ptp ]
  [ -x /usr/bin/tuning ]
}

@test "cni starts" {
  run /usr/bin/bridge
  [ "$status" -eq 1 ]

  run /usr/bin/cnitool
  [ "$status" -eq 1 ]

  run /usr/bin/dhcp
  [ "$status" -eq 1 ]

  run /usr/bin/flannel
  [ "$status" -eq 1 ]

  run /usr/bin/host-local
  [ "$status" -eq 1 ]

  run /usr/bin/ipvlan
  [ "$status" -eq 1 ]

  run /usr/bin/loopback
  [ "$status" -eq 1 ]

  run /usr/bin/macvlan
  [ "$status" -eq 1 ]

  run /usr/bin/ptp
  [ "$status" -eq 1 ]

  run /usr/bin/tuning
  [ "$status" -eq 1 ]

  # /usr/bin/noop is a daemon
}
