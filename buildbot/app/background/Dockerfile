FROM alpine:latest

ARG RUNNER_USER="jobrunner"
ARG RUNNER_GROUP="jobrunner"
ARG WORKDIR="/app"


WORKDIR ${WORKDIR}

RUN apk add --no-cache bash coreutils busybox
RUN addgroup -S ${RUNNER_GROUP} && adduser -S ${RUNNER_USER} -G ${RUNNER_USER}
RUN mkdir -p ${WORKDIR} && chown ${RUNNER_USER}:${RUNNER_GROUP} ${WORKDIR}

USER ${RUNNER_USER}

ENTRYPOINT ["bash", "-c"]
