# The patched base. Challenge 02's scan-patched job builds this and must stay
# GREEN at --severity CRITICAL,HIGH.
FROM python:3.13-alpine

WORKDIR /app
COPY main.py .

# Pick up Alpine security fixes published after the base image was built.
#
# The python:3.13-alpine tag is rebuilt on Python releases, not on every Alpine
# advisory, so its OS layer drifts. In September 2026 it shipped libuuid
# 2.42.1-r0 with seven HIGH CVEs (CVE-2026-53612 and friends) while 2.42.3-r0 was
# already in the Alpine repo — and scan-patched went red with nothing in this
# lab having changed. A "clean" base image is clean on the day you checked it.
RUN apk upgrade --no-cache

# Ship the app, not the toolchain.
#
# Even with the OS layer upgraded, pip vendors its own copies of
# msgpack 1.1.2 and setuptools 70.3.0 — both carrying HIGH CVEs
# (GHSA-6v7p-g79w-8964, CVE-2025-47273). You cannot `pip install --upgrade` your
# way out of that: the vulnerable code is inside pip/_vendor/, not site-packages.
#
# This app is standard library only, so pip has no business being in the runtime
# image at all. Removing it takes the image to 0 CRITICAL, 0 HIGH.
RUN rm -rf /usr/local/lib/python3.13/site-packages/pip \
           /usr/local/lib/python3.13/site-packages/pip-*.dist-info \
           /usr/local/lib/python3.13/ensurepip \
           /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.13

# Do not run as root. Trivy will not catch this; a container-hardening reviewer will.
RUN adduser -D -u 10001 phr
USER phr

ENV PORT=8080
EXPOSE 8080

CMD ["python", "main.py"]
