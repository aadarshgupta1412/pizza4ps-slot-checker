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

import json

# Load configuration
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

# Update README with current configuration
def update_readme(config):
    with open('README.md', 'r') as f:
        content = f.read()
    
    # Find the Features section and update it
    start = content.find('## Features')
    end = content.find('##', start + 1) if content.find('##', start + 1) != -1 else len(content)
    
    # Create new features section
    features = f"## Features\n\n"
    features += f"* Checks for slots on {', '.join(config['target_dates'])}\n"
    features += f"* Looks for slots between {config['time_range']['start']} to {config['time_range']['end']}\n"
    features += f"* Tries booking for {config['num_adults_range']['min']}-{config['num_adults_range']['max']} adults\n"
    features += "* Sends email notifications when slots are found\n"
    
    # Replace the section
    new_content = content[:start] + features + content[end:]
    
    with open('README.md', 'w') as f:
        f.write(new_content)

# Load configuration
config = load_config()
TARGET_DATES = config['target_dates']
TIME_RANGE = config['time_range']
USER_EMAIL = config['email']

# Update README with current configuration
update_readme(config)

# Constants
BOOKING_URL = 'https://www.tablecheck.com/en/shops/pizza-4ps-in-indiranagar/reserve'
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
    
    # Try different ChromeDriver paths based on environment
    chromedriver_paths = [
        '/opt/homebrew/bin/chromedriver',  # Mac with Homebrew
        '/usr/bin/chromedriver',           # GitHub Actions Linux
    ]
    
    for path in chromedriver_paths:
        try:
            service = ChromeService(path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f'Successfully initialized ChromeDriver from {path}')
            return driver
        except Exception as e:
            print(f'Failed to initialize ChromeDriver from {path}: {str(e)}')
            continue
    
    raise Exception('Could not initialize ChromeDriver from any known path')
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
                available_slots.append(time_text)
                print(f"Added available slot: {time_text}")
        
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
        print("Opening booking URL...")
        driver.get(BOOKING_URL)
        time.sleep(5)  # Wait longer for page to load
        
        for date in TARGET_DATES:
            print(f"\nChecking date: {date}")
            for num_adults in [4, 3, 2]:  # Try 4, then 3, then 2 adults
                try:
                    print(f"Trying with {num_adults} adults...")
                    
                    # Wait for page to be interactive
                    print("Waiting for page to be interactive...")
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".reservation-form"))
                    )
                    time.sleep(2)
                    
                    # First select number of guests
                    print(f"Selecting {num_adults} adults...")
                    guests_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".guest-count-button"))
                    )
                    guests_button.click()
                    time.sleep(1)
                    
                    # Select the number from dropdown
                    guest_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{num_adults}')]")),
                    )
                    guest_option.click()
                    time.sleep(2)
                    
                    # Now select the date
                    print(f"Selecting date {date}...")
                    # First click the date input to open calendar
                    date_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".date-picker-button"))
                    )
                    date_button.click()
                    time.sleep(1)
                    
                    # Select the date from calendar
                    target_date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d')
                    date_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//button[contains(@class, 'calendar-day') and contains(text(), '{target_date}')]")),
                    )
                    date_option.click()
                    time.sleep(2)
                    
                    # Look for available time slots
                    print("Looking for available time slots...")
                    time_slots = driver.find_elements(By.CSS_SELECTOR, ".time-slot:not(.disabled)")
                    
                    available_slots = []
                    for slot in time_slots:
                        time_text = slot.text.strip()
                        if time_text and 'FULL' not in time_text.upper():
                            available_slots.append(time_text)
                    
                    if available_slots:
                        message = f"Found slots for {date} with {num_adults} adults:\n" + "\n".join(available_slots)
                        print(message)
                        send_email("Pizza 4P's Slots Available!", message)
                        return  # Found slots, no need to try with fewer adults
                    else:
                        print(f"No available slots found for {date} with {num_adults} adults")
                    
                except TimeoutException as e:
                    print(f"Timeout while checking {date} with {num_adults} adults: {str(e)}")
                    driver.save_screenshot(f"error_{date}_{num_adults}.png")
                    continue
                except Exception as e:
                    print(f"Error while checking {date} with {num_adults} adults: {str(e)}")
                    driver.save_screenshot(f"error_{date}_{num_adults}.png")
                    continue
                
                # Go back to the homepage for next attempt
                driver.get(BOOKING_URL)
                time.sleep(3)

    except Exception as e:
        error_message = f"Error checking availability: {str(e)}"
        print(error_message)
        send_email("Pizza 4P's Booking Script Error", error_message)

    finally:
        driver.quit()

def main():
    print("Starting Pizza 4P's slot checker...")
    check_availability()

if __name__ == "__main__":
    main()
