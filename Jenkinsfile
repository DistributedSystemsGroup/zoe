#!groovy

node('docker-trusty') {
    stage('Cleanup') {
        step([$class: 'WsCleanup'])
    }

    stage('Checkout') {
        checkout scm
        sshagent(['67aa0a6c-64d5-40bd-ae9f-4ff66de97411']) {
            sh "git checkout ${BRANCH_NAME}"
        }
    }

    stage('Install prerequisites') {
        sh "virtualenv venv"
        sh """
        . venv/bin/activate
        pip install -r requirements.txt
        """

        sh """
        . venv/bin/activate
        pip install -r requirements_tests.txt
        """
    }

    stage('Test') {
        try {
            sh """
            . venv/bin/activate
            bash ./run_tests.sh
            """
            currentBuild.result = 'SUCCESS'
        } catch (Exception err) {
            currentBuild.result = 'FAILURE'
        }
    }

    stage('Push') {
        try {
            if (currentBuild.result == 'SUCCESS') {
                echo "Test successful, pushing to github"
                sshagent(['67aa0a6c-64d5-40bd-ae9f-4ff66de97411']) {
                    sh "git remote add github git@github.com:DistributedSystemsGroup/zoe.git"
                    sh "git branch -a"
                    sh "git push github HEAD"
                    sh "git push github --tags"
                }
            } else {
                echo "Build failed, no push"
            }
        } catch (Exception err) {
            currentBuild.result = 'FAILURE'
            }
    }

    stage('Notification and cleanup') {
        echo "Sending notifications"
        step([$class: 'Mailer', notifyEveryUnstableBuild: true, recipients: 'daniele.venzano@eurecom.fr', sendToIndividuals: true])
        step([$class: 'GitHubCommitStatusSetter', errorHandlers: [[$class: 'ChangingBuildStatusErrorHandler', result: 'FAILURE']], reposSource: [$class: 'ManuallyEnteredRepositorySource', url: 'https://github.com/DistributedSystemsGroup/zoe.git']])
    }
}
