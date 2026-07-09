pipeline {
    agent any

    environment {
        HELM_CHART = "helm/sample-nodejs"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Pylint') {
            steps {
                sh "python3 ci-scripts/pylint_check.py --path ci-scripts/"
            }
        }

        stage('Helm Lint') {
            steps {
                sh "helm lint ${HELM_CHART}"
            }
        }

        stage('Helm Dry Run') {
            steps {
                sh "helm template ${HELM_CHART} | kubectl apply --dry-run=client -f -"
            }
        }
    }

    post {
        failure {
            withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                sh '''
                    curl -s -X POST \
                      -H "Authorization: token ${GIT_TOKEN}" \
                      -H "Content-Type: application/json" \
                      -d '{"state":"failure","context":"Jenkins CI/Infra PR","description":"Infra checks failed — merge is blocked."}' \
                      "https://api.github.com/repos/AviAtia/devops-infra/statuses/${GIT_COMMIT}"
                '''
            }
        }
        success {
            withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                sh '''
                    curl -s -X POST \
                      -H "Authorization: token ${GIT_TOKEN}" \
                      -H "Content-Type: application/json" \
                      -d '{"state":"success","context":"Jenkins CI/Infra PR","description":"All checks passed — PR is ready to merge."}' \
                      "https://api.github.com/repos/AviAtia/devops-infra/statuses/${GIT_COMMIT}"
                '''
            }
        }
        always {
            cleanWs()
        }
    }
}
