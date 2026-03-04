-- Migration to add metrics columns to automation_templates table
ALTER TABLE automation_templates ADD COLUMN trigger_app VARCHAR;
ALTER TABLE automation_templates ADD COLUMN action_apps JSON;
ALTER TABLE automation_templates ADD COLUMN complexity_score INTEGER;
ALTER TABLE automation_templates ADD COLUMN maintenance_level VARCHAR;
ALTER TABLE automation_templates ADD COLUMN monthly_opex FLOAT;
