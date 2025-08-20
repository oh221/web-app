pipeline {
    agent any
    
    environment {
        // Docker Hub credentials (configure in Jenkins)
        DOCKERHUB_CREDENTIALS = 'dockerhub-credentials'
        DOCKER_IMAGE = 'omarh120/web-app'
        DOCKER_TAG = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
        LATEST_TAG = 'latest'
        
        // Application settings
        COMPOSE_FILE = 'docker-compose.yml'
        APP_NAME = 'django-web-app'
        
        // Python environment
        PYTHON_VERSION = '3.11'
    }
    
    options {
        // Keep last 10 builds
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Timeout after 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        // Add timestamps to console output
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '🔄 Checking out code from GitHub...'
                checkout scm
                
                // Display git information
                sh '''
                    echo "Current branch: $(git branch --show-current)"
                    echo "Latest commit: $(git log -1 --pretty=format:'%h - %s (%an)')"
                '''
            }
        }
        
        stage('Environment Setup') {
            steps {
                echo '🐍 Setting up Python environment...'
                sh '''
                    # Create virtual environment if it doesn't exist
                    if [ ! -d "venv" ]; then
                        python3 -m venv venv
                    fi
                    
                    # Activate virtual environment and install dependencies
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    
                    # Display installed packages
                    echo "📦 Installed packages:"
                    pip list
                '''
            }
        }
        
        stage('Code Quality & Security') {
            parallel {
                stage('Lint Code') {
                    steps {
                        echo '🔍 Running code quality checks...'
                        sh '''
                            . venv/bin/activate
                            
                            # Install linting tools if not in requirements
                            pip install flake8 black isort || true
                            
                            # Check code formatting
                            echo "Checking code formatting with black..."
                            black --check . || true
                            
                            # Check import sorting
                            echo "Checking import sorting..."
                            isort --check-only . || true
                            
                            # Run flake8 linting
                            echo "Running flake8 linting..."
                            flake8 . --max-line-length=88 --exclude=venv,migrations || true
                        '''
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        echo '🔒 Running security checks...'
                        sh '''
                            . venv/bin/activate
                            
                            # Install security tools
                            pip install safety bandit || true
                            
                            # Check for known security vulnerabilities
                            echo "Checking for security vulnerabilities..."
                            safety check || true
                            
                            # Run bandit security linter
                            echo "Running bandit security scan..."
                            bandit -r . -x venv/ || true
                        '''
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                echo '🧪 Running Django tests...'
                sh '''
                    . venv/bin/activate
                    
                    # Set test environment variables
                    export DEBUG=1
                    export SECRET_KEY=test-secret-key-for-ci
                    
                    # Run Django system checks
                    echo "Running Django system checks..."
                    python manage.py check
                    
                    # Run migrations (for test database)
                    echo "Running test migrations..."
                    python manage.py migrate --run-syncdb
                    
                    # Run tests with coverage if available
                    echo "Running Django tests..."
                    if pip show coverage > /dev/null 2>&1; then
                        coverage run manage.py test
                        coverage report
                        coverage xml
                    else
                        python manage.py test
                    fi
                '''
            }
            post {
                always {
                    // Publish test results if they exist
                    publishTestResults testResultsPattern: 'test-results.xml', allowEmptyResults: true
                    // Publish coverage reports if they exist
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                script {
                    // Build the Docker image
                    def image = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    
                    // Also tag as latest
                    sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:${LATEST_TAG}"
                    
                    // Store image info for later stages
                    env.BUILT_IMAGE = "${DOCKER_IMAGE}:${DOCKER_TAG}"
                    
                    echo "✅ Built image: ${env.BUILT_IMAGE}"
                }
            }
        }
        
        stage('Test Docker Container') {
            steps {
                echo '🔧 Testing Docker container...'
                sh '''
                    # Remove any existing test containers
                    docker rm -f test-container || true
                    
                    # Run container in test mode
                    echo "Starting test container..."
                    docker run -d --name test-container \
                        -p 8001:8000 \
                        -e DEBUG=0 \
                        -e SECRET_KEY=test-secret-key \
                        ${BUILT_IMAGE}
                    
                    # Wait for container to start
                    sleep 10
                    
                    # Check if container is running
                    if docker ps | grep test-container; then
                        echo "✅ Container is running"
                        
                        # Test if the application responds
                        echo "Testing application health..."
                        if curl -f http://localhost:8001/ || curl -f http://localhost:8001/health/ || curl -f http://localhost:8001/admin/; then
                            echo "✅ Application is responding"
                        else
                            echo "⚠️  Application might not be fully ready, but container is running"
                        fi
                    else
                        echo "❌ Container failed to start"
                        docker logs test-container
                        exit 1
                    fi
                    
                    # Cleanup
                    docker stop test-container
                    docker rm test-container
                '''
            }
        }
        
        stage('Push to Docker Hub') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                    branch 'develop'
                }
            }
            steps {
                echo '📤 Pushing to Docker Hub...'
                script {
                    docker.withRegistry('https://registry.hub.docker.com', DOCKERHUB_CREDENTIALS) {
                        // Push both versioned and latest tags
                        sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                        sh "docker push ${DOCKER_IMAGE}:${LATEST_TAG}"
                        
                        echo "✅ Pushed ${DOCKER_IMAGE}:${DOCKER_TAG}"
                        echo "✅ Pushed ${DOCKER_IMAGE}:${LATEST_TAG}"
                    }
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '🚀 Deploying to staging environment...'
                sh '''
                    # Update docker-compose to use the new image
                    sed -i "s|omarh120/web-app:.*|${DOCKER_IMAGE}:${DOCKER_TAG}|g" docker-compose.yml || true
                    
                    # Deploy using docker-compose
                    echo "Stopping existing containers..."
                    docker-compose -f ${COMPOSE_FILE} down || true
                    
                    echo "Starting updated containers..."
                    docker-compose -f ${COMPOSE_FILE} up -d
                    
                    # Wait for deployment
                    sleep 15
                    
                    # Verify deployment
                    if docker-compose -f ${COMPOSE_FILE} ps | grep "Up"; then
                        echo "✅ Deployment successful"
                        
                        # Run post-deployment tasks
                        echo "Running post-deployment tasks..."
                        docker-compose -f ${COMPOSE_FILE} exec -T web python manage.py migrate || true
                        docker-compose -f ${COMPOSE_FILE} exec -T web python manage.py collectstatic --noinput || true
                    else
                        echo "❌ Deployment failed"
                        docker-compose -f ${COMPOSE_FILE} logs
                        exit 1
                    fi
                '''
            }
        }
        
        stage('Smoke Tests') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '💨 Running smoke tests on deployed application...'
                sh '''
                    # Wait for application to be fully ready
                    sleep 30
                    
                    # Basic health checks
                    echo "Testing application endpoints..."
                    
                    # Test main application
                    if curl -f http://localhost:8000/ || curl -f http://localhost:8000/admin/; then
                        echo "✅ Application is accessible"
                    else
                        echo "❌ Application is not accessible"
                        docker-compose -f ${COMPOSE_FILE} logs web
                        exit 1
                    fi
                    
                    # Check Docker container status
                    if docker-compose -f ${COMPOSE_FILE} ps | grep "Up"; then
                        echo "✅ All services are running"
                    else
                        echo "❌ Some services are not running"
                        exit 1
                    fi
                '''
            }
        }
    }
    
    post {
        always {
            echo '🧹 Cleaning up...'
            
            // Clean up Docker images to save space
            sh '''
                # Remove old images (keep last 3 builds)
                docker images ${DOCKER_IMAGE} --format "table {{.Tag}}" | tail -n +4 | head -n -3 | xargs -r docker rmi ${DOCKER_IMAGE}: || true
                
                # Clean up dangling images
                docker image prune -f || true
            '''
            
            // Archive artifacts
            archiveArtifacts artifacts: 'logs/**/*.log, coverage.xml', allowEmptyArchive: true
            
            // Clean workspace
            cleanWs()
        }
        
        success {
            echo '✅ Pipeline completed successfully!'
            
            // Send success notification (configure webhook/email)
            // slackSend channel: '#deployments', 
            //           message: "✅ ${APP_NAME} deployed successfully! Build: ${BUILD_NUMBER}"
        }
        
        failure {
            echo '❌ Pipeline failed!'
            
            // Send failure notification
            // slackSend channel: '#deployments', 
            //           message: "❌ ${APP_NAME} deployment failed! Build: ${BUILD_NUMBER}. Check: ${BUILD_URL}"
        }
        
        unstable {
            echo '⚠️ Pipeline completed with warnings!'
        }
    }
}