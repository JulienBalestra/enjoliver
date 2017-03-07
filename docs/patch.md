# Patchs


Some quick features are breaking changes for the Kubernetes project so Enjoliver store patches and apply them at the compilation time.

**To create a patch:**

    git checkout -b v1.5.3
    git reset HEAD~
    git add pkg/kubelet/rkt/rkt.go
    git commit -m "SomeCommitMessage"
    git format-patch HEAD^ --stdout > ~/enjoliver/aci/aci-hyperkube/patches/XXX.patch