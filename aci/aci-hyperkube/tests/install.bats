#!/dgr/bin/bats

@test "hyperkube is a regular executable file" {
  [ -f "/hyperkube" ]
  [ -x "/hyperkube" ]
}

@test "kubernetes componants are symlinked" {
  [ -L "/apiserver" ]
  [ -L "/controller-manager" ]
  [ -L "/kubectl" ]
  [ -L "/kubelet" ]
  [ -L "/proxy" ]
  [ -L "/scheduler" ]
}

@test "hyperkube is able to run" {
  ./hyperkube --version
  [ $? -eq 0 ]
}
