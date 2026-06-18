CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL,
    description text,
    start_time timestamptz,
    end_time timestamptz,
    priority text NOT NULL DEFAULT 'medium',
    status text NOT NULL DEFAULT 'pending',
    reminder_time timestamptz,
    recurring_rule text,
    reminded boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT tasks_priority_check CHECK (priority IN ('low', 'medium', 'high')),
    CONSTRAINT tasks_status_check CHECK (status IN ('pending', 'done', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_command text,
    intent text NOT NULL,
    before_data jsonb,
    after_data jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT operation_logs_intent_check CHECK (
        intent IN (
            'create_task',
            'update_task',
            'delete_task',
            'query_schedule',
            'complete_task',
            'set_recurring_task',
            'check_reminders',
            'daily_summary'
        )
    )
);

CREATE TABLE IF NOT EXISTS reminders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    send_time timestamptz NOT NULL,
    channel text NOT NULL DEFAULT 'telegram',
    status text NOT NULL DEFAULT 'pending',
    sent_at timestamptz,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT reminders_channel_check CHECK (
        channel IN ('telegram', 'email', 'bark', 'wechat_work', 'dingtalk')
    ),
    CONSTRAINT reminders_status_check CHECK (status IN ('pending', 'sent', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_start_time ON tasks(start_time);
CREATE INDEX IF NOT EXISTS idx_tasks_reminder_time ON tasks(reminder_time);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_reminded ON tasks(reminded);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at ON operation_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_operation_logs_intent ON operation_logs(intent);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, send_time);
CREATE INDEX IF NOT EXISTS idx_reminders_task_id ON reminders(task_id);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_tasks_updated_at ON tasks;
CREATE TRIGGER trg_tasks_updated_at
BEFORE UPDATE ON tasks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_reminders_updated_at ON reminders;
CREATE TRIGGER trg_reminders_updated_at
BEFORE UPDATE ON reminders
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
