# Patchs


Some quick features are breaking changes for the Kubernetes project so Enjoliver store patches and apply them at the compilation time.

**To create a patch:**

    git checkout -b v1.5.1
    git reset HEAD~
    git add pkg/kubelet/rkt/rkt.go
    git commit -m "Syslog"
    git format-patch HEAD^ --stdout > ~/IdeaProjects/enjoliver/hyperkube/workspace/patches/0002-Create-SyslogIdentifier-Systemd-Units.patch