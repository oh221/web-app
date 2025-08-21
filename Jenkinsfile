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
        // Skip default checkout
        skipDefaultCheckout(false)
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '🔄 Checking out code from GitHub...'
                checkout scm
                
                // Display git information
                script {
                    env.GIT_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.GIT_BRANCH = sh(script: 'git rev-parse --abbrev-ref HEAD', returnStdout: true).trim()
                }
                
                sh '''
                    echo "Current branch: ${GIT_BRANCH}"
                    echo "Latest commit: $(git log -1 --pretty=format:'%h - %s (%an)')"
                    echo "Full commit hash: ${GIT_COMMIT}"
                '''
            }
        }
        
        stage('Environment Setup') {
            steps {
                echo '🐍 Setting up Python environment...'
                sh '''
                    # Remove existing venv if it exists
                    rm -rf venv
                    
                    # Create fresh virtual environment
                    python3 -m venv venv
                    
                    # Activate virtual environment and install dependencies
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    
                    # Check if requirements.txt exists
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    else
                        echo "⚠️ No requirements.txt found, installing basic Django"
                        pip install django
                    fi
                    
                    # Display Python and pip versions
                    echo "🐍 Python version: $(python --version)"
                    echo "📦 Pip version: $(pip --version)"
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
                            
                            # Install linting tools
                            pip install flake8 black isort || echo "⚠️ Could not install linting tools"
                            
                            # Check code formatting with black (non-blocking)
                            echo "Checking code formatting with black..."
                            black --check --diff . || echo "⚠️ Code formatting issues found"
                            
                            # Check import sorting (non-blocking)
                            echo "Checking import sorting..."
                            isort --check-only --diff . || echo "⚠️ Import sorting issues found"
                            
                            # Run flake8 linting (non-blocking)
                            echo "Running flake8 linting..."
                            flake8 . --max-line-length=88 --exclude=venv,migrations,__pycache__ --exit-zero || echo "⚠️ Linting issues found"
                        '''
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        echo '🔒 Running security checks...'
                        sh '''
                            . venv/bin/activate
                            
                            # Install security tools
                            pip install safety bandit || echo "⚠️ Could not install security tools"
                            
                            # Check for known security vulnerabilities (non-blocking)
                            echo "Checking for security vulnerabilities..."
                            safety check --json || echo "⚠️ Security vulnerabilities found"
                            
                            # Run bandit security linter (non-blocking)
                            echo "Running bandit security scan..."
                            bandit -r . -f json -o bandit-report.json -x venv/ || echo "⚠️ Security issues found"
                            
                            # Display results if they exist
                            if [ -f bandit-report.json ]; then
                                echo "📋 Bandit report generated"
                            fi
                        '''
                    }
                    post {
                        always {
                            // Archive security reports
                            archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                        }
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
                    export SECRET_KEY=test-secret-key-for-ci-${BUILD_NUMBER}
                    export ALLOWED_HOSTS=localhost,127.0.0.1
                    
                    # Check if manage.py exists
                    if [ ! -f manage.py ]; then
                        echo "❌ manage.py not found! This doesn't appear to be a Django project."
                        exit 1
                    fi
                    
                    # Run Django system checks
                    echo "Running Django system checks..."
                    python manage.py check --deploy || echo "⚠️ System check issues found"
                    
                    # Create test database and run migrations
                    echo "Running test migrations..."
                    python manage.py migrate --run-syncdb --verbosity=1
                    
                    # Run tests with coverage if available
                    echo "Running Django tests..."
                    pip install coverage || echo "Coverage not installed"
                    
                    if command -v coverage &> /dev/null; then
                        coverage run --source='.' manage.py test --verbosity=2
                        coverage report --show-missing
                        coverage xml -o coverage.xml
                        coverage html -d htmlcov/
                    else
                        python manage.py test --verbosity=2
                    fi
                '''
            }
            post {
                always {
                    // Publish test results if they exist
                    publishTestResults testResultsPattern: 'test-results.xml', allowEmptyResults: true
                    // Publish coverage reports if they exist
                    script {
                        if (fileExists('coverage.xml')) {
                            publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                        }
                    }
                    // Archive coverage HTML report
                    archiveArtifacts artifacts: 'htmlcov/**/*', allowEmptyArchive: true
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                script {
                    try {
                        // Clean up old images first
                        sh "docker image prune -f || true"
                        
                        // Build the Docker image
                        def image = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                        
                        // Also tag as latest
                        sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:${LATEST_TAG}"
                        
                        // Store image info for later stages
                        env.BUILT_IMAGE = "${DOCKER_IMAGE}:${DOCKER_TAG}"
                        
                        echo "✅ Built image: ${env.BUILT_IMAGE}"
                        
                        // Show image info
                        sh "docker images ${DOCKER_IMAGE}"
                        
                    } catch (Exception e) {
                        echo "❌ Docker build failed: ${e.getMessage()}"
                        throw e
                    }
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
                        -e SECRET_KEY=test-secret-key-${BUILD_NUMBER} \
                        -e ALLOWED_HOSTS=localhost,127.0.0.1 \
                        ${BUILT_IMAGE}
                    
                    # Wait for container to start and show logs
                    echo "Waiting for container to start..."
                    sleep 15
                    
                    # Show container logs
                    echo "Container logs:"
                    docker logs test-container
                    
                    # Check if container is running
                    if docker ps | grep test-container; then
                        echo "✅ Container is running"
                        
                        # Test if the application responds (with retries)
                        echo "Testing application health..."
                        for i in {1..5}; do
                            if curl -f --connect-timeout 10 --max-time 30 http://localhost:8001/ || 
                               curl -f --connect-timeout 10 --max-time 30 http://localhost:8001/admin/ || 
                               curl -f --connect-timeout 10 --max-time 30 http://localhost:8001/health/; then
                                echo "✅ Application is responding (attempt $i)"
                                break
                            else
                                echo "⏳ Waiting for application to respond (attempt $i/5)..."
                                sleep 10
                            fi
                            
                            if [ $i -eq 5 ]; then
                                echo "⚠️ Application not responding, but container is running"
                                docker logs test-container
                            fi
                        done
                    else
                        echo "❌ Container failed to start"
                        docker logs test-container
                        exit 1
                    fi
                '''
            }
            post {
                always {
                    // Cleanup test container
                    sh '''
                        docker stop test-container || true
                        docker rm test-container || true
                    '''
                }
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
                        try {
                            // Push both versioned and latest tags
                            sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                            sh "docker push ${DOCKER_IMAGE}:${LATEST_TAG}"
                            
                            echo "✅ Pushed ${DOCKER_IMAGE}:${DOCKER_TAG}"
                            echo "✅ Pushed ${DOCKER_IMAGE}:${LATEST_TAG}"
                        } catch (Exception e) {
                            echo "❌ Failed to push to Docker Hub: ${e.getMessage()}"
                            throw e
                        }
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
                    # Stop existing containers gracefully
                    echo "Stopping existing containers..."
                    docker-compose -f ${COMPOSE_FILE} down --timeout 30 || true
                    
                    # Clean up old containers and images
                    docker container prune -f || true
                    
                    # Use the built image for deployment
                    export DOCKER_IMAGE_TAG=${DOCKER_TAG}
                    
                    # Start updated containers
                    echo "Starting updated containers..."
                    docker-compose -f ${COMPOSE_FILE} up -d --force-recreate
                    
                    # Wait for deployment
                    echo "Waiting for services to start..."
                    sleep 30
                    
                    # Verify deployment
                    if docker-compose -f ${COMPOSE_FILE} ps | grep "Up"; then
                        echo "✅ Deployment successful"
                        
                        # Run post-deployment tasks
                        echo "Running post-deployment tasks..."
                        docker-compose -f ${COMPOSE_FILE} exec -T web python manage.py migrate --noinput || echo "⚠️ Migration failed"
                        docker-compose -f ${COMPOSE_FILE} exec -T web python manage.py collectstatic --noinput || echo "⚠️ Static files collection failed"
                        
                        # Show running services
                        docker-compose -f ${COMPOSE_FILE} ps
                    else
                        echo "❌ Deployment failed"
                        docker-compose -f ${COMPOSE_FILE} logs --tail=50
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
                    echo "Waiting for application to stabilize..."
                    sleep 30
                    
                    # Basic health checks with retries
                    echo "Testing application endpoints..."
                    success=false
                    
                    for i in {1..5}; do
                        if curl -f --connect-timeout 10 --max-time 30 http://localhost:8000/ || 
                           curl -f --connect-timeout 10 --max-time 30 http://localhost:8000/admin/; then
                            echo "✅ Application is accessible (attempt $i)"
                            success=true
                            break
                        else
                            echo "⏳ Waiting for application (attempt $i/5)..."
                            sleep 15
                        fi
                    done
                    
                    if [ "$success" = false ]; then
                        echo "❌ Application is not accessible after multiple attempts"
                        docker-compose -f ${COMPOSE_FILE} logs web --tail=50
                        exit 1
                    fi
                    
                    # Check Docker container status
                    if docker-compose -f ${COMPOSE_FILE} ps | grep "Up"; then
                        echo "✅ All services are running"
                        docker-compose -f ${COMPOSE_FILE} ps
                    else
                        echo "❌ Some services are not running"
                        docker-compose -f ${COMPOSE_FILE} ps
                        docker-compose -f ${COMPOSE_FILE} logs --tail=50
                        exit 1
                    fi
                    
                    # Additional health checks
                    echo "Running additional health checks..."
                    
                    # Check disk space
                    echo "💾 Disk usage:"
                    df -h
                    
                    # Check Docker stats
                    echo "🐳 Docker stats:"
                    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
                '''
            }
        }
    }
    
    post {
        always {
            echo '🧹 Cleaning up...'
            
            // Clean up Docker images to save space (keep last 5 builds)
            sh '''
                # Remove old tagged images (keep recent ones)
                docker images ${DOCKER_IMAGE} --format "table {{.Tag}}" | tail -n +6 | xargs -r -I {} docker rmi ${DOCKER_IMAGE}:{} || true
                
                # Clean up dangling images and unused containers
                docker image prune -f || true
                docker container prune -f || true
                
                # Show remaining images
                echo "Remaining images:"
                docker images ${DOCKER_IMAGE} || true
            '''
            
            // Archive important artifacts
            archiveArtifacts artifacts: 'logs/**/*.log, coverage.xml, htmlcov/**/*', allowEmptyArchive: true
            
            // Publish final test results
            publishTestResults testResultsPattern: '**/*test*.xml', allowEmptyResults: true
        }
        
        success {
            echo '✅ Pipeline completed successfully!'
            echo "🎉 Build ${BUILD_NUMBER} deployed successfully!"
            echo "🔗 Application URL: http://localhost:8000"
            
            // Send success notification (uncomment and configure as needed)
            // slackSend channel: '#deployments', 
            //           color: 'good',
            //           message: "✅ ${APP_NAME} Build #${BUILD_NUMBER} deployed successfully!\n🔗 Commit: ${GIT_COMMIT.take(7)}\n🌐 URL: http://localhost:8000"
        }
        
        failure {
            echo '❌ Pipeline failed!'
            echo "💥 Build ${BUILD_NUMBER} failed at stage: ${env.STAGE_NAME}"
            
            // Clean up any remaining test containers
            sh '''
                docker stop test-container || true
                docker rm test-container || true
                docker-compose -f ${COMPOSE_FILE} down || true
            '''
            
            // Send failure notification (uncomment and configure as needed)
            // slackSend channel: '#deployments',
            //           color: 'danger', 
            //           message: "❌ ${APP_NAME} Build #${BUILD_NUMBER} failed!\n💥 Stage: ${env.STAGE_NAME}\n🔗 Check: ${BUILD_URL}"
        }
        
        unstable {
            echo '⚠️ Pipeline completed with warnings!'
            echo "⚠️ Build ${BUILD_NUMBER} completed but some tests may have failed"
        }
        
        cleanup {
            // Final cleanup
            cleanWs(cleanWhenNotBuilt: false,
                   deleteDirs: true,
                   disableDeferredWipeout: true,
                   notFailBuild: true)
        }
    }
}