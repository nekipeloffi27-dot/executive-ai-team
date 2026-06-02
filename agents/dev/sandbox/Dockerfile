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
RUN chmod +x /entrypoint.sh && chown -R node:node /workspace

# git дефолты на системном уровне — будут видны и под root, и под node
RUN git config --system user.email "dev-agent@exec-team.local" \
 && git config --system user.name  "Exec Team Dev Agent" \
 && git config --system init.defaultBranch main \
 && git config --system pull.rebase false \
 && git config --system core.autocrlf input

# Claude Code не разрешает --dangerously-skip-permissions под root,
# поэтому переключаемся на встроенного user 'node' (uid=1000, совпадает с ubuntu на host VM)
USER node
ENTRYPOINT ["/entrypoint.sh"]
