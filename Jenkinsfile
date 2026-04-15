pipeline {
    agent any

    environment {
        IMAGE_NAME = "shaunak30/myapp"  
        CONTAINER_NAME = "myapp-container"
    }

    stages {

        stage('Pull Image from Docker Hub') {
            steps {
                echo "Pulling the latest image..."
                sh 'docker pull $IMAGE_NAME'
            }
        }

        stage('Stop Old Container') {
            steps {
                echo "Stopping existing container if running..."
                sh '''
                docker stop $CONTAINER_NAME || true
                docker rm $CONTAINER_NAME || true
                '''
            }
        }

        stage('Free Port 8000 (IMPORTANT FIX)') {
            steps {
                echo "Freeing port 8000 if occupied..."
                sh '''
                PORT=$(lsof -t -i:8000)
                if [ -n "$PORT" ]; then
                    echo "Port 8000 is in use. Killing process $PORT"
                    kill -9 $PORT
                fi
                '''
            }
        }

        stage('Run New Container with MongoDB Atlas') {
            steps {
                echo "Starting new container with MongoDB Atlas..."
                withCredentials([string(credentialsId: 'mongo-uri', variable: 'MONGO_URI')]) {
                    sh '''
                    docker run -d --restart always -p 8000:8000 \
                        -e MONGO_URI="$MONGO_URI" \
                        --name $CONTAINER_NAME $IMAGE_NAME
                    '''
                }
            }
        }

        stage('Run Django Migrations') {
            steps {
                echo "Running Django migrations inside the container..."
                sh '''
                docker exec $CONTAINER_NAME python manage.py makemigrations
                docker exec $CONTAINER_NAME python manage.py migrate
                '''
            }
        }
    }

    post {
        success {
            echo "Deployment and migrations completed successfully!"
        }
        failure {
            echo "Deployment failed. Check logs for details."
        }
    }
}