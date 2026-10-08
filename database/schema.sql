-- ===================================================
-- LogicEval-AI Database Schema
-- CBSE Class 12 AI-Assisted Coding Logic Tutor
-- ===================================================

CREATE DATABASE IF NOT EXISTS codelogic_db;
USE codelogic_db;

-- ---------------------------------------------------
-- 1. User Information Table (Authentication & Progress)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS userinfo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    currentq INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------
-- 2. Questions Repository
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_text TEXT NOT NULL,
    reference_answer TEXT,
    difficulty VARCHAR(50) DEFAULT 'Medium',
    topic VARCHAR(100) DEFAULT 'Python Basics'
);
