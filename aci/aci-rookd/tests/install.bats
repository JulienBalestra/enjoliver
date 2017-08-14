#!/dgr/bin/bats
NAME=${AC_APP_NAME#aci-*}
@test "$NAME  is here" {
  [ -d "/opt/bin" ]
  [ -f "/opt/bin/$NAME" ]
}