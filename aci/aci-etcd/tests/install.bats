#!/dgr/bin/bats

@test "etcd is well installed" {
  [ -x /usr/bin/etcdctl ]
  [ -x /usr/bin/etcd ]
}

@test "run" {
  run /usr/bin/etcdctl --version
  [ "$status" -eq 0 ]

  run /usr/bin/etcd --version
  [ "$status" -eq 0 ]
}