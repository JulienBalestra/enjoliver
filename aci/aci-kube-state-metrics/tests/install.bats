#!/dgr/bin/bats

@test "kube-state-metrics is a regular executable file" {
  [ -x "/usr/bin/kube-state-metrics" ]
}


@test "run" {
  run /usr/bin/kube-state-metrics --version
  [ "$status" -eq 0 ]
}