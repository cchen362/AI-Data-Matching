
# Product Requirements Document (PRD)
## Vendor–Client Matching & Analysis Tool

### 1. Overview
This project aims to build a lightweight **Streamlit web application** that allows sourcing and commercial teams to upload vendor (Raindrop contracts) and client/opportunity (Salesforce exports) files, automatically detect overlaps, and present a consolidated view of companies that are both vendors and clients. The app should generate interactive tables, charts, and downloadable reports (HTML and Excel).

---

### 2. Objectives
- Provide a **single view** of companies who are both vendors and clients/opportunities.
- Allow teams to see:  
  - How much we **spend as a vendor**.  
  - How much they **spend as a client/opportunity**.  
  - **Contract details** (terms, end dates, stage if opportunity).  
- Normalize currencies into **USD**.  
- Enable **interactive exploration** (full table with filters).  
- Allow **downloadable reports** (full dataset or filtered view).  

---

### 3. Scope
#### In Scope
- Upload and process **Raindrop contract list (main file)**.  
- Upload and process **client & opportunity files**:  
  - EGE Active Customers  
  - EGE Active Opportunities  
  - BT Active Clients  
  - BT Opportunity Pipeline  
- Normalize schemas (map differing column names).  
- Currency conversion via **free live FX API**.  
- Company name matching using **fuzzy matching** with strict threshold.  
- Consolidate **client spend across sources** if same company exists.  
- Output in **USD only**.  
- Generate interactive charts & tables in-app.  
- Allow **HTML + Excel downloads** (full dataset or filtered subset).  

#### Out of Scope
- API integrations with Raindrop or Salesforce (future phase).  
- Authentication/SSO.  
- Large-scale database backend (initially in-memory pandas).  

---

### 4. Users
- **Primary Users**: Sourcing & Commercial team members.  
- **Usage Context**: Ad-hoc analysis for strategic insights, vendor-client negotiations, and identifying cross-relationships.  

---

### 5. Functional Requirements

#### File Handling
- Accept multiple file formats: `.csv`, `.xlsx`, `.xls`.  
- Detect file type based on **column headers** (not filenames).  
- Normalize column names (with LLM-assisted suggestions).  

#### Data Processing
- **Main File (Raindrop contracts)**  
  - Columns: `Company Name`, `Total Value + Currency`, `Terms (Mos)`, `End Date`.  
- **EGE Active Customers**  
  - If `Ultimate Parent Account (read only)` exists → group all `Contracted Annual Travel Budget + Currency`.  
  - Else → take row value.  
  - Convert all to USD.  
- **EGE Active Opportunities**  
  - Group `Corporate Gross Bookings Value in USD` by `Ultimate Parent Account (read only)` if available.  
  - Flag as **opportunity** (no contract term).  
  - Capture `Stage` column.  
- **BT Active Clients**  
  - Group `Expected Total Travel Volume + Currency` by `Ultimate Parent Name` if available.  
  - Else → take row value.  
  - Convert to USD.  
- **BT Opportunity Pipeline**  
  - Group `Expected Total Travel Volume (converted)` by `Ultimate Parent Name` if available.  
  - Else → take row value.  
  - Flag as **opportunity**.  
  - Capture `Stage` column.  

#### Matching Logic
- Match **Raindrop vendors vs Clients/Opportunities** using fuzzy matching.  
- Threshold set conservatively (to avoid Qualcomm vs Qualtrics errors).  
- If multiple client sources contain same company → consolidate into one "Client Spend".  

#### Outputs
- **Consolidated Table** showing:  
  - Company Name  
  - Vendor Spend (USD)  
  - Vendor Contract End Date  
  - Vendor Contract Term (Mos)  
  - Client Spend (USD)  
  - Client Contract Term (if applicable)  
  - Opportunity Stage (if applicable)  
- **Interactive Charts**:  
  - Top 10 overlaps by spend.  
  - Contract expiry timelines.  
- **Download Options**:  
  - Full Report (all matches).  
  - Current View (filtered subset).  
  - Formats: HTML (styled) + Excel.  

#### User Interactions
- Upload files (main + client).  
- See full comparison table.  
- Apply filters/search to drill down.  
- Generate charts from filtered view.  
- Download report (full or filtered).  

---

### 6. Non-Functional Requirements
- Handle datasets of:  
  - Raindrop contracts: ~5,500 rows.  
  - Client files: 2,500 – 28,000 rows each.  
- App performance: < 5 seconds for typical uploads.  
- Enterprise-style UI (no emojis, clean CSS).  
- Lightweight (Streamlit app, Python + Pandas backend).  

---

### 7. Tech Stack
- **Frontend/UI**: Streamlit.  
- **Backend/Processing**: Python (Pandas, RapidFuzz, Requests).  
- **Currency Conversion**: Free API (e.g., exchangerate.host).  
- **LLM**: OpenAI API (GPT) for Q&A + schema mapping.  
- **Visualization**: Plotly (interactive).  
- **Export**: Pandas → HTML (Jinja2 template, styled) & Excel.  

---

### 8. Architecture Flow
1. User uploads files.  
2. System detects file types via column headers.  
3. Normalize schemas (LLM assist).  
4. Convert values to USD (via API).  
5. Match vendors vs clients (fuzzy match).  
6. Consolidate client spend if multiple sources.  
7. Generate consolidated table.  
8. Render interactive charts.  
9. Allow downloads (full or filtered).  

---

### 9. Roadmap
**Phase 1 (MVP)**  
- File uploads.  
- Schema detection + normalization.  
- USD conversion.  
- Vendor-client matching.  
- Consolidated table.  
- Interactive charts.  
- HTML + Excel downloads.  

**Phase 2**  
- LLM-powered natural language queries.  
- LLM column-mapping suggestions.  
- Save user-defined mapping preferences.  

**Phase 3**  
- Persistent database (Postgres).  
- Authentication (SSO).  
- API integrations (Raindrop + Salesforce).  

---

### 10. Open Questions
- Should we allow manual override for fuzzy matches (review screen)?  
- Should the HTML report include embedded logos/branding for stakeholder presentations?  
