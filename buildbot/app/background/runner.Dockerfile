FROM alpine:latest

WORKDIR /app

RUN apk add --no-cache bash coreutils busybox

RUN addgroup -S jobrunner && adduser -S jobrunner -G jobrunner

USER jobrunner

ENTRYPOINT ["bash", "-c"]
