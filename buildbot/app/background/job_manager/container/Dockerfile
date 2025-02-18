FROM alpine:latest

ARG WORKDIR="/job"
ARG SCRIPT_PATH=${WORKDIR}/run.sh

RUN apk add --no-cache bash coreutils busybox

WORKDIR ${WORKDIR}

RUN addgroup -S runners && adduser -S jobrunner -G runners

RUN mkdir -p ${WORKDIR} && chown jobrunner:runners ${WORKDIR}

USER jobrunner

RUN touch ${SCRIPT_PATH} && chmod +x ${SCRIPT_PATH}

ENTRYPOINT ["bash", "-c"]