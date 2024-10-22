# Unstructured

## Contents

This directory contains the Dockerfile used to build our slightly modified version of the Unstructured API. As of version `0.0.80`, the API is built using a RockyLinux base image, which does not include the gnu `timeout` command required by the unstructured startup script when `MAX_LIFETIME_SECONDS` is set.

To fix this, we need to install `coreutils` (which includes `timeout`) using the appropriate package manager for the base image.

The resulting image is then pushed to our private Docker registry.
