#!/bin/bash

# Seiketsu AI Client Instance User Data Script
# Automatically configures and starts the application

set -e

# Variables passed from Terraform
CLIENT_ID="${client_id}"
DB_ENDPOINT="${db_endpoint}"
DB_NAME="${db_name}"
DB_USERNAME="${db_username}"
REDIS_ENDPOINT="${redis_endpoint}"
S3_BUCKET="${s3_bucket}"

# System configuration
echo "=== Seiketsu AI Client Instance Setup ==="
echo "Client ID: $CLIENT_ID"
echo "Starting system configuration..."

# Update system packages
yum update -y
yum install -y docker htop curl wget unzip awscli

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ec2-user to docker group
usermod -a -G docker ec2-user

# Create application directories
mkdir -p /opt/seiketsu
mkdir -p /opt/seiketsu/logs
mkdir -p /opt/seiketsu/config
mkdir -p /opt/seiketsu/data

# Create environment configuration
cat > /opt/seiketsu/.env << EOL
# Seiketsu AI Client Configuration
CLIENT_ID=$CLIENT_ID
ENVIRONMENT=production

# Database Configuration
DATABASE_URL=postgresql://$DB_USERNAME:__DB_PASSWORD__@$DB_ENDPOINT:5432/$DB_NAME
DB_HOST=$DB_ENDPOINT
DB_NAME=$DB_NAME
DB_USER=$DB_USERNAME
DB_PASSWORD=__DB_PASSWORD__
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://$REDIS_ENDPOINT:6379
REDIS_HOST=$REDIS_ENDPOINT
REDIS_PORT=6379
REDIS_PASSWORD=__REDIS_PASSWORD__

# AWS Configuration
AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
S3_BUCKET=$S3_BUCKET

# Application Configuration
APP_PORT=8000
APP_HOST=0.0.0.0
LOG_LEVEL=INFO
METRICS_ENABLED=true

# External API Configuration
ELEVENLABS_API_KEY=__ELEVENLABS_API_KEY__
TWILIO_ACCOUNT_SID=__TWILIO_ACCOUNT_SID__
TWILIO_AUTH_TOKEN=__TWILIO_AUTH_TOKEN__
TWILIO_PHONE_NUMBER=__TWILIO_PHONE_NUMBER__
MLS_API_KEY=__MLS_API_KEY__

# Security Configuration
JWT_SECRET_KEY=__JWT_SECRET_KEY__
ENCRYPTION_KEY=__ENCRYPTION_KEY__
EOL

# Create Docker Compose configuration
cat > /opt/seiketsu/docker-compose.yml << EOL
version: '3.8'

services:
  seiketsu-app:
    image: seiketsu/ai-voice-agent:latest
    container_name: seiketsu-${CLIENT_ID}
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - CLIENT_ID=${CLIENT_ID}
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./config:/app/config
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # CloudWatch Log Agent
  cloudwatch-agent:
    image: amazon/cloudwatch-agent:latest
    container_name: cloudwatch-agent-${CLIENT_ID}
    restart: unless-stopped
    volumes:
      - ./logs:/opt/aws/logs
      - ./cloudwatch-agent.json:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
    environment:
      - AWS_REGION=\${AWS_REGION}

  # Metrics Exporter
  metrics-exporter:
    image: seiketsu/metrics-exporter:latest
    container_name: metrics-exporter-${CLIENT_ID}
    restart: unless-stopped
    ports:
      - "9090:9090"
    environment:
      - CLIENT_ID=${CLIENT_ID}
      - METRICS_PORT=9090
    env_file:
      - .env
    depends_on:
      - seiketsu-app

networks:
  default:
    name: seiketsu-${CLIENT_ID}
EOL

# Create CloudWatch Agent configuration
cat > /opt/seiketsu/cloudwatch-agent.json << EOL
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/aws/logs/app.log",
            "log_group_name": "/aws/seiketsu/$CLIENT_ID",
            "log_stream_name": "application",
            "timezone": "UTC"
          },
          {
            "file_path": "/opt/aws/logs/error.log",
            "log_group_name": "/aws/seiketsu/$CLIENT_ID",
            "log_stream_name": "errors",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/messages",
            "log_group_name": "/aws/seiketsu/$CLIENT_ID",
            "log_stream_name": "system",
            "timezone": "UTC"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "Seiketsu/Client",
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
        "metrics_collection_interval": 60,
        "resources": ["*"],
        "totalcpu": false
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "diskio": {
        "measurement": ["io_time"],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      },
      "netstat": {
        "measurement": ["tcp_established", "tcp_time_wait"],
        "metrics_collection_interval": 60
      },
      "swap": {
        "measurement": ["swap_used_percent"],
        "metrics_collection_interval": 60
      }
    }
  }
}
EOL

# Create health check script
cat > /opt/seiketsu/health-check.sh << 'EOL'
#!/bin/bash

# Health check script for Seiketsu AI application
set -e

CLIENT_ID="$1"
if [ -z "$CLIENT_ID" ]; then
    echo "Usage: $0 <client_id>"
    exit 1
fi

echo "=== Health Check for Client: $CLIENT_ID ==="

# Check if containers are running
if ! docker-compose -f /opt/seiketsu/docker-compose.yml ps | grep -q "Up"; then
    echo "ERROR: Application containers are not running"
    exit 1
fi

# Check application health endpoint
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: Application health check failed"
    exit 1
fi

# Check database connectivity
if ! docker-compose -f /opt/seiketsu/docker-compose.yml exec -T seiketsu-app python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('Database connection: OK')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" > /dev/null 2>&1; then
    echo "ERROR: Database connection failed"
    exit 1
fi

# Check Redis connectivity
if ! docker-compose -f /opt/seiketsu/docker-compose.yml exec -T seiketsu-app python -c "
import redis
import os
try:
    r = redis.Redis(host=os.environ['REDIS_HOST'], port=6379, password=os.environ.get('REDIS_PASSWORD'))
    r.ping()
    print('Redis connection: OK')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
" > /dev/null 2>&1; then
    echo "ERROR: Redis connection failed"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "WARNING: Disk usage is $DISK_USAGE%"
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "WARNING: Memory usage is $MEM_USAGE%"
fi

echo "=== Health Check PASSED ==="
echo "Application is running normally"
echo "Database: Connected"
echo "Redis: Connected"
echo "Disk Usage: $DISK_USAGE%"
echo "Memory Usage: $MEM_USAGE%"
EOL

chmod +x /opt/seiketsu/health-check.sh

# Create startup script
cat > /opt/seiketsu/start.sh << 'EOL'
#!/bin/bash

# Startup script for Seiketsu AI application
set -e

CLIENT_ID="$1"
if [ -z "$CLIENT_ID" ]; then
    echo "Usage: $0 <client_id>"
    exit 1
fi

echo "=== Starting Seiketsu AI Application for Client: $CLIENT_ID ==="

cd /opt/seiketsu

# Pull latest images
echo "Pulling latest Docker images..."
docker-compose pull

# Start services
echo "Starting application services..."
docker-compose up -d

# Wait for application to be ready
echo "Waiting for application to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Application is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Application failed to start within 30 attempts"
        docker-compose logs
        exit 1
    fi
    echo "Attempt $i/30: Waiting for application..."
    sleep 10
done

echo "=== Application Started Successfully ==="
echo "Health endpoint: http://localhost:8000/health"
echo "Metrics endpoint: http://localhost:9090/metrics"
echo "Logs: docker-compose logs -f"
EOL

chmod +x /opt/seiketsu/start.sh

# Create stop script
cat > /opt/seiketsu/stop.sh << 'EOL'
#!/bin/bash

# Stop script for Seiketsu AI application
set -e

CLIENT_ID="$1"
if [ -z "$CLIENT_ID" ]; then
    echo "Usage: $0 <client_id>"
    exit 1
fi

echo "=== Stopping Seiketsu AI Application for Client: $CLIENT_ID ==="

cd /opt/seiketsu

# Stop services gracefully
echo "Stopping application services..."
docker-compose down --timeout 30

echo "=== Application Stopped Successfully ==="
EOL

chmod +x /opt/seiketsu/stop.sh

# Create systemd service
cat > /etc/systemd/system/seiketsu-${CLIENT_ID}.service << EOL
[Unit]
Description=Seiketsu AI Voice Agent for Client $CLIENT_ID
Requires=docker.service
After=docker.service
StartLimitIntervalSec=0

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/seiketsu
ExecStart=/opt/seiketsu/start.sh $CLIENT_ID
ExecStop=/opt/seiketsu/stop.sh $CLIENT_ID
TimeoutStartSec=300
TimeoutStopSec=60
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
systemctl daemon-reload
systemctl enable seiketsu-${CLIENT_ID}.service

# Create log rotation configuration
cat > /etc/logrotate.d/seiketsu-${CLIENT_ID} << EOL
/opt/seiketsu/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    create 644 root root
}
EOL

# Set up CloudWatch agent
echo "Setting up CloudWatch monitoring..."
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent service
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# Create deployment status file
cat > /opt/seiketsu/deployment-status.json << EOL
{
  "client_id": "$CLIENT_ID",
  "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "configured",
  "instance_id": "$(curl -s http://169.254.169.254/latest/meta-data/instance-id)",
  "region": "$(curl -s http://169.254.169.254/latest/meta-data/placement/region)",
  "availability_zone": "$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)",
  "instance_type": "$(curl -s http://169.254.169.254/latest/meta-data/instance-type)",
  "private_ip": "$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)",
  "public_ip": "$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)",
  "components": {
    "docker": "installed",
    "docker_compose": "installed",
    "cloudwatch_agent": "configured",
    "application": "ready_to_start",
    "health_checks": "configured",
    "monitoring": "enabled"
  }
}
EOL

# Create cron job for health checks
cat > /etc/cron.d/seiketsu-${CLIENT_ID}-health << EOL
# Health check every 5 minutes
*/5 * * * * root /opt/seiketsu/health-check.sh $CLIENT_ID >> /opt/seiketsu/logs/health-check.log 2>&1

# Daily log cleanup
0 2 * * * root find /opt/seiketsu/logs -name "*.log" -mtime +7 -delete

# Weekly system update check
0 3 * * 0 root yum check-update > /opt/seiketsu/logs/update-check.log 2>&1
EOL

# Set proper permissions
chown -R root:root /opt/seiketsu
chmod -R 755 /opt/seiketsu
chmod 600 /opt/seiketsu/.env

# Create initial log files
touch /opt/seiketsu/logs/app.log
touch /opt/seiketsu/logs/error.log
touch /opt/seiketsu/logs/health-check.log
chmod 644 /opt/seiketsu/logs/*.log

# Signal completion
echo "=== User Data Script Completed Successfully ==="
echo "Client Instance for $CLIENT_ID is ready for application deployment"
echo "Status file: /opt/seiketsu/deployment-status.json"
echo "Start command: systemctl start seiketsu-${CLIENT_ID}"
echo "Stop command: systemctl stop seiketsu-${CLIENT_ID}"
echo "Health check: /opt/seiketsu/health-check.sh $CLIENT_ID"
echo "Logs: tail -f /opt/seiketsu/logs/app.log"

# Update deployment status
cat > /opt/seiketsu/deployment-status.json << EOL
{
  "client_id": "$CLIENT_ID",
  "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "ready",
  "instance_id": "$(curl -s http://169.254.169.254/latest/meta-data/instance-id)",
  "region": "$(curl -s http://169.254.169.254/latest/meta-data/placement/region)",
  "availability_zone": "$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)",
  "instance_type": "$(curl -s http://169.254.169.254/latest/meta-data/instance-type)",
  "private_ip": "$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)",
  "public_ip": "$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)",
  "components": {
    "docker": "ready",
    "docker_compose": "ready",
    "cloudwatch_agent": "running",
    "application": "ready_to_start",
    "health_checks": "enabled",
    "monitoring": "active",
    "systemd_service": "enabled",
    "log_rotation": "configured"
  },
  "endpoints": {
    "health": "http://localhost:8000/health",
    "metrics": "http://localhost:9090/metrics",
    "logs": "/opt/seiketsu/logs/"
  }
}
EOL

echo "User data script execution completed at $(date)"