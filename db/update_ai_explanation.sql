-- Add ai_explanation column to tickets table
-- If JSON is not supported by the current MySQL version, it should be changed to TEXT.
ALTER TABLE `tickets` 
ADD COLUMN `ai_explanation` JSON NULL AFTER `escalation_required`;

-- Verification
DESCRIBE `tickets`;
