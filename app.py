import os
import re
import time
import json
import pickle
import random
from datetime import datetime

import cv2
import pytesseract
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from flask import Flask, render_template, request

from courses import COURSE_INFO

BASE_URL = 'https://ellm.in/RES_ESE/form_sem_res.php'

COURSE_SELECT_XPATH = '/html/body/form/table/tbody/tr[4]/th[2]/div/div/select'
ROLLNO_FIELD_XPATH = '//*[@id="Roll Number"]'
CAPTCHA_IMG_XPATH = '/html/body/form/table/tbody/tr[8]/td[3]/img'
CAPTCHA_FIELD_XPATH = '//*[@id="Security Code"]'
RESULT_TABLE_XPATH = '/html/body/table/tbody/tr[3]/td/table'
RESULT_NOT_FOUND_XPATH = '/html/body/table/tbody/tr[3]/td/b'

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTCHA_PATH = os.path.join(BASE_DIR, "captchas", "captcha.png")
CAPTCHA_FOLDER = os.path.join(BASE_DIR, "captchas")
RESULTS_FOLDER = os.path.join(BASE_DIR, "results")
JSON_FOLDER = os.path.join(BASE_DIR, "results", "json")
PKL_FOLDER = os.path.join(BASE_DIR, "results", "pkl")
LOG_FOLDER = os.path.join(BASE_DIR, "results", "logs")

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
]

os.makedirs(CAPTCHA_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs(JSON_FOLDER, exist_ok=True)
os.makedirs(PKL_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/response' , methods = ['POST'])
def results():

    results = []

    total_attempted = 0
    total_fetched = 0
    total_not_found = 0
    total_wrong_captcha = 0
    not_found_count = 0

    is_json_created = False
    is_pkl_created = False
    is_log_created = False

    random_user_agent = random.choice(USER_AGENTS)
    scrap_date_str = datetime.now().strftime("%d-%m-%Y")

    selected_course = request.form.get('course')
    rno_start = COURSE_INFO[selected_course]["rno_start"]
    rno_end = COURSE_INFO[selected_course]["rno_end"]

    filename_base = sanitize_filename(selected_course)
    json_path = os.path.join(JSON_FOLDER, f"{filename_base}.json")
    pkl_path = os.path.join(PKL_FOLDER, f"{filename_base}.pkl")
    log_path = os.path.join(LOG_FOLDER, f"{filename_base}.log")

    driver = setup_selenium_driver()

    scrap_start = datetime.now()
    scrap_start_str = scrap_start.strftime("%I:%M:%S %p")

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"Scraping Log\n\n")
        log_file.write(f"Date         : {scrap_date_str}\n")
        log_file.write(f"Course       : {selected_course}\n")
        log_file.write(f"Roll Number  : [{rno_start} - {rno_end}]\n")
        log_file.write(f"User Agent   : {random_user_agent}\n")
        log_file.write(f"Start Time   : {scrap_start_str}\n\n")

    print(f"\nScraping Date : {scrap_date_str}")
    print(f"Selected Course : {selected_course}")
    print(f"Roll Number Range : [{rno_start} - {rno_end}]")
    print(f"Using User Agent : {random_user_agent}")
    print("\n🟡 Scraping Started...")

    for rollno in range(rno_start , rno_end):

        attempts = 1
        success = False

        while attempts <= 3:

            total_attempted += 1
            driver.get(BASE_URL)

            course_field = Select(driver.find_element('xpath' , COURSE_SELECT_XPATH))
            course_field.select_by_visible_text(selected_course)

            rno_field = driver.find_element('xpath' , ROLLNO_FIELD_XPATH)
            rno_field.send_keys(rollno)

            captcha_img_tag = driver.find_element('xpath' , CAPTCHA_IMG_XPATH)
            captcha_img_tag.screenshot(CAPTCHA_PATH)

            captcha_code = preprocess_and_read_captcha(CAPTCHA_PATH)

            captcha_field = driver.find_element('xpath' , CAPTCHA_FIELD_XPATH)
            captcha_field.send_keys(captcha_code)

            time.sleep(0.2)

            try:
                table = driver.find_element('xpath' , RESULT_TABLE_XPATH)
                rows = table.find_elements(By.TAG_NAME , 'tr')
                not_found_count = 0

                result_row = []

                for row in rows:
                    for data in row.find_elements(By.TAG_NAME , 'th'):
                        result_row.append(data.text)
                    for data in row.find_elements(By.TAG_NAME , 'td'):
                        result_row.append(data.text)

                success = True
                total_fetched += 1

                student_result = extract_student_result(result_row)
                results.append(student_result)

                msg = f"✅ [{rollno}] → Result Found Successfully On Attempt [{attempts}] - Row Length [{len(result_row)}]"
                log_message(msg, log_path)
                print(msg)
                break

            except Exception as e:
                try:
                    driver.find_element('xpath', RESULT_NOT_FOUND_XPATH)
                    total_not_found += 1
                    msg = f"❎ [{rollno}] → Result Not Found On Attempt [{attempts}] - Not Present On Site"
                    log_message(msg, log_path)
                    print(msg)
                    break

                except Exception as e:
                    msg = f"⚠️ [{rollno}] → Result Not Found On Attempt [{attempts}] - Wrong Captcha"
                    attempts += 1
                    total_wrong_captcha += 1
                    log_message(msg, log_path)
                    print(msg)

        if not success:
            not_found_count += 1
            msg = f"❌ Failed To Fetch Result After 3 Attempts Or Result Not Found!"
            log_message(msg, log_path)
            print(msg)
            if not_found_count >= 4:
                msg = "4 Consecutive Roll Numbers Not Found! Stopping The Scraping Process."
                log_message(msg, log_path)
                print(msg)
                break

    driver.close()
    print("🟡 Scraping Completed!")

    scrap_end = datetime.now()
    scrap_end_str = scrap_end.strftime("%I:%M:%S %p")
    scrap_duration_str = str(scrap_end - scrap_start).split(".")[0]
    success_rate = ((total_fetched + total_not_found) / total_attempted) * 100 if total_attempted > 0 else 0

    print(f"\nScrap Start Time : {scrap_start_str}")
    print(f"Scraping End Time : {scrap_end_str}")
    print(f"Scrap Duration : {scrap_duration_str}")
    print(f"\nResults List With Size [{len(results)}] :")
    print(results)

    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"\nEnd Time            : {scrap_end_str}\n")
        log_file.write(f"Duration            : {scrap_duration_str}\n")
        log_file.write(f"Results List Size   : {len(results)}\n")
        log_file.write(f"Total Attempted     : {total_attempted}\n")
        log_file.write(f"Total Fetched       : {total_fetched}\n")
        log_file.write(f"Total Not Found     : {total_not_found}\n")
        log_file.write(f"Total Wrong Captcha : {total_wrong_captcha}\n")
        log_file.write(f"Success Rate        : {round(success_rate , 2)}%\n")

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        is_json_created = True
        json_path = os.path.abspath(json_path)
        msg = f"\n✅ JSON File Created Successfully At {json_path}"
        log_message(msg, log_path)
        print(msg)

    except Exception as e:
        msg = "\n❌ Failed To Create JSON File!"
        log_message(msg, log_path)
        print(msg)
        print(e)

    try:
        with open(pkl_path, "wb") as f:
            pickle.dump(results, f)
        is_pkl_created = True
        pkl_path = os.path.abspath(pkl_path)
        msg = f"✅ PKL File Created Successfully At {pkl_path}"
        log_message(msg, log_path)
        print(msg)

    except Exception as e:
        msg = "❌ Failed To Create PKL File!"
        log_message(msg, log_path)
        print(msg)
        print(e)

    if os.path.exists(log_path):
        is_log_created = True
        log_path = os.path.abspath(log_path)
        print(f"✅ LOG File Created Successfully At {log_path}")
    else:
        print("❌ Failed To Create LOG File!")

    print(f"\nTotal Attempted : {total_attempted}")
    print(f"Total Fetched : {total_fetched}")
    print(f"Total Not Found : {total_not_found}")
    print(f"Total Wrong Captcha : {total_wrong_captcha}")
    print(f"Success Rate : {round(success_rate , 2)}%\n")

    return render_template('response.html', selected_course = selected_course, scrap_date_str = scrap_date_str, scrap_start_str = scrap_start_str, scrap_end_str = scrap_end_str, scrap_duration_str = scrap_duration_str, total_attempted = total_attempted, total_fetched = total_fetched, total_not_found = total_not_found, total_wrong_captcha = total_wrong_captcha, success_rate = success_rate, is_json_created = is_json_created, json_path = json_path, is_pkl_created = is_pkl_created, pkl_path = pkl_path, is_log_created = is_log_created, log_path = log_path, results = results)

def sanitize_filename(course_name):
    sanitized = re.sub(r'[^\w\s]', '', course_name)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized.strip()

def setup_selenium_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('detach', True)
    random_user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={random_user_agent}")
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        }
    )
    driver.maximize_window()
    return driver

def log_message(msg, log_path):
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(msg + "\n")

def preprocess_and_read_captcha(img_path):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite(img_path, thresh)
    captcha_text = pytesseract.image_to_string(Image.open(img_path), config='--psm 8 --oem 3')
    return captcha_text

def extract_student_result(result_row):
    
    student_result = {
        "roll_no": result_row[1],
        "name": result_row[3],
        "course": result_row[5],
        "subjects": {},
        "grand_total": {},
        "result": "",
        "percentage": None
    }

    i = 14

    while i < len(result_row):
        row = result_row[i:i+8]
        if row[0] == "Grand Total":
            total_max = int(row[5])
            total_obt = int(row[7])
            student_result["grand_total"] = {
                "TOTAL_MAX": int(row[5]),
                "TOTAL_MIN": int(row[6]),
                "TOTAL_OBT": int(row[7])
            }
            if total_max > 0:
                student_result["percentage"] = round((total_obt / total_max) * 100, 2)
            i += 8
        elif row[0] == "Result":
            student_result["result"] = row[1]
            break
        elif len(row) == 8:
            subject_code = row[0]
            student_result["subjects"][subject_code] = {
                "CIA_MAX": row[1],
                "CIA_OBT": row[2],
                "ESE_MAX": row[3],
                "ESE_OBT": row[4],
                "TOTAL_MAX": row[5],
                "TOTAL_MIN": row[6],
                "TOTAL_OBT": row[7],
            }
            i += 8
        else:
            break

    return student_result

if __name__ == "__main__":
    app.run(debug=True)

# Tesseract Installation Path - https://github.com/UB-Mannheim/tesseract/wiki
# Copy the path of tesseract.exe from your system and paste it in TESSERACT_PATH variable