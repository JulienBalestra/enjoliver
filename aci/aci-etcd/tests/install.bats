#!/dgr/bin/bats

@test "etcd is well installed" {
  [ -x /usr/bin/etcdctl ]
  [ -x /usr/bin/etcd ]
}

