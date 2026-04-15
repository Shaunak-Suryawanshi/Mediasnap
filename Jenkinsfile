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
                echo "Stopping existing container if running..."
                docker stop $CONTAINER_NAME || true
                docker rm $CONTAINER_NAME || true
                '''
            }
        }

        stage('Free Port 8000 (IMPORTANT FIX)') {
            steps {
                sh '''
                echo "Freeing port 8000 if occupied..."
                docker ps -q --filter "publish=8000" | xargs -r docker stop
                docker ps -aq --filter "publish=8000" | xargs -r docker rm
                '''
            }
        }

        stage('Run New Container with MongoDB Atlas') {
            steps {
                // Inject MongoDB URI securely from Jenkins Credentials
                withCredentials([string(credentialsId: 'mongo-uri', variable: 'MONGO_URI')]) {
                    sh '''
                    echo "Starting new container with MongoDB Atlas connection..."
                    docker run -d --restart always -p 8000:8000 \
                      -e MONGO_URI="$MONGO_URI" \
                      --name $CONTAINER_NAME $IMAGE_NAME
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Deployment completed successfully!"
        }
        failure {
            echo "Deployment failed. Check logs for details."
        }
    }
}