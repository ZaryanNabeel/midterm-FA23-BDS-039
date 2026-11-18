pipeline {
  agent any

  triggers { githubPush() }

  environment {
    SID   = 'FA23-BDS-039'
    IMAGE = 'midterm-fa23-bds-039'
    MAIL_TO = 'qasimalik@gmail.com'
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Train & Test') {
      steps {
        sh '''
          docker run --rm --user $(id -u):$(id -g) \
            -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 -e GIT_COMMIT=$GIT_COMMIT \
            -v "$WORKSPACE":/work -w /work python:3.11-slim \
            sh -c "pip install -q --user -r requirements.txt pytest httpx && python train.py && python -m pytest -q -p no:cacheprovider"
        '''
      }
    }

    stage('Build Image') {
      steps {
        sh 'docker build --build-arg GIT_COMMIT=$GIT_COMMIT -t $IMAGE:latest .'
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          docker rm -f midterm || true
          docker run -d --name midterm --restart unless-stopped -p 8000:8000 $IMAGE:latest
          for i in $(seq 1 20); do
            curl -sf http://localhost:8000/metrics && exit 0
            sleep 3
          done
          echo "Deployment health check failed"; exit 1
        '''
      }
    }

    stage('Push to Docker Hub') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
          withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                           usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
            sh '''
              echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
              docker tag $IMAGE:latest $DH_USER/$IMAGE:latest
              docker tag $IMAGE:latest $DH_USER/$IMAGE:$GIT_COMMIT
              docker push $DH_USER/$IMAGE:latest
              docker push $DH_USER/$IMAGE:$GIT_COMMIT
              docker logout
            '''
          }
        }
      }
    }
  }

  post {
    always {
      script {
        def metrics = sh(returnStdout: true, script: 'curl -s http://localhost:8000/metrics || echo unavailable').trim()
        emailext(
          to: env.MAIL_TO,
          subject: "MIDTERM ${env.SID} - Build #${env.BUILD_NUMBER} ${currentBuild.currentResult}",
          body: "Student Reg No: ${env.SID}\nResult: ${currentBuild.currentResult}\nCommit: ${env.GIT_COMMIT}\nMetrics: ${metrics}\nBuild: ${env.BUILD_URL}"
        )
      }
    }
  }
}
