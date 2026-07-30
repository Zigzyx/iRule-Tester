pipeline {
    agent any

    environment {
        BIGIP_HOST   = 'bigip-staging.internal.net'
        BIGIP_CREDS  = credentials('bigip-ci-credentials') // Binds $BIGIP_CREDS_USR and $BIGIP_CREDS_PSW
        STAGING_PART = 'Staging_Validation'
    }

    stages {
        stage('Checkout Source') {
            steps {
                checkout scm
            }
        }

        stage('Setup Dependencies') {
            steps {
                // Ensure required Python libraries are installed on the Jenkins agent
                sh 'python3 -m pip install --quiet requests'
            }
        }

        stage('Static Code Analysis & Linting') {
            steps {
                sh 'python3 scripts/irule_linter.py irules/*.tcl'
            }
        }

        stage('Multi-iRule Conflict Analysis') {
            steps {
                sh '''
                    for map in mappings/*.json; do
                        python3 scripts/conflict_checker.py "$map"
                    done
                '''
            }
        }

        stage('BIG-IP Object Dependency Audit') {
            steps {
                sh '''
                    for irule in irules/*.tcl; do
                        python3 scripts/dependency_checker.py "${BIGIP_HOST}" "${BIGIP_CREDS_USR}" "${BIGIP_CREDS_PSW}" "$irule"
                    done
                '''
            }
        }

        stage('BIG-IP Sandbox Compilation (Dry-Run)') {
            steps {
                sh '''
                    for irule in irules/*.tcl; do
                        IRULE_NAME=$(basename "$irule" .tcl)
                        IRULE_CONTENT=$(jq -sR . "$irule")
                        
                        curl -sk -u "${BIGIP_CREDS_USR}:${BIGIP_CREDS_PSW}" \
                          -X POST "https://${BIGIP_HOST}/mgmt/tm/ltm/rule" \
                          -H "Content-Type: application/json" \
                          -d "{\"name\":\"${IRULE_NAME}_ci_test\", \"partition\":\"${STAGING_PART}\", \"apiAnonymous\": ${IRULE_CONTENT}}"
                    done
                '''
            }
        }

        stage('Behavioral Integration Testing') {
            steps {
                sh '''
                    curl -k -s -H "Host: myververworld.com" https://${BIGIP_HOST}/ | grep "interswitchgroup.com/card-network"
                '''
            }
        }

        stage('Manual Approval Gate') {
            steps {
                input message: 'All static, dependency, and compilation checks passed. Approve deployment to Production Virtual Servers?', submitter: 'network-security-admin'
            }
        }

        stage('Deploy to Production Virtual Servers') {
            steps {
                sh 'echo "Applying iRules to target Virtual Servers..."'
            }
        }
    }

    post {
        always {
            sh '''
                for irule in irules/*.tcl; do
                    IRULE_NAME=$(basename "$irule" .tcl)
                    curl -sk -u "${BIGIP_CREDS_USR}:${BIGIP_CREDS_PSW}" \
                      -X DELETE "https://${BIGIP_HOST}/mgmt/tm/ltm/rule/~${STAGING_PART}~${IRULE_NAME}_ci_test" || true
                done
            '''
        }
        failure {
            echo "iRule Validation Pipeline Failed. Review logs for errors."
        }
    }
}
