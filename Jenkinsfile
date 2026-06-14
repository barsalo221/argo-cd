pipeline {
    agent {
        kubernetes {
            // הגדרת ה-Namespace שבו ירוץ הפוד הדינמי
            namespace 'devops-tools'
            yaml """
kind: Pod
metadata:
  name: car-app-builder
spec:
  serviceAccountName: jenkins
  containers:
  - name: jnlp
    image: jenkins/inbound-agent:latest
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command:
    - cat
    tty: true
    # הוספת הרשאות Root לקניקו כדי למנוע Permission denied בתוך התיקייה שלו
    securityContext:
      runAsUser: 0
      runAsGroup: 0
"""
        }
    }

    environment {
        DOCKER_USER = 'barsalo221'
        IMAGE_NAME = "${DOCKER_USER}/car-app"
        IMAGE_TAG = "v1.0.${BUILD_NUMBER}"
        VALUES_FILE_PATH = 'car-app-chart/values.yaml'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build & Push with Kaniko') {
            steps {
                withVault([configuration: [timeout: 60, vaultCredentialId: 'vault-k8s-auth', vaultUrl: 'http://vault.vault.svc.cluster.local:8200'], 
                           vaultSecrets: [[path: 'secret/jenkins/dockerhub', secretValues: [[envVar: 'DOCKER_PASS', vaultKey: 'password']]]]]) {
                    
                    script {
                        // הכל נעטף תחת קניקו, והמשתנים של ג'נקינס מוזרקים פנימה בעזרת מרכאות כפולות במקום גרש בודד
                        container('kaniko') {
                            sh """
                            mkdir -p /kaniko/.docker
                            echo "{\\"auths\\":{\\"https://index.docker.io/v1/\\":{\\"auth\\":\\"\$(echo -n ${DOCKER_USER}:${DOCKER_PASS} | base64)\\"}}}" > /kaniko/.docker/config.json
                            
                            /kaniko/executor --context=${WORKSPACE} --dockerfile=${WORKSPACE}/Dockerfile --destination=${IMAGE_NAME}:${IMAGE_TAG}
                            """
                        }
                    }
                }
            }
        }

        stage('Update & Push to Git') {
            steps {
                withVault([configuration: [timeout: 60, vaultCredentialId: 'vault-k8s-auth', vaultUrl: 'http://vault.vault.svc.cluster.local:8200'], 
                           vaultSecrets: [[path: 'secret/jenkins/github', secretValues: [[envVar: 'GIT_TOKEN', vaultKey: 'token']]]]]) {
                    
                    sh """
                    git config user.email "jenkins-bot@local"
                    git config user.name "Jenkins CI Bot"
                    sed -i 's/tag:.*/tag: "${IMAGE_TAG}"/g' ${VALUES_FILE_PATH}
                    git remote set-url origin https://x-access-token:${GIT_TOKEN}@github.com/${DOCKER_USER}/argo-cd.git
                    git add ${VALUES_FILE_PATH}
                    git commit -m "chore: update image tag to ${IMAGE_TAG}"
                    git push origin HEAD:main
                    """
                }
            }
        }
    }
}