pipeline {
    agent any

    environment {
        IMAGE_NAME = "shaunak30/myapp"
        CONTAINER_NAME = "myapp-container"
    }

    stages {

        stage('Pull Image from Docker Hub') {
            steps {
                sh 'docker pull $IMAGE_NAME'
            }
        }

        stage('Stop Old Container') {
            steps {
                sh '''
                docker stop $CONTAINER_NAME || true
                docker rm $CONTAINER_NAME || true
                '''
            }
        }

        stage('Run New Container') {
            steps {
                sh '''
                docker run -d --restart always -p 8000:8000 --name $CONTAINER_NAME $IMAGE_NAME
                '''
            }
        }
    }
}
