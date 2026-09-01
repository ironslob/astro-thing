# AWS production mapping

Not required to run the local MVP. This is the intended lift from Compose without rewriting the app.

| Concern | Local Compose | AWS |
| --- | --- | --- |
| Frontend | `frontend` nginx container | S3 + CloudFront, or the same container on ECS |
| API | `backend` | ECS Fargate service, ALB, `/health` |
| Worker / beat | `worker`, `beat` | Separate Fargate services (same image, different command) |
| PostgreSQL | `postgres` | RDS PostgreSQL with automated backups / PITR |
| Redis | `redis` | ElastiCache (broker + locks + rate limits; not source of truth) |
| Images | local build | ECR |
| Secrets | Compose environment | Secrets Manager / SSM |
| Logs | container stdout | CloudWatch |
| DNS / TLS | localhost:8080 | Route 53 + ACM |

Skeleton task definition (illustrative):

```json
{
  "family": "astro-window-api",
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/astro-window-backend:latest",
      "portMappings": [{ "containerPort": 8000 }],
      "environment": [{ "name": "ENVIRONMENT", "value": "production" }],
      "secrets": [
        { "name": "DATABASE_URL", "valueFrom": "arn:aws:ssm:REGION:ACCOUNT:parameter/astro/DATABASE_URL" },
        { "name": "SECRET_KEY", "valueFrom": "arn:aws:ssm:REGION:ACCOUNT:parameter/astro/SECRET_KEY" }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')\""]
      }
    }
  ]
}
```

Set `SESSION_COOKIE_SECURE=true` and `FRONTEND_BASE_URL` to the HTTPS origin. Keep `WeatherProvider` timeouts and the 60 req/min public forecast limit enabled.
