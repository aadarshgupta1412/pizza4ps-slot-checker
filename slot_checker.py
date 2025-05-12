import time
import schedule
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
TARGET_DATES = ['2025-05-17', '2025-05-18']
TIME_RANGE = {
    'start': '12:00',
    'end': '21:00'
}
BOOKING_URL = 'https://www.tablecheck.com/en/shops/pizza-4ps-in-indiranagar/reserve'
USER_EMAIL = 'aadarshgupta1412@gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
# Load environment variables
from dotenv import load_dotenv
import os

load_dotenv()

# Get email credentials from environment variables
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

if not EMAIL_USER or not EMAIL_PASSWORD:
    raise ValueError("Please set EMAIL_USER and EMAIL_PASSWORD in .env file")

# Booking details
BOOKING_INFO = {
    'name': 'Aadarsh Gupta',
    'phone': '917879974479',  # Formatted for the website
    'adults': [4, 3, 2]  # Will try these numbers in order
}

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    
    # First try to use Chrome directly
    try:
        return webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Direct Chrome initialization failed: {e}")
        
        # Fallback: try using ChromeDriverManager
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            service = ChromeService()
            return webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"ChromeDriver initialization failed: {e}")
            raise

def send_email(subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = USER_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

def is_time_in_range(time_str):
    time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()
    start_time = datetime.datetime.strptime(TIME_RANGE['start'], '%H:%M').time()
    end_time = datetime.datetime.strptime(TIME_RANGE['end'], '%H:%M').time()
    return start_time <= time_obj <= end_time

def try_booking(driver, date, time_slot, num_adults):
    try:
        # Select date
        date_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='date-picker-input']"))
        )
        date_input.clear()
        date_input.send_keys(date)

        # Select number of adults
        adults_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='adults-select']"))
        )
        adults_dropdown.click()
        adult_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-value='{num_adults}']"))
        )
        adult_option.click()

        # Select time slot
        time_slot_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{time_slot}')]"))
        )
        time_slot_element.click()

        # Fill in contact details
        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "firstName"))
        )
        name_input.send_keys(BOOKING_INFO['name'])

        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "phone"))
        )
        phone_input.send_keys(BOOKING_INFO['phone'])

        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys(USER_EMAIL)

        # Accept terms
        terms_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[type='checkbox']"))
        )
        terms_checkbox.click()

        # Click next step/submit
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[type='submit']"))
        )
        submit_button.click()

        # Wait for confirmation
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".confirmation-message"))
        )

        message = f"Successfully booked a table!\nDate: {date}\nTime: {time_slot}\nNumber of adults: {num_adults}"
        send_email("Pizza 4P's Booking Confirmed!", message)
        return True

    except Exception as e:
        print(f"Booking failed: {str(e)}")
        return False

def check_availability():
    print(f"Checking availability at {datetime.datetime.now()}")
    driver = setup_driver()
    
    try:
        driver.get(BOOKING_URL)
        
        for date in TARGET_DATES:
            for num_adults in BOOKING_INFO['adults']:
                try:
                    # Similar steps as in try_booking but only checking availability
                    date_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='date-picker-input']"))
                    )
                    date_input.clear()
                    date_input.send_keys(date)

                    # Get available time slots
                    time_slots = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".time-slot"))
                    )

                    available_slots = []
                    for slot in time_slots:
                        time_text = slot.get_attribute('textContent').strip()
                        if is_time_in_range(time_text):
                            available_slots.append(time_text)

                    if available_slots:
                        print(f"Found slots for {date}: {available_slots}")
                        for time_slot in available_slots:
                            if try_booking(driver, date, time_slot, num_adults):
                                return  # Successfully booked

                except TimeoutException:
                    print(f"No slots available for {date} with {num_adults} adults")
                    continue

    except Exception as e:
        error_message = f"Error checking availability: {str(e)}"
        print(error_message)
        send_email("Pizza 4P's Booking Script Error", error_message)

    finally:
        driver.quit()

def main():
    print("Starting Pizza 4P's slot checker...")
    
    # Run immediately once
    check_availability()
    
    # Schedule to run every 30 minutes
    schedule.every(30).minutes.do(check_availability)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
