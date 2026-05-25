"""Tech skill keyword dictionary grouped by category."""

SKILL_DICT: dict[str, list[str]] = {
    "languages": [
        "python", "java", "javascript", "typescript", "go", "rust", "c", "c++", "c#",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "shell",
        "bash", "powershell", "haskell", "elixir", "erlang", "clojure", "groovy",
        "dart", "lua", "julia", "fortran", "cobol", "assembly", "vhdl", "verilog",
        "objective-c", "f#", "ocaml", "prolog", "lisp", "scheme",
    ],
    "frameworks": [
        "react", "vue", "angular", "svelte", "nextjs", "nuxt", "gatsby", "remix",
        "fastapi", "django", "flask", "tornado", "aiohttp", "starlette",
        "spring", "spring boot", "hibernate", "struts", "jsf",
        "express", "nestjs", "koa", "hapi", "fastify",
        "rails", "sinatra", "phoenix", "ecto",
        "laravel", "symfony", "codeigniter",
        "asp.net", "asp.net core", "blazor", "xamarin", "maui",
        "gin", "echo", "fiber",
        "actix", "axum", "rocket",
        "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost", "lightgbm",
        "hugging face", "transformers", "langchain", "llama index",
        "hadoop", "spark", "flink", "kafka streams",
        "react native", "flutter", "ionic",
        "tailwind", "bootstrap", "material ui", "chakra ui", "shadcn",
        "graphql", "apollo", "relay",
        "redux", "zustand", "mobx", "recoil",
        "prisma", "typeorm", "sequelize", "sqlalchemy", "peewee",
        "celery", "dramatiq", "rq",
        "pytest", "jest", "mocha", "cypress", "playwright", "selenium",
        "pydantic", "marshmallow", "zod",
    ],
    "tools": [
        "docker", "kubernetes", "helm", "istio", "envoy",
        "git", "github", "gitlab", "bitbucket", "mercurial",
        "aws", "gcp", "azure", "digitalocean", "heroku", "vercel", "netlify",
        "terraform", "ansible", "chef", "puppet", "saltstack",
        "jenkins", "github actions", "gitlab ci", "circleci", "travis ci", "drone",
        "prometheus", "grafana", "datadog", "new relic", "splunk", "elk stack",
        "elasticsearch", "logstash", "kibana", "opensearch",
        "nginx", "apache", "caddy", "haproxy",
        "redis", "memcached", "rabbitmq", "kafka", "nats", "pulsar",
        "postgresql", "mysql", "mariadb", "sqlite", "oracle", "mssql",
        "mongodb", "cassandra", "dynamodb", "couchdb", "firebase",
        "snowflake", "bigquery", "redshift", "databricks", "dbt",
        "airflow", "prefect", "dagster", "luigi",
        "linux", "ubuntu", "centos", "debian", "alpine",
        "vscode", "intellij", "eclipse", "vim", "emacs",
        "jira", "confluence", "notion", "slack", "figma",
        "postman", "swagger", "openapi",
        "webpack", "vite", "parcel", "rollup", "esbuild",
        "npm", "yarn", "pnpm", "pip", "poetry", "conda",
        "jupyter", "colab", "databricks notebooks",
        "s3", "ec2", "lambda", "rds", "ecs", "eks",
        "cloudflare", "fastly", "akamai",
        "opencv", "ffmpeg",
        "llm", "ollama", "openai api", "anthropic api",
    ],
    "concepts": [
        "rest api", "restful", "graphql", "grpc", "websocket", "webhook",
        "microservices", "monolith", "serverless", "event-driven", "event sourcing",
        "cqrs", "domain-driven design", "ddd", "clean architecture", "hexagonal architecture",
        "ci/cd", "devops", "gitops", "sre", "platform engineering",
        "agile", "scrum", "kanban", "sprint", "tdd", "bdd",
        "design patterns", "solid principles", "dry", "kiss", "yagni",
        "oauth", "jwt", "saml", "sso", "rbac", "abac",
        "encryption", "ssl/tls", "https", "cryptography",
        "sql", "nosql", "newql", "acid", "cap theorem", "eventual consistency",
        "sharding", "replication", "caching", "cdn",
        "load balancing", "rate limiting", "circuit breaker", "service mesh",
        "machine learning", "deep learning", "nlp", "computer vision",
        "data pipeline", "etl", "elt", "data modeling", "data warehouse",
        "feature engineering", "model training", "model deployment", "mlops",
        "rag", "vector search", "embeddings", "prompt engineering",
        "a/b testing", "feature flags", "canary deployment", "blue-green deployment",
        "distributed systems", "consensus", "raft", "paxos",
        "api gateway", "service discovery", "message queue",
        "observability", "tracing", "logging", "monitoring",
        "responsive design", "accessibility", "web performance", "core web vitals",
        "unit testing", "integration testing", "e2e testing", "code review",
        "technical debt", "refactoring", "code quality", "static analysis",
        "infrastructure as code", "immutable infrastructure",
    ],
}

SKILL_SET: frozenset[str] = frozenset(
    skill.lower()
    for skills in SKILL_DICT.values()
    for skill in skills
)

_REVERSE_INDEX: dict[str, str] = {
    skill.lower(): category
    for category, skills in SKILL_DICT.items()
    for skill in skills
}


def get_category(skill: str) -> str | None:
    return _REVERSE_INDEX.get(skill.lower())
