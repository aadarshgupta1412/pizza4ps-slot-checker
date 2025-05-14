import time
import datetime
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load configuration
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

# Update README with current configuration
def update_readme(config):
    try:
        with open('README.md', 'r') as f:
            content = f.read()
        
        # Find the Features section and update it
        start = content.find('## Features')
        if start == -1:
            print("Could not find Features section in README")
            return
            
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
        print("README updated successfully")
    except Exception as e:
        print(f"Error updating README: {str(e)}")

# Load configuration
config = load_config()
TARGET_DATES = config['target_dates']
TIME_RANGE = config['time_range']
USER_EMAIL = config['email']

# Update README with current configuration
try:
    update_readme(config)
except Exception as e:
    print(f"Warning: Could not update README: {str(e)}")

# Constants
BOOKING_URL = 'https://www.tablecheck.com/en/shops/pizza-4ps-in-indiranagar/reserve'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Get email credentials from environment variables
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

if not EMAIL_USER or not EMAIL_PASSWORD:
    raise ValueError("Please set EMAIL_USER and EMAIL_PASSWORD in .env file")

def setup_driver():
    try:
        print("Setting up Chrome driver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Try direct path first (for Mac ARM)
        try:
            # For Mac ARM architecture
            driver = webdriver.Chrome(options=chrome_options)
            print("Successfully initialized ChromeDriver directly")
            return driver
        except Exception as e:
            print(f"Direct initialization failed: {str(e)}")
            
            # Fallback to ChromeDriverManager
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"Successfully initialized ChromeDriver with ChromeDriverManager")
            return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {str(e)}")
        raise

def send_email(subject, message):
    try:
        print("Sending email notification...")
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
        
        print("Email notification sent successfully")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def try_booking(driver, date, time_slot, num_adults):
    try:
        print(f"Attempting to book: {date} at {time_slot} for {num_adults} adults")
        # Take screenshot before booking attempt
        driver.save_screenshot(f"booking_attempt_{date}_{time_slot.replace(':', '')}.png")
        
        # 1. Click on the time slot button
        print(f"Clicking on time slot: {time_slot}")
        try:
            # Try different ways to find the time slot button
            time_slot_found = False
            
            # Method 1: Direct text match
            try:
                slot_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{time_slot}')]")),
                )
                slot_button.click()
                time_slot_found = True
                print(f"Clicked time slot using direct text match: {time_slot}")
            except Exception as e:
                print(f"Could not click time slot using direct text match: {str(e)}")
            
            # Method 2: Find by class and text
            if not time_slot_found:
                try:
                    slot_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//button[contains(@class, 'time-slot') and contains(text(), '{time_slot}')]")),
                    )
                    slot_button.click()
                    time_slot_found = True
                    print(f"Clicked time slot using class and text: {time_slot}")
                except Exception as e:
                    print(f"Could not click time slot using class and text: {str(e)}")
            
            # Method 3: Find any available time slot
            if not time_slot_found:
                try:
                    available_slots = driver.find_elements(By.CSS_SELECTOR, ".time-slot:not(.disabled), [data-testid='time-slot']:not([disabled]), .available-time")
                    if available_slots:
                        available_slots[0].click()
                        time_slot_found = True
                        print(f"Clicked first available time slot")
                    else:
                        print("No available time slots found")
                except Exception as e:
                    print(f"Could not click any available time slot: {str(e)}")
            
            if not time_slot_found:
                raise Exception("Could not find or click any time slot")
                
            # Wait for booking form to appear
            time.sleep(3)
            driver.save_screenshot(f"after_time_slot_{date}_{time_slot.replace(':', '')}.png")
            
        except Exception as e:
            print(f"Error selecting time slot: {str(e)}")
            driver.save_screenshot(f"time_slot_error_{date}_{time_slot.replace(':', '')}.png")
            raise
        
        # 2. Fill in contact details
        print("Filling in contact details...")
        try:
            # Name field
            try:
                name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='firstName'], [data-testid='first-name-input']"))
                )
                name_input.clear()
                name_input.send_keys("Aadarsh Gupta")
                print("Filled in name")
            except Exception as e:
                print(f"Could not fill in name: {str(e)}")
            
            # Phone field
            try:
                phone_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='phone'], [data-testid='phone-input']"))
                )
                phone_input.clear()
                phone_input.send_keys("917879974479")
                print("Filled in phone")
            except Exception as e:
                print(f"Could not fill in phone: {str(e)}")
            
            # Email field
            try:
                email_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email'], [data-testid='email-input']"))
                )
                email_input.clear()
                email_input.send_keys(USER_EMAIL)
                print("Filled in email")
            except Exception as e:
                print(f"Could not fill in email: {str(e)}")
            
            # Take screenshot after filling details
            driver.save_screenshot(f"filled_details_{date}_{time_slot.replace(':', '')}.png")
            
            # 3. Accept terms (if present)
            try:
                terms_checkbox = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='checkbox'], [data-testid='terms-checkbox']"))
                )
                if not terms_checkbox.is_selected():
                    terms_checkbox.click()
                    print("Accepted terms")
            except Exception as e:
                print(f"Could not accept terms (may not be required): {str(e)}")
            
            # 4. Submit booking
            print("Attempting to submit booking...")
            try:
                submit_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], [data-testid='submit-button'], .submit-button, button:contains('Book'), button:contains('Reserve')"))
                )
                # Uncomment the line below to actually submit the booking
                # submit_button.click()
                print("Found submit button but NOT clicking it (safety measure)")
                print("To actually submit the booking, uncomment the submit_button.click() line in the code")
            except Exception as e:
                print(f"Could not find submit button: {str(e)}")
            
            # Take final screenshot
            driver.save_screenshot(f"booking_final_{date}_{time_slot.replace(':', '')}.png")
            
        except Exception as e:
            print(f"Error filling in contact details: {str(e)}")
            driver.save_screenshot(f"details_error_{date}_{time_slot.replace(':', '')}.png")
            raise
        
        print("Booking attempt completed - check screenshots for results")
        return True
    except Exception as e:
        print(f"Booking failed: {str(e)}")
        driver.save_screenshot(f"booking_error_{date}_{time_slot.replace(':', '')}.png")
        return False

def check_availability():
    print(f"Checking availability at {datetime.datetime.now()}")
    driver = setup_driver()
    
    try:
        print("Opening booking URL...")
        driver.get(BOOKING_URL)
        time.sleep(10)  # Wait for initial page load
        
        # Take screenshot of initial page
        driver.save_screenshot("initial_page.png")
        print("Saved screenshot of initial page")
        
        # Print page information for debugging
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        for date in TARGET_DATES:
            print(f"\nChecking date: {date}")
            for num_adults in [4, 3, 2]:  # Try with different numbers of adults
                try:
                    print(f"Trying with {num_adults} adults...")
                    
                    # Take screenshot before each attempt
                    driver.save_screenshot(f"before_{date}_{num_adults}.png")
                    
                    # Wait for page to be interactive
                    print("Waiting for page to be interactive...")
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Print page source for debugging
                    print(f"Page source length: {len(driver.page_source)}")
                    
                    # Refresh page for each attempt to ensure clean state
                    driver.refresh()
                    time.sleep(5)
                    
                    # Take screenshot after refresh
                    driver.save_screenshot(f"after_refresh_{date}_{num_adults}.png")
                    
                    # Step 1: Select number of adults
                    print(f"Selecting {num_adults} adults...")
                    try:
                        # Try different selectors for the guest count button
                        guest_selectors = [
                            ".guest-count-button",
                            "[data-testid='guest-count-button']",
                            "button:contains('Guest')",
                            "button:contains('People')",
                            "select[name='adults']",
                            "#adults"
                        ]
                        
                        guest_button_found = False
                        for selector in guest_selectors:
                            try:
                                guest_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                                guest_button.click()
                                guest_button_found = True
                                print(f"Clicked guest button with selector: {selector}")
                                time.sleep(2)
                                break
                            except Exception as e:
                                print(f"Could not click guest button with selector {selector}: {str(e)}")
                        
                        # If no button found, try XPath
                        if not guest_button_found:
                            try:
                                guest_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Guest') or contains(., 'People') or contains(., 'Adult')]"))
                                )
                                guest_button.click()
                                guest_button_found = True
                                print("Clicked guest button using XPath")
                                time.sleep(2)
                            except Exception as e:
                                print(f"Could not click guest button using XPath: {str(e)}")
                        
                        # Now select the number of adults
                        if guest_button_found:
                            try:
                                # Try to find the adult option by text
                                adult_option = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, f"//button[text()='{num_adults}'] | //option[text()='{num_adults}'] | //div[text()='{num_adults}']")),
                                )
                                adult_option.click()
                                print(f"Selected {num_adults} adults")
                                time.sleep(2)
                            except Exception as e:
                                print(f"Could not select {num_adults} adults: {str(e)}")
                    except Exception as e:
                        print(f"Error selecting number of adults: {str(e)}")
                    
                    # Step 2: Select date
                    print(f"Selecting date: {date}")
                    try:
                        # Try different selectors for the date button
                        date_selectors = [
                            ".date-picker-button",
                            "[data-testid='date-picker-button']",
                            "input[type='date']",
                            "button:contains('Date')"
                        ]
                        
                        date_button_found = False
                        for selector in date_selectors:
                            try:
                                date_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                                date_button.click()
                                date_button_found = True
                                print(f"Clicked date button with selector: {selector}")
                                time.sleep(2)
                                break
                            except Exception as e:
                                print(f"Could not click date button with selector {selector}: {str(e)}")
                        
                        # If no button found, try XPath
                        if not date_button_found:
                            try:
                                date_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Date') or contains(., 'Calendar')]"))
                                )
                                date_button.click()
                                date_button_found = True
                                print("Clicked date button using XPath")
                                time.sleep(2)
                            except Exception as e:
                                print(f"Could not click date button using XPath: {str(e)}")
                        
                        # Now select the date
                        if date_button_found:
                            try:
                                # Parse the date
                                date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
                                day = date_obj.day
                                
                                # Try to find the date in the calendar
                                date_option = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, f"//button[text()='{day}'] | //td[text()='{day}']")),
                                )
                                date_option.click()
                                print(f"Selected date {date}")
                                time.sleep(2)
                            except Exception as e:
                                print(f"Could not select date {date}: {str(e)}")
                    except Exception as e:
                        print(f"Error selecting date: {str(e)}")
                    
                    # Step 3: Look for available time slots
                    print("Looking for available time slots...")
                    time_slots = []
                    try:
                        # Try different selectors for time slots
                        time_slot_selectors = [
                            ".time-slot:not(.disabled)",
                            "[data-testid='time-slot']:not([disabled])",
                            ".available-time",
                            "button.available",
                            "button:not([disabled])"
                        ]
                        
                        for selector in time_slot_selectors:
                            try:
                                slots = driver.find_elements(By.CSS_SELECTOR, selector)
                                if slots:
                                    time_slots = slots
                                    print(f"Found {len(slots)} time slots with selector: {selector}")
                                    break
                            except Exception as e:
                                print(f"Could not find time slots with selector {selector}: {str(e)}")
                        
                        # Take screenshot of available slots
                        driver.save_screenshot(f"time_slots_{date}_{num_adults}.png")
                        
                        if time_slots:
                            print(f"Found {len(time_slots)} available time slots!")
                            available_times = [slot.text for slot in time_slots if slot.text.strip()]
                            print(f"Available times: {', '.join(available_times)}")
                            
                            if available_times:
                                # Send email notification
                                subject = f"Pizza 4P's Slots Available - {date} for {num_adults} adults"
                                message = f"Found {len(available_times)} available slots on {date} for {num_adults} adults:\n\n"
                                message += "\n".join(available_times)
                                message += "\n\nBook now at: " + BOOKING_URL
                                send_email(subject, message)
                                
                                # Try to book the first available slot
                                try_booking(driver, date, available_times[0], num_adults)
                                return  # Exit after finding and attempting to book
                            else:
                                print("Found time slots but couldn't extract times")
                        else:
                            print("No available time slots found")
                    except Exception as e:
                        print(f"Error looking for time slots: {str(e)}")
                    
                    # Take screenshot of final state
                    driver.save_screenshot(f"final_{date}_{num_adults}.png")
                    
                    print(f"Completed check for {date} with {num_adults} adults")
                    
                    # In a real implementation, you would:
                    # 1. Find and select the date
                    # 2. Find and select the number of guests
                    # 3. Look for available time slots
                    # 4. Send notification if slots are found
                    
                except TimeoutException as e:
                    print(f"Timeout while checking {date} with {num_adults} adults: {str(e)}")
                    driver.save_screenshot(f"error_{date}_{num_adults}.png")
                except Exception as e:
                    print(f"Error while checking {date} with {num_adults} adults: {str(e)}")
                    driver.save_screenshot(f"error_{date}_{num_adults}.png")
    except Exception as e:
        print(f"Error during availability check: {str(e)}")
    finally:
        try:
            driver.quit()
            print("Browser closed")
        except:
            print("Error closing browser")

def main():
    print("Starting Pizza 4P's slot checker...")
    check_availability()

if __name__ == "__main__":
    main()
