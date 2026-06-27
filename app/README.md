# AI BUSINESS ANALYTICS DASHBOARD

A full-stack web application that lets a business upload a sales CSV or Excel file and instantly get back revenue trends, best selling productsm, key metrices, and AI generated business recommendations.

Built to demonstrate a complete data pipline from raw file upload, through ata analysis and visualisation, to an LLM powered insights layer all in Python.

---
## Features

- File upload -which accepts .csv and .xlsx sales data
- Automated analysis - pandas calculations of total revenue, average order value, best selling products, and monthly revene trends
- Charts -Plotly- generated revenue and sales visualisations
- AI Recommendation - Google Gemini API analyses the results and generates specific actionable businesss recommendations
- Simple web interface -currently allow upload file then analyses and view results

---

## Tech Stack
| Layer | Technology                  |
|----|-----------------------------|
| Backend | Python, FastApi             |
| Data Analysis | Pandas                      |
| Visualisation | Plotly                      |
| Database |                             |
| AI | Google Gemini API           |
| Frontend | HTML, JAVASCRPT (FETCH API) |
|    |             |

---

## How it works
    
1. User uploads a CSV/EXCEL file through web interface
2. Fast API recives the file and loads it into a pandas dataframe
3. The analysis module calculates revenue, top products and trends/ if no revenue it finds it using product and cost
4. Plotly generates chart data from the results
5. Report saved in pysql
6. The summary statistics are sent to the Gemini API, which returns three tailor business recommendations
7. Results-including the AI recommendations are returned to the browser and displayed.

---

## Project structure

```
business-dashboard/
|-- app/
|   |-- main.py (continue)
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
```

Get a free Gemini API key at [aistudio.google.com](https:aistudio.google.com).

### 4. Set up the database
Make sure to use pysql

### 5.Run the app
```
bash
uvicorn app.main:app --reload
```

Visit `http:\\127.0.0.1:8000` in your browser.

---

## Usage
1. Open the app in browser
2. Choose a `.csv` or `.xlsx` file containing sales data (experts columns such as 'date', 'product', etc)
3. Click **Upload an analyse**
4. View the calculated metrics and AI- generated recommendations directly on the page

---

## Future Improvements

- [ ] add user aunthentication
- [ ] add support for more files

---

## Diniso Gwabeni