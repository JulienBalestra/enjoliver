#!/dgr/bin/bats

@test "haproxy is well installed" {
  [ -x /usr/sbin/haproxy ]
}

@test "run" {
  run /usr/sbin/haproxy -v
  [ "$status" -eq 0 ]
}