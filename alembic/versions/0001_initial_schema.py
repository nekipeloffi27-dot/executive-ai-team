"""initial schema for executive-ai-team v3

Revision ID: 0001
Revises:
Create Date: 2026-06-01

"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── features ─────────────────────────────────────────────
    op.execute("""
        CREATE TABLE features (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_slug TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'clarification',
            mode TEXT NOT NULL DEFAULT 'new',  -- 'new' or 'edit'
            context JSONB NOT NULL DEFAULT '{}'::jsonb,
            budget_cap_cents INTEGER NOT NULL DEFAULT 500,
            budget_used_cents INTEGER NOT NULL DEFAULT 0,
            tg_thread_id INTEGER,  -- Telegram topic message_thread_id
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            cancelled_at TIMESTAMPTZ,
            deployed_at TIMESTAMPTZ
        );
        CREATE INDEX idx_features_state ON features (state);
        CREATE INDEX idx_features_project ON features (project_slug);
    """)

    # ─── tasks ────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            feature_id UUID NOT NULL REFERENCES features(id) ON DELETE CASCADE,
            type TEXT NOT NULL,            -- backend / frontend_web / frontend_mobile
            status TEXT NOT NULL DEFAULT 'pending',
            complexity TEXT NOT NULL DEFAULT 'medium',  -- simple / medium / complex
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            -- готовый план от CTO для dev-агента (минимизирует tool calls в sandbox)
            affected_files JSONB NOT NULL DEFAULT '[]'::jsonb,
            changes_per_file JSONB NOT NULL DEFAULT '[]'::jsonb,
            acceptance_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
            api_contract JSONB,
            pr_url TEXT,
            pr_number INTEGER,
            branch_name TEXT,
            cto_review_verdict TEXT,        -- approve / request_changes
            cto_review_comments TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_tasks_feature ON tasks (feature_id);
        CREATE INDEX idx_tasks_status ON tasks (status);
    """)

    # ─── agent_calls (audit) ─────────────────────────────────
    op.execute("""
        CREATE TABLE agent_calls (
            id BIGSERIAL PRIMARY KEY,
            feature_id UUID REFERENCES features(id) ON DELETE SET NULL,
            task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            thread_id UUID,  -- discussion_threads(id), FK nullable so we don't enforce order
            agent_role TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            cache_creation_tokens INTEGER NOT NULL DEFAULT 0,
            cache_read_tokens INTEGER NOT NULL DEFAULT 0,
            cost_cents NUMERIC(10,2) NOT NULL DEFAULT 0,
            duration_ms INTEGER NOT NULL DEFAULT 0,
            iterations INTEGER NOT NULL DEFAULT 1,  -- сколько tool-use итераций было
            success BOOLEAN NOT NULL DEFAULT TRUE,
            error TEXT,
            operation_kind TEXT,  -- 'agentic', 'one_shot', 'reflection', 'router'
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_agent_calls_role ON agent_calls (agent_role);
        CREATE INDEX idx_agent_calls_feature ON agent_calls (feature_id);
        CREATE INDEX idx_agent_calls_thread ON agent_calls (thread_id);
        CREATE INDEX idx_agent_calls_created ON agent_calls (created_at DESC);
    """)

    # ─── cost_attributions (агрегат для бюджет-отчётов) ──────
    op.execute("""
        CREATE TABLE cost_attributions (
            id BIGSERIAL PRIMARY KEY,
            project_slug TEXT NOT NULL,
            agent_role TEXT NOT NULL,
            feature_id UUID REFERENCES features(id) ON DELETE SET NULL,
            task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            thread_id UUID,
            operation_kind TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cost_cents NUMERIC(10,2) NOT NULL,
            criticality TEXT NOT NULL,  -- 'critical' / 'non_critical'
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_cost_attr_project ON cost_attributions (project_slug);
        CREATE INDEX idx_cost_attr_role ON cost_attributions (agent_role);
        CREATE INDEX idx_cost_attr_created ON cost_attributions (created_at DESC);
    """)

    # ─── budget_caps (конфигурируемый бюджет) ────────────────
    op.execute("""
        CREATE TABLE budget_caps (
            id SERIAL PRIMARY KEY,
            project_slug TEXT NOT NULL UNIQUE,
            monthly_cap_cents INTEGER NOT NULL DEFAULT 15000,
            hard_stop_pct INTEGER NOT NULL DEFAULT 80,
            default_feature_cap_cents INTEGER NOT NULL DEFAULT 500,
            default_thread_cap_cents INTEGER NOT NULL DEFAULT 100,
            researcher_weekly_cap_cents INTEGER NOT NULL DEFAULT 1500,
            curator_weekly_cap_cents INTEGER NOT NULL DEFAULT 1000,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # ─── decisions (CEO решения с обоснованием) ──────────────
    op.execute("""
        CREATE TABLE decisions (
            id SERIAL PRIMARY KEY,
            project_slug TEXT NOT NULL,
            topic TEXT NOT NULL,
            decision TEXT NOT NULL,
            rationale TEXT,
            status TEXT NOT NULL DEFAULT 'active',  -- active / superseded / reverted
            supersedes INTEGER REFERENCES decisions(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_decisions_project ON decisions (project_slug);
        CREATE INDEX idx_decisions_status ON decisions (status);
    """)

    # ─── roadmap_items ────────────────────────────────────────
    op.execute("""
        CREATE TABLE roadmap_items (
            id SERIAL PRIMARY KEY,
            project_slug TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            phase TEXT,  -- 'phase_0', 'phase_1', 'phase_2', ...
            priority INTEGER NOT NULL DEFAULT 100,
            status TEXT NOT NULL DEFAULT 'proposed',  -- proposed / accepted / in_progress / done / dropped
            proposed_by TEXT,  -- agent_role
            estimated_cost_cents INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            decided_at TIMESTAMPTZ
        );
        CREATE INDEX idx_roadmap_project ON roadmap_items (project_slug);
        CREATE INDEX idx_roadmap_status ON roadmap_items (status);
    """)

    # ─── discussion_threads (Thread Engine) ──────────────────
    op.execute("""
        CREATE TABLE discussion_threads (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_slug TEXT NOT NULL,
            topic TEXT NOT NULL,
            initial_question TEXT NOT NULL,
            opened_by TEXT NOT NULL,  -- 'ceo' or agent_role
            participants JSONB NOT NULL DEFAULT '[]'::jsonb,  -- list of agent_roles
            status TEXT NOT NULL DEFAULT 'open',
            mode TEXT NOT NULL DEFAULT 'default',  -- default / deep
            max_rounds INTEGER NOT NULL DEFAULT 3,
            max_messages INTEGER NOT NULL DEFAULT 8,
            budget_cap_cents INTEGER NOT NULL DEFAULT 100,
            budget_used_cents INTEGER NOT NULL DEFAULT 0,
            rounds_completed INTEGER NOT NULL DEFAULT 0,
            messages_count INTEGER NOT NULL DEFAULT 0,
            tg_thread_id INTEGER,
            related_feature_id UUID REFERENCES features(id) ON DELETE SET NULL,
            -- финальная сводка от Chief of Staff после исчерпания
            ceo_options JSONB,
            ceo_decision TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            decided_at TIMESTAMPTZ
        );
        CREATE INDEX idx_threads_status ON discussion_threads (status);
        CREATE INDEX idx_threads_project ON discussion_threads (project_slug);
    """)

    # ─── thread_messages ──────────────────────────────────────
    op.execute("""
        CREATE TABLE thread_messages (
            id BIGSERIAL PRIMARY KEY,
            thread_id UUID NOT NULL REFERENCES discussion_threads(id) ON DELETE CASCADE,
            author TEXT NOT NULL,  -- 'ceo' or agent_role
            content TEXT NOT NULL,
            citations JSONB NOT NULL DEFAULT '[]'::jsonb,  -- ссылки на decisions, research, etc
            is_summary BOOLEAN NOT NULL DEFAULT FALSE,  -- финальная сводка от Chief of Staff
            round_number INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_thread_msgs_thread ON thread_messages (thread_id);
    """)

    # ─── agent_reflections (self-improvement loop) ───────────
    op.execute("""
        CREATE TABLE agent_reflections (
            id BIGSERIAL PRIMARY KEY,
            agent_role TEXT NOT NULL,
            feature_id UUID REFERENCES features(id) ON DELETE SET NULL,
            task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            thread_id UUID REFERENCES discussion_threads(id) ON DELETE SET NULL,
            task_description TEXT NOT NULL,
            went_well TEXT,
            uncertain_about TEXT,
            knowledge_gap TEXT,
            would_do_differently TEXT,
            outcome TEXT NOT NULL DEFAULT 'completed',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_reflections_role ON agent_reflections (agent_role);
        CREATE INDEX idx_reflections_created ON agent_reflections (created_at DESC);
    """)

    # ─── quality_signals (без LLM) ────────────────────────────
    op.execute("""
        CREATE TABLE quality_signals (
            id BIGSERIAL PRIMARY KEY,
            kind TEXT NOT NULL,         -- redo_design / fail_test / cto_request_changes / ceo_feedback / budget_overrun
            target_agent_role TEXT NOT NULL,
            content TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'medium',  -- low / medium / high
            source TEXT NOT NULL,       -- 'ceo' or agent_role
            feature_id UUID REFERENCES features(id) ON DELETE SET NULL,
            task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_quality_role ON quality_signals (target_agent_role);
        CREATE INDEX idx_quality_kind ON quality_signals (kind);
        CREATE INDEX idx_quality_created ON quality_signals (created_at DESC);
    """)

    # ─── skill_proposals ──────────────────────────────────────
    op.execute("""
        CREATE TABLE skill_proposals (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            target_agent_role TEXT NOT NULL,
            rationale TEXT NOT NULL,
            draft_content TEXT NOT NULL,
            estimated_cost_impact_cents INTEGER,  -- сколько +/- на одну фичу
            evidence_reflection_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            evidence_signal_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            status TEXT NOT NULL DEFAULT 'proposed',
            decided_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_skill_proposals_status ON skill_proposals (status);
    """)

    # ─── research_findings ────────────────────────────────────
    op.execute("""
        CREATE TABLE research_findings (
            id BIGSERIAL PRIMARY KEY,
            project_slug TEXT NOT NULL,
            source TEXT NOT NULL,           -- 'researcher_agent', 'ceo', 'external_url'
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            relevance_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
            url TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_findings_project ON research_findings (project_slug);
        CREATE INDEX idx_findings_created ON research_findings (created_at DESC);
    """)

    # ─── state_transitions (audit для state machine) ──────────
    op.execute("""
        CREATE TABLE state_transitions (
            id BIGSERIAL PRIMARY KEY,
            feature_id UUID NOT NULL REFERENCES features(id) ON DELETE CASCADE,
            from_state TEXT,
            to_state TEXT NOT NULL,
            triggered_by TEXT NOT NULL,  -- 'ceo' or agent_role or 'system'
            reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_transitions_feature ON state_transitions (feature_id);
    """)

    # ─── ceo_pending_decisions ────────────────────────────────
    # Decisions Required dashboard
    op.execute("""
        CREATE TABLE ceo_pending_decisions (
            id SERIAL PRIMARY KEY,
            project_slug TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            urgency TEXT NOT NULL DEFAULT 'normal',  -- low / normal / high / urgent
            related_thread_id UUID REFERENCES discussion_threads(id) ON DELETE SET NULL,
            related_feature_id UUID REFERENCES features(id) ON DELETE SET NULL,
            choices JSONB NOT NULL DEFAULT '[]'::jsonb,  -- варианты выбора с описаниями
            proposed_by TEXT NOT NULL,
            decided BOOLEAN NOT NULL DEFAULT FALSE,
            ceo_choice TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            decided_at TIMESTAMPTZ
        );
        CREATE INDEX idx_pending_project ON ceo_pending_decisions (project_slug);
        CREATE INDEX idx_pending_undecided ON ceo_pending_decisions (decided) WHERE decided = FALSE;
    """)

    # ─── Pre-seeded budget_caps for moy-kosmetolog ───────────
    op.execute("""
        INSERT INTO budget_caps (project_slug, monthly_cap_cents, hard_stop_pct, default_feature_cap_cents, default_thread_cap_cents)
        VALUES ('moy-kosmetolog', 15000, 80, 500, 100)
        ON CONFLICT DO NOTHING;
    """)

    # ─── Pre-seeded 7 CEO decisions ──────────────────────────
    op.execute("""
        INSERT INTO decisions (project_slug, topic, decision, rationale, status) VALUES
        ('moy-kosmetolog', 'MVP target audience',
         'Портреты 1-2 (Алина 24, Денис 19) — молодая аудитория с проблемами кожи. Записи мастеров в MVP нет.',
         'Портреты 3-5 — Phase 2.',
         'active'),
        ('moy-kosmetolog', 'North Star and phased KPIs',
         '100K MAU за 12 мес от soft launch (аспирация). Phase 1 (+3 мес) = 1K MAU, Phase 2 (+9 мес) = 10K. MAU = авторизованный + ≥1 действие в месяц.',
         'Разделение аспирации и рабочей цели. Пересмотр каждый квартал.',
         'active'),
        ('moy-kosmetolog', 'AI team budget cap',
         'Жёсткий cap $150/мес. Hard-stop при 80%. Конфигурируется через budget_caps в БД.',
         'Ранняя стадия. Маркетинг — отдельный бюджет.',
         'active'),
        ('moy-kosmetolog', 'UVP (working hypothesis)',
         'Против Lóvi: РФ-фокус, русский, PWA, тон сообщества, монетизация подписка + affiliate.',
         'Гипотеза. Researcher валидирует в Phase 1.',
         'active'),
        ('moy-kosmetolog', 'Product brand name',
         'Мой Косметолог. Возможен ребрендинг к запуску.',
         'Рабочее имя. Open question для команды.',
         'active'),
        ('moy-kosmetolog', 'Monetization model (MVP)',
         'Подписка (основная) + affiliate с маркетплейсами (Wildberries, Ozon, Золотое Яблоко). Прямые покупки в MVP не реализуем.',
         'Фокус MVP на ценности продукта, не e-commerce. Сэкономит интеграции с СБП/логистикой/складом.',
         'active'),
        ('moy-kosmetolog', 'Authentication wall on scan result (OPEN)',
         'Текущий сценарий — auth после скана (шаг 3). Открыт thread для обсуждения альтернатив (Lóvi-модель с quiz перед auth).',
         'Потенциальное узкое место конверсии. Команда обсудит как первый живой тест Thread Engine.',
         'active');
    """)

    # ─── Pre-seeded pending decision для wall-авторизации ────
    op.execute("""
        INSERT INTO ceo_pending_decisions (project_slug, title, description, urgency, choices, proposed_by, decided)
        VALUES (
          'moy-kosmetolog',
          'Wall авторизации на шаге 3 — обсудить с командой',
          'Текущий клиентский сценарий шага 3: после скана → результат с проблемами кожи → CTA "Подобрать уход" + auth wall. Альтернатива (Lóvi-модель): quiz → инвестиция времени → auth позже когда уже emotional attachment. Какой подход выбрать для MVP?',
          'high',
          '[{"key": "open_thread", "label": "Открыть thread с Designer + Strategist + CTO для обсуждения"}, {"key": "keep_current", "label": "Оставить текущий сценарий, валидировать на A/B потом"}, {"key": "switch_to_quiz", "label": "Сразу перейти на quiz-first как у Lóvi"}]'::jsonb,
          'system',
          FALSE
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ceo_pending_decisions CASCADE;")
    op.execute("DROP TABLE IF EXISTS state_transitions CASCADE;")
    op.execute("DROP TABLE IF EXISTS research_findings CASCADE;")
    op.execute("DROP TABLE IF EXISTS skill_proposals CASCADE;")
    op.execute("DROP TABLE IF EXISTS quality_signals CASCADE;")
    op.execute("DROP TABLE IF EXISTS agent_reflections CASCADE;")
    op.execute("DROP TABLE IF EXISTS thread_messages CASCADE;")
    op.execute("DROP TABLE IF EXISTS discussion_threads CASCADE;")
    op.execute("DROP TABLE IF EXISTS roadmap_items CASCADE;")
    op.execute("DROP TABLE IF EXISTS decisions CASCADE;")
    op.execute("DROP TABLE IF EXISTS budget_caps CASCADE;")
    op.execute("DROP TABLE IF EXISTS cost_attributions CASCADE;")
    op.execute("DROP TABLE IF EXISTS agent_calls CASCADE;")
    op.execute("DROP TABLE IF EXISTS tasks CASCADE;")
    op.execute("DROP TABLE IF EXISTS features CASCADE;")
