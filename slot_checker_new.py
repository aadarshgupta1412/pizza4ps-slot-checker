import time
import datetime
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
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
        
        # This is a placeholder for the actual booking logic
        # In a real implementation, you would:
        # 1. Click on the time slot
        # 2. Fill in contact details
        # 3. Complete the booking
        
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
                    
                    # Try to find and interact with the booking form
                    # This is a simplified approach - we'll just look for any available slots
                    # and take screenshots for manual verification
                    
                    # Take screenshot after refresh
                    driver.save_screenshot(f"after_refresh_{date}_{num_adults}.png")
                    
                    # Look for any clickable elements that might be time slots
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    print(f"Found {len(buttons)} buttons on page")
                    
                    # Take screenshot of final state
                    driver.save_screenshot(f"final_{date}_{num_adults}.png")
                    
                    # For now, just report that we checked and took screenshots
                    print(f"Completed check for {date} with {num_adults} adults")
                    print("Check screenshots for visual verification")
                    
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
