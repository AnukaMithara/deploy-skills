# Spring Boot images

- Select the Java version from the Maven or Gradle build and preserve the existing build tool and wrapper when present.
- Resolve dependencies in a builder stage and copy only the executable JAR plus documented runtime tools into the final image.
- Use a JRE runtime when the application does not require a JDK at runtime.
- Run the JAR with exec-form `java -jar` as a dedicated non-root user.
- Keep `spring-boot:run`, DevTools, Maven, Gradle, and source bind mounts in the development target only.
- Configure graceful shutdown and provide memory limits at the orchestrator level before inventing JVM heap flags.
- Keep Flyway or Liquibase migrations as an explicit one-shot deployment operation; disable automatic production migration in the long-running application unless repository evidence requires it.
- Health-check the application and required dependencies. Add a small health client to the runtime image only when the base does not already provide a reliable option.
