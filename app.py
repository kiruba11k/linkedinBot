import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="LinkedIn Auto Connector", layout="wide")

st.title("LinkedIn Auto Connection Tool")
st.markdown("""
**Upload your CSV** containing:
- `profile_url`: LinkedIn profile link
- `invite_msg`: Custom message to send
""")

# Upload CSV
uploaded_file = st.file_uploader(" Upload CSV File", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader(" Preview of Uploaded Data")
    st.dataframe(df)

    # Option to set connection limit
    max_requests = st.number_input("Set Maximum Requests to Send", min_value=1, max_value=len(df), value=min(20, len(df)))

    # Start button
    if st.button(" Start Sending Requests"):
        st.info("Initializing automation... Please wait.")
        progress_bar = st.progress(0)
        status_area = st.empty()

        # LinkedIn credentials from secrets
        LINKEDIN_USERNAME = st.secrets["LINKEDIN_USERNAME"]
        LINKEDIN_PASSWORD = st.secrets["LINKEDIN_PASSWORD"]
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)

        results = []

        def login_to_linkedin():
            driver.get("https://www.linkedin.com/login")
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "username")))
            driver.find_element(By.ID, "username").send_keys(LINKEDIN_USERNAME)
            driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
            driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
            WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/feed/')]")))
            logging.info(" Logged in successfully.")
            status_area.write(" Logged into LinkedIn successfully.")

        def send_request(profile_url, message):
            driver.get(profile_url)
            time.sleep(7)
            try:
                connect_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Connect')]"))
                )
                connect_btn.click()
                add_note_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Add a note']"))
                )
                add_note_btn.click()
                message_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "message"))
                )
                message_box.send_keys(message)
                send_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button//span[text()='Send']"))
                )
                send_btn.click()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return " Sent", timestamp

                
            except Exception as e:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return f" Failed: {e}", timestamp

        login_to_linkedin()

        for i, row in df.head(max_requests).iterrows():
            profile_url = row['profile_url']
            message = row['invite_msg']
            status_area.write(f" Sending request to: {profile_url}")
            result = send_request(profile_url, message)
            results.append({"Profile": profile_url, "Status": result})
            progress_bar.progress((i + 1) / max_requests)
            time.sleep(5)  # Delay to prevent account blocks

        driver.quit()

        st.success(" All connection requests processed!")
        st.subheader(" Summary Report")
        st.dataframe(pd.DataFrame(results))

        # Option to download the result as CSV
        csv_download = pd.DataFrame(results).to_csv(index=False)
        st.download_button(" Download Report", csv_download, "linkedin_results.csv", "text/csv")
