#!/bin/sh

if [ -z "${SONAR_PROJECT_KEY}" ]; then
  echo "Undefined \"projectKey\"" && exit 1
else
  COMMAND="sonar-scanner -Dsonar.sourceEncoding=UTF-8 -Dsonar.sources=. -Dsonar.exclusions=\"zoe_api/web/static/**\" -Dsonar.host.url=\"$SONARQUBE_SERVER_URL\" -Dsonar.login=\"$SONARQUBE_USER\" -Dsonar.password=\"$SONARQUBE_PASSWORD\" -Dsonar.projectKey=\"${SONAR_PROJECT_KEY}\""

  if [ ! -z "${SONAR_PROJECT_VERSION}" ]; then
    COMMAND="$COMMAND -Dsonar.projectVersion=\"${SONAR_PROJECT_VERSION}\""
  fi

  if [ ! -z "${SONAR_PROJECT_NAME}" ]; then
    COMMAND="$COMMAND -Dsonar.projectName=\"${SONAR_PROJECT_NAME}\""
  fi
  if [ ! -z ${CI_BUILD_REF} ]; then
    COMMAND="$COMMAND -Dsonar.gitlab.commit_sha=\"${CI_BUILD_REF}\""
  fi
  if [ ! -z ${CI_BUILD_REF_NAME} ]; then
    COMMAND="$COMMAND -Dsonar.gitlab.ref_name=\"${CI_BUILD_REF_NAME}\""
  fi
  if [ ! -z ${SONAR_BRANCH} ]; then
    COMMAND="$COMMAND -Dsonar.branch=\"${SONAR_BRANCH}\""
  fi

  eval ${COMMAND}
fi
