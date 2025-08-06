# Automated Financial Content Pipeline

## Phase 1: Data Collection & Storage

**Input:** News Sources RSS Feeds

**Process:** Research_Agent
- **Action:** Parse, Clean, Filter
- **Output:** Structured Data

**Process:** Database_Agent
- **Action:** INSERT & INDEX data
- **Core Component:** SQL Database

---

## Phase 2: Data Analysis & Processing

**Input:** SQL Database

**Process:** Analytics_Agent
- **Action:** Analyze & Score content
- **Output:** Prioritized Content List
- **Process:** Store analysis metadata back into SQL Database

---

## Phase 3: Content Creation & Localization

**Input:** SQL Database

**Process:** Extractor_Agent
- **Action:** Extract key facts, quotes, and data
- **Output:** Structured Content Elements

**Process:** Writer_Agent
- **Action:** Generate draft article in Chinese
- **Output:** Draft Articles

**Process:** Localization_Agent
- **Action:** Cultural review & SEO enhancement
- **Output:** Finalized Content

---

## Phase 4: Visuals & Formatting

**Input 1:** Finalized Content  
**Input 2:** SQL Database

**Process:** Designer_Agent
- **Action:** Create charts & images from market data
- **Output:** Visual Assets

**Process:** Formatter_Agent
- **Action:** Combine text and visuals for Ghost CMS
- **Output:** Ghost-Ready Post

---

## Phase 5: Publication & Analytics

**Input:** Ghost-Ready Post

**Process:** Publisher_Agent
- **Action 1:** Push content to Ghost CMS API
- **Action 2:** Log publication status to SQL Database
- **Output:** Live Post on Ghost CMS

**Process:** Monitor_Agent
- **Action:** Track engagement and user behavior
- **Output:** Performance Metrics
- **Process:** Store performance metrics back into SQL Database (Feedback Loop)