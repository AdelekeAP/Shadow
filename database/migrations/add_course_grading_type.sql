-- Migration: add Course.grading_type to support single-grade courses (e.g. Final Year Project)
--
-- 'standard_35_65' — PAU default: 35% Continuous Assessment + 65% Final Exam
-- 'single_grade'   — one final score out of 100 (thesis + defence + supervisor assessment);
--                    no CA/Exam split, no exam prediction. Grade point uses the 5.0 scale.
--
-- Idempotent: safe to run more than once.

ALTER TABLE courses
    ADD COLUMN IF NOT EXISTS grading_type VARCHAR(20) NOT NULL DEFAULT 'standard_35_65';

-- Final Year Project I & II are graded as a single score out of 100.
UPDATE courses
    SET grading_type = 'single_grade'
    WHERE code IN ('CSC497', 'CSC498');
