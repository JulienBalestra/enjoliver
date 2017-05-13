#!/dgr/bin/bats

@test "kube-state-metrics is a regular executable file" {
  [ -x "/usr/bin/kube-state-metrics" ]
}
