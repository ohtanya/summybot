module.exports = {
  apps: [{
    name: 'summybot',
    script: 'main.py',
    interpreter: '/opt/summybot/.venv/bin/python',
    cwd: '/opt/summybot',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '2G',
    restart_delay: 5000,
    max_restarts: 10,
    min_uptime: '10s',
    env: {
      PYTHONPATH: '/opt/summybot',
      PYTHONUNBUFFERED: '1',
      OPENAI_API_KEY: process.env.OPENAI_API_KEY
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    kill_timeout: 5000
  }]
};