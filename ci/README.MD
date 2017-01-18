# Zoe Continuous Integration
----------------------------
# Overview
- Integrated Zoe repository to Jenkins and SonarQube
- Each commit to Zoe repository trigger a build at Jenkins:
  - Run SonarQube Scanner to analyze the codebase
  - Create two containers for zoe-master, zoe-api
  - Run integration test [testing rest api]
  - Build new images if no errors happen
  - Deploy Zoe with latest images

# Software Stack
- Jenkins - version 2.7.4
- SonarQube - version 9.6.0

# Configuration
### Jenkins
  - Required:
    - Plugins: Github plugin, SonarQube Plugin, Email Plugin (optional)
    - Softwares: Java, Python, Docker
      - Go to Manage Jenkins, then  Global Tool Configuration to setup Java SDK
  - SonarQube server configuration:
      - Go to Manage Jenkins then Configure System
      - SonarQube servers: input name, server URL, server version, **sever authentication token** (created on SonarQube Server)
- Create credentials for Github account
  - Create SSH key pair on Jenkins Server
    - Add public key to Github
    - Add private key to Jenkins credentials
- Create new item as a **freestyle project** to descibe Github repository
  - General
    - Select Github project
    - Insert project URL
  - Source Code Management
    - Select **Git**
    - Repositories
      - Repository URL: use **SSH URL** of github repository
      - Credentials: select the one created above
  - Build Triggers
      - Select **Build when a change is pushed to Github**
  - Post-build Actions [Optional]
     - Add **E-mail Notification** for notifying when jobs finish
### Github
- Add new SSH key (the one created on Jenkins server)
- Go to the project (which is integrated to Jenkins) settings
  - Integration & Services
    - Add Service, choose **Jenkins (Github plugin)**
    - Add Jenkins hook url
      - For github plugin, this one would have the format: http://your-jenkins.com/github-webhook/
      - In case your Jenkins doens't expose to the world, try **ngrok**
### SonarQube
- On **Administration**, go to **My Account**, then **Security**
- Generate Tokens, copy this and paste to **server authentication token** on Jenkins configuration
- The project needs to provides **sonar-properties** file in the repo: http://docs.sonarqube.org/display/SCAN/Analyzing+with+SonarQube+Scanner

# Execute Shell Script
Script to execute ci in zoe-kpmg branch i34-t7.4.1
Push this script inside the **execute shell script** of Jenkins job
```
# Build new container images
python3 ci/zoeci.py 1 tcp://192.168.12.2:2375 192.168.12.2:5000/zoe:$BUILD_ID
# Deploy new zoe with the above images for testing
python3 ci/zoeci.py 0 tcp://192.168.12.2:2375 ci/docker-compose-test.yml 192.168.12.2:5000/zoe:$BUILD_ID

# Run integration test
cd tests
coverage run -p basic_auth_success_test.py
coverage run -p cookie_auth_success_test.py
coverage combine
coverage xml
cd ..

# Rebuild new frontend
cd zoe_fe
ng build --env=prod --output-path=build/prod/
cd ..
cp -r zoe_fe/build/prod .
tar -cvf prod.tar prod

# Push the built images above to local registry
python3 ci/zoeci.py 2 tcp://192.168.12.2:2375 192.168.12.2:5000/zoe:$BUILD_ID
# Redeploy zoe with new images
python3 ci/zoeci.py 0 tcp://192.168.12.2:2375 ci/docker-compose-prod.yml 192.168.12.2:5000/zoe:$BUILD_ID
```
