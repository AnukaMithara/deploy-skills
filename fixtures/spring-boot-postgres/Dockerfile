# syntax=docker/dockerfile:1

FROM maven:3.9.11-eclipse-temurin-21-alpine AS development
WORKDIR /app
ENV HOME=/home/app \
    MAVEN_CONFIG=/home/app/.m2
RUN addgroup -S -g 10001 app \
    && adduser -S -D -u 10001 -G app -h /home/app app \
    && mkdir -p /home/app/.m2 \
    && chown -R app:app /app /home/app
COPY --chown=app:app pom.xml ./
COPY --chown=app:app src ./src
USER app
RUN mvn -B -ntp -DskipTests package
CMD ["mvn", "-B", "-ntp", "spring-boot:run"]

FROM development AS builder
RUN cp target/deploy-skills-spring-fixture-0.1.0.jar /app/app.jar

FROM eclipse-temurin:21-jre-alpine AS runtime
WORKDIR /app
# hadolint ignore=DL3017,DL3018
RUN apk upgrade --no-cache \
    && apk add --no-cache curl \
    && addgroup -S -g 10001 app \
    && adduser -S -D -u 10001 -G app -h /home/app app
COPY --from=builder --chown=app:app /app/app.jar ./app.jar
USER 10001:10001
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
