#!/dgr/bin/bats

@test "gunicorn is a regular executable file" {
  [ -f "/usr/local/bin/gunicorn" ]
  [ -x "/usr/local/bin/gunicorn" ]
}

@test "gunicorn is a link executable file" {
  [ -s "/usr/bin/gunicorn" ]
  [ -x "/usr/bin/gunicorn" ]
}

@test "matchbox is a regular executable file" {
  [ -f "/usr/bin/matchbox" ]
  [ -x "/usr/bin/matchbox" ]
}

@test "validation is OK" {
    make -C /opt/enjoliver validate
  [ $? -eq 0 ]
}