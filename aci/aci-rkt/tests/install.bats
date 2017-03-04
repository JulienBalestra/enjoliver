#!/dgr/bin/bats

@test "rkt is well installed" {
  [ -x /usr/bin/rkt ]
  [ -f /usr/lib/rkt/stage1-images/stage1-fly.aci ]
  [ -f /usr/lib/rkt/stage1-images/stage1-coreos.aci ]
  [ -f /usr/lib/rkt/stage1-images/stage1-kvm.aci ]
}

