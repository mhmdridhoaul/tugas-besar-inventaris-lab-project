pipeline {
    agent any

    environment {
        APP_NAME = 'lab-inventory'
        BACKEND_IMAGE = 'lab-inventory-backend'
        HEALTH_CHECK_URL = 'http://localhost:8080/health'
    }

    stages {
        // ========================================================
        // STAGE 1: CHECKOUT SCM
        // Mengunduh kode sumber terbaru dari repositori GitHub
        // ========================================================
        stage('Checkout') {
            steps {
                echo '=== [Stage 1] Mengunduh kode sumber dari GitHub (SCM) ==='
                checkout scm
                script {
                    echo "Commit ID: ${env.GIT_COMMIT ?: 'Local / Manual Trigger'}"
                    echo "Branch   : ${env.GIT_BRANCH ?: 'main'}"
                }
            }
        }

        // ========================================================
        // STAGE 2: SYNTAX CHECK
        // Validasi sintaks Python & validasi file konfigurasi Compose
        // ========================================================
        stage('Syntax Check') {
            steps {
                echo '=== [Stage 2] Validasi Sintaks Python & Konfigurasi ==='
                script {
                    if (isUnix()) {
                        sh '''
                            echo "Memeriksa sintaks Python app.py..."
                            python3 -m py_compile app.py || python -m py_compile app.py
                            echo "Python syntax check PASSED."
                        '''
                    } else {
                        bat '''
                            echo Memeriksa sintaks Python app.py...
                            python -m py_compile app.py
                            if errorlevel 1 exit /b 1
                            echo Python syntax check PASSED.
                        '''
                    }
                }
            }
        }

        // ========================================================
        // STAGE 3: BUILD IMAGE
        // Membangun image Docker Backend & mempersiapkan service
        // ========================================================
        stage('Build Image') {
            steps {
                echo '=== [Stage 3] Membangun Docker Image Backend ==='
                script {
                    if (isUnix()) {
                        sh '''
                            docker compose build --no-cache || docker-compose build --no-cache
                            echo "Docker Build Image PASSED."
                        '''
                    } else {
                        bat '''
                            docker-compose build --no-cache || docker compose build --no-cache
                            if errorlevel 1 exit /b 1
                            echo Docker Build Image PASSED.
                        '''
                    }
                }
            }
        }

        // ========================================================
        // STAGE 4: AUTOMATED DEPLOYMENT
        // Menjalankan stack Docker Compose (Backend, Frontend, Volume, Network)
        // ========================================================
        stage('Automated Deployment') {
            steps {
                echo '=== [Stage 4] Menjalankan Deployment Otomatis (Docker Compose) ==='
                script {
                    if (isUnix()) {
                        sh '''
                            echo "Menghentikan kontainer lama jika ada..."
                            docker compose down || docker-compose down || true
                            echo "Menjalankan stack kontainer baru di latar belakang..."
                            docker compose up -d --remove-orphans || docker-compose up -d --remove-orphans
                            echo "Status kontainer aktif:"
                            docker compose ps || docker-compose ps
                        '''
                    } else {
                        bat '''
                            echo Menghentikan kontainer lama jika ada...
                            docker-compose down || docker compose down || ver > nul
                            echo Menjalankan stack kontainer baru...
                            docker-compose up -d --remove-orphans || docker compose up -d --remove-orphans
                            if errorlevel 1 exit /b 1
                            docker-compose ps || docker compose ps
                        '''
                    }
                }
            }
        }

        // ========================================================
        // STAGE 5: HEALTH CHECK
        // Menguji ketersediaan layanan setelah deployment via HTTP GET
        // ========================================================
        stage('Health Check') {
            steps {
                echo '=== [Stage 5] Menjalankan Health Check Service ==='
                script {
                    if (isUnix()) {
                        sh '''
                            echo "Menunggu inisialisasi service (5 detik)..."
                            sleep 5
                            
                            echo "Menguji endpoint health check backend via Nginx reverse proxy..."
                            RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health || curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
                            
                            if [ "$RESPONSE" = "200" ]; then
                                echo "Health Check SUCCESS! HTTP Response: $RESPONSE"
                                echo "Backend & Frontend siap melayani traffic."
                            else
                                echo "Health Check FAILED! HTTP Response: $RESPONSE"
                                exit 1
                            fi
                        '''
                    } else {
                        bat '''
                            echo Menunggu inisialisasi service (5 detik)...
                            timeout /t 5 /nobreak > nul
                            
                            echo Menguji endpoint health check backend...
                            curl -s -f http://localhost:8080/health || curl -s -f http://localhost:5000/health
                            if errorlevel 1 (
                                echo Health Check GAGAL! Service belum siap.
                                exit /b 1
                            ) else (
                                echo Health Check SUKSES! Service berstatus UP.
                            )
                        '''
                    }
                }
            }
        }
    }

    // ========================================================
    // POST ACTIONS: NOTIFIKASI HASIL PIPELINE
    // ========================================================
    post {
        always {
            echo '=== Pipeline Execution Completed ==='
        }
        success {
            echo '====================================================='
            echo '  [SUCCESS] CI/CD PIPELINE SELESAI DENGAN SEMPURNA! '
            echo '  Aplikasi Lab Inventory Catalog aktif dan sehat.    '
            echo '  Akses UI di: http://localhost:8080                 '
            echo '====================================================='
        }
        failure {
            echo '====================================================='
            echo '  [FAILURE] PIPELINE MENGALAMI KENDALA!             '
            echo '  Silakan periksa log stage di atas untuk investigasi'
            echo '====================================================='
        }
    }
}
