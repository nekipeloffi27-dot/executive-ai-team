FROM node:20-bookworm

# ─── System deps ─────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    jq \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# ─── Claude Code CLI ─────────────────────────────────────────
RUN npm install -g @anthropic-ai/claude-code

# ─── GitHub CLI ──────────────────────────────────────────────
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh && rm -rf /var/lib/apt/lists/*

# ─── pnpm и Python для возможных backend задач ───────────────
RUN npm install -g pnpm
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# ─── Proxy конфиг (зашит в образ, не через env) ──────────────
# Если build-arg ANTHROPIC_PROXY_URL пустой — proxy просто не используется
ARG ANTHROPIC_PROXY_URL=""
ENV BAKED_PROXY_URL=${ANTHROPIC_PROXY_URL}

# ─── Entrypoint ──────────────────────────────────────────────
WORKDIR /workspace
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# git дефолты, чтобы не было сюрпризов
RUN git config --global user.email "dev-agent@exec-team.local" \
 && git config --global user.name  "Exec Team Dev Agent" \
 && git config --global init.defaultBranch main \
 && git config --global pull.rebase false \
 && git config --global core.autocrlf input

ENTRYPOINT ["/entrypoint.sh"]
