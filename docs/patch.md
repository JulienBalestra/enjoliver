# Patchs


Some quick features are breaking changes for the Kubernetes project so Enjoliver store patches and apply them at the compilation time.

**To create a patch:**

    git checkout -b v1.5.1
    git add the/file
    git commit -m "This is needed for ..."
    git format-patch HEAD^ --stdout > enjoliver/hyperkube/workspace/patches/000X-My-New.patch