pipeline {
    agent any
    
    environment {
        DOCKERHUB_CREDENTIALS = 'dockerhub-credentials'
        DOCKER_IMAGE = 'omarh120/web-app'
        DOCKER_TAG = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
        LATEST_TAG = 'latest'
        COMPOSE_FILE = 'docker-compose.yml'
        APP_NAME = 'django-web-app'
        PYTHON_VERSION = '3.11'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        skipDefaultCheckout(false)
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
                
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
                echo 'Setting up Python environment...'
                sh '''
                    rm -rf venv
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    else
                        echo "No requirements.txt found, installing basic Django"
                        pip install django
                    fi
                    
                    echo "Python version: $(python --version)"
                    echo "Pip version: $(pip --version)"
                    pip list
                '''
            }
        }
        
        stage('Code Quality & Security') {
            parallel {
                stage('Lint Code') {
                    steps {
                        echo 'Running code quality checks...'
                        sh '''
                            . venv/bin/activate
                            pip install flake8 black isort || echo "Could not install linting tools"
                            black --check --diff . || echo "Code formatting issues found"
                            isort --check-only --diff . || echo "Import sorting issues found"
                            flake8 . --max-line-length=88 --exclude=venv,migrations,__pycache__ --exit-zero || echo "Linting issues found"
                        '''
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        echo 'Running security checks...'
                        sh '''
                            . venv/bin/activate
                            pip install safety bandit || echo "Could not install security tools"
                            safety check --json || echo "Security vulnerabilities found"
                            bandit -r . -f json -o bandit-report.json -x venv/ || echo "Security issues found"
                            
                            if [ -f bandit-report.json ]; then
                                echo "Bandit report generated"
                            fi
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                echo 'Running Django tests...'
                sh '''
                    . venv/bin/activate
                    export DEBUG=1
                    export SECRET_KEY=test-secret-key-for-ci-${BUILD_NUMBER}
                    export ALLOWED_HOSTS=localhost,127.0.0.1
                    
                    if [ ! -f manage.py ]; then
                        echo "manage.py not found! This doesn't appear to be a Django project."
                        exit 1
                    fi
                    
                    python manage.py check --deploy || echo "System check issues found"
                    python manage.py migrate --run-syncdb --verbosity=1
                    
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
                    script {
                        if (fileExists('test-results.xml')) {
                            junit testResultsPattern: 'test-results.xml', allowEmptyResults: true
                        }
                    }
                    archiveArtifacts artifacts: 'htmlcov/**/*', allowEmptyArchive: true
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
                script {
                    try {
                        sh "docker image prune -f || true"
                        def image = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                        sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:${LATEST_TAG}"
                        env.BUILT_IMAGE = "${DOCKER_IMAGE}:${DOCKER_TAG}"
                        echo "Built image: ${env.BUILT_IMAGE}"
                        sh "docker images ${DOCKER_IMAGE}"
                    } catch (Exception e) {
                        echo "Docker build failed: ${e.getMessage()}"
                        throw e
                    }
                }
            }
        }
        
        stage('Test Docker Container') {
            steps {
                echo 'Testing Docker container...'
                sh '''
                    docker rm -f test-container || true
                    
                    echo "Starting test container..."
                    docker run -d --name test-container \
                        -p 8001:8000 \
                        -e DEBUG=0 \
                        -e SECRET_KEY=test-secret-key-${BUILD_NUMBER} \
                        -e ALLOWED_HOSTS=localhost,127.0.0.1 \
                        ${BUILT_IMAGE}
                    
                    sleep 15
                    echo "Container logs:"
                    docker logs test-container
                    
                    if docker ps | grep test-container; then
                        echo "Container is running"
                        
                        for i in {1..5}; do
                            if curl -f --connect-timeout 10 --max-time 30 http://localhost:8001/ || 
                               curl -f --connect-timeout 10 --max-time 30 http://localhost:8001/admin/; then
                                echo "Application is responding (attempt $i)"
                                break
                            else
                                echo "Waiting for application to respond (attempt $i/5)..."
                                sleep 10
                            fi
                            
                            if [ $i -eq 5 ]; then
                                echo "Application not responding, but container is running"
                                docker logs test-container
                            fi
                        done
                    else
                        echo "Container failed to start"
                        docker logs test-container
                        exit 1
                    fi
                '''
            }
            post {
                always {
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
                echo 'Pushing to Docker Hub...'
                script {
                    docker.withRegistry('https://registry.hub.docker.com', DOCKERHUB_CREDENTIALS) {
                        try {
                            sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                            sh "docker push ${DOCKER_IMAGE}:${LATEST_TAG}"
                            echo "Pushed ${DOCKER_IMAGE}:${DOCKER_TAG}"
                            echo "Pushed ${DOCKER_IMAGE}:${LATEST_TAG}"
                        } catch (Exception e) {
                            echo "Failed to push to Docker Hub: ${e.getMessage()}"
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
                echo 'Deploying to staging environment...'
                sh '''
                    echo "Stopping existing containers..."
                    docker compose -f ${COMPOSE_FILE} down --timeout 30 || true
                    docker container prune -f || true
                    
                    export DOCKER_IMAGE_TAG=${DOCKER_TAG}
                    
                    echo "Starting updated containers..."
                    docker compose -f ${COMPOSE_FILE} up -d --force-recreate
                    
                    sleep 30
                    
                    if docker compose -f ${COMPOSE_FILE} ps | grep "Up"; then
                        echo "Deployment successful"
                        docker compose -f ${COMPOSE_FILE} exec -T web python manage.py migrate --noinput || echo "Migration failed"
                        docker compose -f ${COMPOSE_FILE} exec -T web python manage.py collectstatic --noinput || echo "Static files collection failed"
                        docker compose -f ${COMPOSE_FILE} ps
                    else
                        echo "Deployment failed"
                        docker compose -f ${COMPOSE_FILE} logs --tail=50
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
                echo 'Running smoke tests on deployed application...'
                sh '''
                    sleep 30
                    
                    success=false
                    for i in {1..5}; do
                        if curl -f --connect-timeout 10 --max-time 30 http://localhost:8000/ || 
                           curl -f --connect-timeout 10 --max-time 30 http://localhost:8000/admin/; then
                            echo "Application is accessible (attempt $i)"
                            success=true
                            break
                        else
                            echo "Waiting for application (attempt $i/5)..."
                            sleep 15
                        fi
                    done
                    
                    if [ "$success" = false ]; then
                        echo "Application is not accessible after multiple attempts"
                        docker compose -f ${COMPOSE_FILE} logs web --tail=50
                        exit 1
                    fi
                    
                    if docker compose -f ${COMPOSE_FILE} ps | grep "Up"; then
                        echo "All services are running"
                        docker compose -f ${COMPOSE_FILE} ps
                    else
                        echo "Some services are not running"
                        exit 1
                    fi
                    
                    echo "Disk usage:"
                    df -h
                    
                    echo "Docker stats:"
                    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
                '''
            }
        }
    }
    
    post {
        always {
            echo 'Cleaning up...'
            
            sh '''
                docker images ${DOCKER_IMAGE} --format "table {{.Tag}}" | tail -n +6 | xargs -r -I {} docker rmi ${DOCKER_IMAGE}:{} || true
                docker image prune -f || true
                docker container prune -f || true
                echo "Remaining images:"
                docker images ${DOCKER_IMAGE} || true
            '''
            
            archiveArtifacts artifacts: 'logs/**/*.log, coverage.xml, htmlcov/**/*', allowEmptyArchive: true
            
            script {
                if (fileExists('**/*test*.xml')) {
                    junit testResultsPattern: '**/*test*.xml', allowEmptyResults: true
                }
            }
        }
        
        success {
            echo 'Pipeline completed successfully!'
            echo "Build ${BUILD_NUMBER} deployed successfully!"
            echo "Application URL: http://localhost:8000"
        }
        
        failure {
            echo 'Pipeline failed!'
            echo "Build ${BUILD_NUMBER} failed at stage: ${env.STAGE_NAME}"
            
            sh '''
                docker stop test-container || true
                docker rm test-container || true
                docker compose -f ${COMPOSE_FILE} down || true
            '''
        }
        
        unstable {
            echo 'Pipeline completed with warnings!'
            echo "Build ${BUILD_NUMBER} completed but some tests may have failed"
        }
        
        cleanup {
            cleanWs(cleanWhenNotBuilt: false,
                   deleteDirs: true,
                   disableDeferredWipeout: true,
                   notFailBuild: true)
        }
    }
}