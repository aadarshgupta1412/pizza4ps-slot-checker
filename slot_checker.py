import time
import schedule
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
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
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully: {subject}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

def setup_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # Use system Chrome and ChromeDriver in GitHub Actions
    service = ChromeService('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def check_availability(driver, date, num_adults):
    url = f"https://pizza4ps.quandoo.jp/en/place/pizza-4ps-saigon-centre-2-le-loi-23968/calendar?date={date}"
    print(f"Checking URL: {url}")
    driver.get(url)
    
    try:
        print("Waiting for time slots to load...")
        # Wait for the time slots to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='time-slot-button']"))
        )
        
        # Find all time slots
        time_slots = driver.find_elements(By.CSS_SELECTOR, "[data-testid='time-slot-button']")
        print(f"Found {len(time_slots)} time slots")
        available_slots = []
        
        for slot in time_slots:
            time_text = slot.text
            print(f"Found slot: {time_text}")
            if time_text and not "FULL" in time_text:
                # Check if the time is between 12 PM and 9 PM
                try:
                    hour = int(time_text.split(':')[0])
                    if 12 <= hour <= 21:  # 12 PM to 9 PM
                        available_slots.append(time_text)
                        print(f"Added available slot: {time_text}")
                except ValueError:
                    continue
        
        return available_slots
    
    except TimeoutException:
        print(f"Timeout waiting for time slots to load for date: {date}")
        return []
    except NoSuchElementException:
        print(f"No time slots found for date: {date}")
        return []
    except Exception as e:
        print(f"Error checking availability: {str(e)}")
        return []

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
        name_input.send_keys('Aadarsh Gupta')

        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "phone"))
        )
        phone_input.send_keys('917879974479')

        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys(EMAIL_USER)

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
