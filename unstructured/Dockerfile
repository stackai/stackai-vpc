FROM downloads.unstructured.io/unstructured-io/unstructured-api:0.0.80

# Switch to root to install packages
USER root

# Install GNU Coreutils (which includes GNU timeout) using apk
RUN apk update && apk add coreutils

USER 1000
