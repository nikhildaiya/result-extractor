📊 Result Extractor (Data Collection & Storage Engine)

An internal web scraping system designed to fetch, structure, and persist college examination result data from the official result portal.
This project is used only by the developer to scrape results once per examination and store them in reusable formats for further analysis and public presentation.

<hr>

📌 Project Purpose

The official college result website provides:

* One result at a time

* Mandatory manual input (course, roll number, captcha)

* No bulk access or analytical insights

This project solves that limitation by acting as a data ingestion layer, responsible for:

* Automated bulk result scraping

* Accurate captcha handling

* Structured data extraction

* Persistent storage for reuse by other applications

<hr>

🧠 Key Design Philosophy

* Scrape once, use many times

* No repeated scraping for end users

* Separation of concerns:

  * This project → data collection

  * Other projects → analytics, visualization, public access
 
<hr>

🚀 Features

* Single internal UI to select course and start scraping

* Random User-Agent rotation for each scraping session

* Selenium-based browser automation with webdriver spoofing

* Roll number ranges loaded from an external course configuration file

* Robust captcha handling using:

  * Image preprocessing with OpenCV

  * OCR using Tesseract

* Intelligent retry mechanism:

  * Up to 3 attempts per roll number for captcha failures

* Smart termination:

  * Stops scraping after 4 consecutive roll numbers are not found

* Structured result extraction:

  * Student details

  * Subject-wise marks

  * Grand total

  * Percentage and result status

* Persistent storage:

  * JSON (readable & backup)

  * PKL (primary data source for fast reuse)

* Detailed logging:

  * Timestamped logs

  * Attempt counts

  * Success rate

  * Error tracking

* End-of-scrape summary page with complete statistics

<hr>

🛠 Tech Stack

* Language: Python

* Backend: Flask

* Web Automation: Selenium

* OCR: Tesseract (pytesseract)

* Image Processing: OpenCV

* Data Serialization: JSON, Pickle

* Frontend: HTML, CSS

<hr>

⚙️ How It Works (Scraping Workflow)

1. Developer selects a course from the internal UI.

2. System:

    * Loads roll number range from courses.py

    * Chooses a random User-Agent

    * Launches a spoofed Selenium browser

3. For each roll number:

    * Opens the official college result page

    * Selects course and fills roll number

    * Captures captcha image

    * Preprocesses captcha using OpenCV

    * Extracts captcha text using Tesseract OCR

    * Submits the form

4. Based on page response:

    * If result table is found → extract and store data

    * If result not found → count and continue

    * If captcha is wrong → retry (max 3 attempts)

5. Scraping stops automatically after multiple consecutive roll numbers are not found.

6. After completion:

    * Results are saved to JSON and PKL files

    * A detailed log file is generated

    * Summary statistics are displayed on the final page

<hr>

📁 Project Structure

```
result-extractor/
│── app.py
│── courses.py
│── requirements.txt
│
├── templates/
│   ├── index.html
│   ├── response.html
│
├── static/
│   ├── styles/
│   ├── images/
│
├── captchas/
│   └── captcha.png
│
└── results/
    ├── json/
    ├── pkl/
    └── logs/
```

<hr>

🧪 Installation & Setup

1️⃣ Clone Repository

```
git clone https://github.com/nikhildaiya/result-extractor.git
cd result-extractor
```

2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

3️⃣ Install Tesseract OCR

Download and install from:

```
https://github.com/UB-Mannheim/tesseract/wiki
```

Update path in app.py:

```
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

4️⃣ Run Application

```
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

<hr>

📦 Output Files

For each scraping session, the project generates:

* JSON file

    * Human-readable backup format

* PKL file

    * Primary data source for fast loading and reuse

* LOG file

    * Complete scraping history and diagnostics

All files are stored course-wise inside the results/ directory.

<hr>

📊 Scraping Summary Metrics

Displayed at the end of each run:

* Scraping start & end time

* Total duration

* Total roll numbers attempted

* Total results fetched

* Total results not found

* Total captcha failures

* Overall scraping accuracy

<hr>

🔮 Future Enhancements

* Headless scraping mode with fallback

* Parallel scraping with rate control

* Database storage (PostgreSQL / SQLite)

* Automatic integration with analytics dashboard

* Advanced captcha preprocessing strategies

<hr>

⚠️ Disclaimer

This project is developed strictly for educational, research, and personal use to understand:

* Web automation

* OCR-based captcha handling

* Data extraction pipelines

* Robust scraping architecture

<hr>

👨‍💻 Author

Nikhil Daiya

Internal Result Data Scraping & Storage System
