# AI BUSINESS ANALYTICS DASHBOARD

A full-stack web application that lets a business upload a sales CSV or Excel file and instantly get back revenue trends, best selling productsm, key metrices, and AI generated business recommendations.

Built to demonstrate a complete data pipline from raw file upload, through ata analysis and visualisation, to an LLM powered insights layer all in Python.

---
## Features

- **File upload** -which accepts .csv and .xlsx sales data, inclduing multiple files at once merged for single analysis
- **External data imports** -pulls sales data directly from Stripe, Shopify, or public Google Sheet instead of uploading a file
- **Column mapping** -if your file's columns don't match the expected names, a mapping step lets you tell which column means what, instead of failing outright
- **Automated analysis** - pandas calculations of total revenue, average order value, best selling products, and monthly revene trends, revenue growth %, busiest month/day of week, unique customers, refund rate, and anomaly detection (statistical outliers flagged automatically)
- **Charts** -Plotly- generated revenue and sales visualisations
- **Export** - download any report as CSV or PDF
- **Persistent** storage -every uploaded report is saved to a SQLite database via sql alchemy
- **AI Recommendation** - Google Gemini API analyses the results and generates specific actionable business recommendations, with an explicit low confidence note when the sample size is small
- **Chat with your data** - ask free-form follow up questions about a specific report. Answers are grounded only in that reports stored summary (not the raw file), so the model won't invent mnumbers
- **Workspaces + team access** -separate multiple businesses/shops into their own workspace, and invite other registered users to view and work with the same reports.
- **Polished web user interface** -currently allow upload file then analyses and view results. Dark navy dashboard built with custom CSS and Inter topology. Contains animated metric cards, fade in transitions and responsive layout
- **User authentication** -register and login with email and password; the passwords are bcrypt-hashed, sessions are JWT-based
- **Protected everything** -every upload, report, workspace, and ation is tied to the logged-in user; unauthorised requests are rejected

---

## Tech Stack
| Layer          | Technology                        |
|----------------|-----------------------------------|
| Backend        | Python, FastApi                   |
| Data Analysis  | Pandas                            |
| Visualisation  | Plotly                            |
| Database       | SQLite, SQLAlchemy                |
| Integrations   | Stripe API,Shopify Admin API,Google Sheets|
| Email          | smtplib + APScheduler             |
| PDF export     | ReportLab                         |
| AI             | Google Gemini API                 |
| Frontend       | HTML, JAVASCRPT (FETCH API)       |
| Authentication | JWT(python jose), bcrypt(passlib) |

---

## How it works
    
1. User registers or logs in -a JWT access token is returned and stored in browser
2. From the Dashboard, the user uploads a CSV/EXCEL file through web interface
3. Fast API receives the file, verifies the token and identifies the logged-in user 
4. The file is loaded into a pandas dataframe for analysis. Revenue is calculated automatically if it is not present.
5. The analysis module calculates revenue, top products and trends/ if no revenue it finds it using product and cost
6. Plotly generates chart data from the results
7. Report saved in SQLite
8. The summary statistics are sent to the Gemini API, which returns three tailor business recommendations
9. Results-including the AI recommendations are returned to the browser and displayed.
10. Anyone invited to a workspace sees the same reports ast the owner

---

## Project structure

```
business-dashboard/
|-- app/
|   |-- __init__.py
|   |-- access.py
|   |-- admin_routes.py
|   |-- ai_recommendatio.py 
|   |-- analytics.py
|   |-- auth.py
|   |-- auth_routes.py
|   |-- business_routes.py
|   |-- email_utils.py
|   |-- integration_routes.py
|   |-- dashboard.db
|   |-- debug_test.py 
|   |-- main.py
|   |-- models.py
|   |-- routes.py 
|-- static/
|   |-- style.css 
|   |-- js/
|   |   |-- common.js
|   |   |-- dashboard.js
|   |   |-- settings.js
|   |   |-- history.js
|-- templates
|-- |-- index.html
|-- |-- _nav.html
|-- |-- login.html
|-- |-- dashboard.html
|-- |-- history.html
|-- |-- settings.html
|-- uploads
|   |-- test_sales_data.csv 
|-- requirements.txt
|-- .env 

```

---

## Setup and Installment

### 1. Clone the repository
```bash
git clone https://github.com/theusername/business-dashbord.git
cd business-dashboard
```

### 2. Create a virtual environment and install dependencies
```
bash 
python -m venv venv
source venv/bin/activate
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` fle in the project root:
```
GEMINI_API_KEY=your_own_personal_api_key_here
JWT_SECRET_KEY=randomstring
DEBUG=false
ENABLE_EMAIL_DIGEST=false
SMTP_HOST=smtp.
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=password
SMTP_FROM=my@example.com
```

Get a free Gemini API key at [aistudio.google.com](https:aistudio.google.com).

### 4. Set up the database
No separate database server is required. The app uses SQLite which stores all data in a single dashboard.db file thats created automatically.

### 5.Run the app
```
bash
uvicorn app.main:app --reload
```

Visit `http:\\127.0.0.1:8000` in your browser.

---

## Usage
1. Open the app in browser -you will see login/register forms
2. Register a new account with email and password
3. You will be taken to dashboard automatically
4. Choose a `.csv` or `.xlsx` file containing sales data (experts columns such as 'date', 'product', etc)
5. Click **Upload an analyse**
6. If the columns aren't recognised, fill in the mapping form that appears and continue
7. View the calculated metrics, charts, anomalies and AI- generated recommendations directly on the page. Ask the chat box a question about the report if you want more detail
8. Export the report as CSV or PDF from the same page.
9. Visit **History** to browse every page report, view an old one, delete one, or check two to compare them.
10. Visit **Settings** to create additional workspaces and invite teammates, invite members to see the same report as owners
11. Click logout to end your session

---

## Expected CSV Format

| Column    | Description                          |
|-----------|--------------------------------------|
| `Date`    | Transaction date (e.g. `2023-01-02`) |
| `Product` | Product name                         |
| `Units`   | Units solds                          |
| `Revenue` | Revenue for that row                 |
| `Customer`| (optional) Customer identifier/email |
| `Revenue` | (optional)e.g paid,redunded,cancelled|

- Files with `Qunatity` and `Price` columns are also supported- revenue is calculated automatically. `N/A` values are handled gracefully
- Files with different columns names entirely are supported via column mapping step down after upload.
- `N/A` values are handled gracefully.

---

## About the "Admin" endpoint

There's no admin *page* - its a single API endpoint, `POST /admin/send-digests`. It manually triggers the optional weekly email digest immediately, instead of waiting for the once-a-week background job, which is useful for testing your SMTP configuration.

**Known limitation:** this endpoint currently isn't restricted to an atual "admin" user. Any logged in user can call it, and it will send digest emails to every registered user. Fine for a personal/demo deployment not soenthimg to expose as is in a real mutitenant product.

---

## Known limitations

## Requirements
```
fastapi
uvicorn[standard]
pandas
plotly
openpyxl
sqlalchemy
passlib[bcrypt]
python-json[cryptography]
pydantic[email]
python-multipart
python-dotenv
python-jose
reportlab
apscheduler
requests
jinja2
google-genai
bcrypt==4.0.1
```

---

## Future Improvements

- [ ] Restrict `/amin/send-digests` to a real admin role
- [ ] member removal + workspace delection
- [ ] password reset + email verification
- [ ] search/sort/pagination on the History page
- [ ] Automated tests (pytest) covering access control specifically
- [ ] OAuth-based integrations instead of pasted API keys

---

## Diniso Gwabeni
