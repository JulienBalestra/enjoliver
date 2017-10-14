#!/dgr/bin/bats

@test "rkt is well installed" {
  [ -x /usr/bin/rkt ]
  [ -f /usr/lib/rkt/stage1-images/stage1-fly.aci ]
  [ -f /usr/lib/rkt/stage1-images/stage1-src.aci ]
}


@test "run" {
  run /usr/bin/rkt -h
  [ "$status" -eq 0 ]
}
