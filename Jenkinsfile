pipeline {
    agent any

    environment {
        PORT = "8000"
        VENV_DIR = "${WORKSPACE}/venv"
        APP_NAME = "main"
    }

    stages {

        stage('Check & Kill Existing Process') {
            steps {
                script {
                    def pids = sh(script: "lsof -ti tcp:${PORT} || true", returnStdout: true).trim()
                    if (pids) {
                        sh "kill -9 ${pids} || true"
                        echo "Killed existing process on port ${PORT}."
                    } else {
                        echo "No process found on port ${PORT}."
                    }
                }
            }
        }

        stage('Checkout Code') {
            steps {
                git branch: 'master', url: 'https://github.com/autkarsh989/CareMate'
            }
        }

        stage('Run FastAPI in Background') {
            steps {
                script {
                    sh """
                    JENKINS_NODE_COOKIE=dontKillMe nohup ${env.VENV_DIR}/bin/python -m uvicorn ${env.APP_NAME}:app --host 0.0.0.0 --port ${env.PORT} > fastapi.log 2>&1 & 
                    """
                }
            }
        }

    }

    post {
        success {
            echo "✅ Pipeline completed successfully! FastAPI is running in background."
        }
        failure {
            echo "❌ Pipeline failed. Check logs for details."
        }
    }
}
