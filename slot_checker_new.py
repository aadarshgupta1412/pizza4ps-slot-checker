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
        # Run in visible mode for better JavaScript interaction
        # chrome_options.add_argument("--headless")  # Commented out for visible mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        # Add user agent to appear more like a real browser
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36")
        
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

def fill_booking_details(driver, date, time_slot, num_adults):
    """Helper function to fill in booking details after a time slot has been selected"""
    print(f"Filling booking details for {date} at {time_slot} for {num_adults} adults")
    try:
        # Take screenshot before filling details
        driver.save_screenshot(f"before_details_{date}_{time_slot.replace(':', '')}.png")
        
        # Wait for booking form to appear
        time.sleep(3)
        
        # Name field
        try:
            # Try different selectors for name input
            name_selectors = [
                "input[name='firstName']", 
                "[data-testid='first-name-input']",
                "input[placeholder*='name' i]",
                "input[id*='name' i]",
                "input[name*='name' i]"
            ]
            
            name_input = None
            for selector in name_selectors:
                try:
                    name_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if name_input:
                        break
                except:
                    continue
            
            if name_input:
                name_input.clear()
                name_input.send_keys("Aadarsh Gupta")
                print("Filled in name")
            else:
                print("Could not find name input field")
        except Exception as e:
            print(f"Error filling in name: {str(e)}")
        
        # Phone field
        try:
            # Try different selectors for phone input
            phone_selectors = [
                "input[name='phone']", 
                "[data-testid='phone-input']",
                "input[placeholder*='phone' i]",
                "input[id*='phone' i]",
                "input[name*='phone' i]",
                "input[type='tel']"
            ]
            
            phone_input = None
            for selector in phone_selectors:
                try:
                    phone_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if phone_input:
                        break
                except:
                    continue
            
            if phone_input:
                phone_input.clear()
                phone_input.send_keys("917879974479")
                print("Filled in phone")
            else:
                print("Could not find phone input field")
        except Exception as e:
            print(f"Error filling in phone: {str(e)}")
        
        # Email field
        try:
            # Try different selectors for email input
            email_selectors = [
                "input[name='email']", 
                "[data-testid='email-input']",
                "input[placeholder*='email' i]",
                "input[id*='email' i]",
                "input[name*='email' i]",
                "input[type='email']"
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if email_input:
                        break
                except:
                    continue
            
            if email_input:
                email_input.clear()
                email_input.send_keys(USER_EMAIL)
                print("Filled in email")
            else:
                print("Could not find email input field")
        except Exception as e:
            print(f"Error filling in email: {str(e)}")
        
        # Take screenshot after filling details
        driver.save_screenshot(f"filled_details_{date}_{time_slot.replace(':', '')}.png")
        
        # Accept terms (if present)
        try:
            # Try different selectors for terms checkbox
            terms_selectors = [
                "input[type='checkbox']", 
                "[data-testid='terms-checkbox']",
                ".terms-checkbox",
                "input[id*='terms' i]",
                "input[name*='terms' i]"
            ]
            
            terms_checkbox = None
            for selector in terms_selectors:
                try:
                    checkboxes = driver.find_elements(By.CSS_SELECTOR, selector)
                    if checkboxes:
                        terms_checkbox = checkboxes[0]
                        break
                except:
                    continue
            
            if terms_checkbox and not terms_checkbox.is_selected():
                terms_checkbox.click()
                print("Accepted terms")
        except Exception as e:
            print(f"Could not accept terms (may not be required): {str(e)}")
        
        # Submit booking
        print("Attempting to submit booking...")
        try:
            # Try different selectors for submit button
            submit_selectors = [
                "button[type='submit']", 
                "[data-testid='submit-button']",
                ".submit-button",
                "button:contains('Book')",
                "button:contains('Reserve')",
                "button.primary",
                "button.submit",
                "input[type='submit']"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    if buttons:
                        submit_button = buttons[0]
                        break
                except:
                    continue
            
            if not submit_button:
                # Try XPath approach
                xpath_patterns = [
                    "//button[contains(., 'Book')]",
                    "//button[contains(., 'Reserve')]",
                    "//button[contains(., 'Submit')]",
                    "//button[contains(., 'Confirm')]"
                ]
                
                for xpath in xpath_patterns:
                    try:
                        buttons = driver.find_elements(By.XPATH, xpath)
                        if buttons:
                            submit_button = buttons[0]
                            break
                    except:
                        continue
            
            if submit_button:
                # Uncomment the line below to actually submit the booking
                # submit_button.click()
                print("Found submit button but NOT clicking it (safety measure)")
                print("To actually submit the booking, uncomment the submit_button.click() line in the code")
                # Take screenshot of submit button
                driver.save_screenshot(f"submit_button_{date}_{time_slot.replace(':', '')}.png")
            else:
                print("Could not find submit button")
        except Exception as e:
            print(f"Error finding submit button: {str(e)}")
        
        # Take final screenshot
        driver.save_screenshot(f"booking_final_{date}_{time_slot.replace(':', '')}.png")
        
        print("Booking details filled successfully")
        return True
    except Exception as e:
        print(f"Error filling booking details: {str(e)}")
        driver.save_screenshot(f"details_error_{date}_{time_slot.replace(':', '')}.png")
        return False

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
        
        # 2. Fill in booking details
        fill_booking_details(driver, date, time_slot, num_adults)
        
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
                    
                    # Step 2: Select date using direct JavaScript injection
                    print(f"Selecting date: {date}")
                    try:
                        # Try to find any date input field
                        date_input_found = False
                        
                        # Method 1: Try to find a date input field
                        try:
                            date_input = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='date'], [data-testid='date-picker-input'], input.date-input"))
                            )
                            # Clear and set the date directly
                            driver.execute_script("arguments[0].value = arguments[1]", date_input, date)
                            # Trigger change event
                            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { 'bubbles': true }))", date_input)
                            date_input_found = True
                            print(f"Set date {date} directly on input field")
                            time.sleep(2)
                        except Exception as e:
                            print(f"Could not set date directly on input: {str(e)}")
                        
                        # Method 2: Try to use JavaScript to set the date in the application's state
                        if not date_input_found:
                            try:
                                # This is a more aggressive approach - inject a date value directly into the page
                                js_script = f"""
                                // Try to find any date picker or input
                                var datePickers = document.querySelectorAll('input[type="date"], [data-testid*="date"], .date-picker, .calendar');
                                if (datePickers.length > 0) {{                                    
                                    // Set value and dispatch events
                                    datePickers.forEach(function(el) {{
                                        el.value = '{date}';
                                        el.dispatchEvent(new Event('change', {{ 'bubbles': true }}));
                                        el.dispatchEvent(new Event('input', {{ 'bubbles': true }}));
                                        console.log('Set date on element:', el);
                                    }});
                                    return true;
                                }}
                                return false;
                                """
                                result = driver.execute_script(js_script)
                                if result:
                                    date_input_found = True
                                    print(f"Set date {date} using JavaScript injection")
                                    time.sleep(2)
                            except Exception as e:
                                print(f"Could not set date using JavaScript: {str(e)}")
                        
                        # Method 3: Try clicking on the date field and then selecting from calendar
                        if not date_input_found:
                            try:
                                # Click any element that might open a date picker
                                date_elements = driver.find_elements(By.XPATH, "//button[contains(., 'Date')] | //input[contains(@placeholder, 'date')] | //div[contains(@class, 'date')]")
                                if date_elements:
                                    date_elements[0].click()
                                    print("Clicked on potential date element")
                                    time.sleep(2)
                                    
                                    # Now try to select the date from calendar
                                    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
                                    day = date_obj.day
                                    month = date_obj.month
                                    year = date_obj.year
                                    
                                    # Try to find the date in the calendar
                                    calendar_day = driver.find_elements(By.XPATH, f"//button[contains(text(), '{day}')] | //td[contains(text(), '{day}')]")
                                    if calendar_day:
                                        calendar_day[0].click()
                                        date_input_found = True
                                        print(f"Selected date {date} from calendar")
                                        time.sleep(2)
                            except Exception as e:
                                print(f"Could not select date from calendar: {str(e)}")
                        
                        # Take screenshot after date selection attempt
                        driver.save_screenshot(f"date_selection_{date}_{num_adults}.png")
                        
                        if not date_input_found:
                            print("WARNING: Could not set date, but continuing anyway")
                            # We'll continue anyway as the site might have a default date selected
                    except Exception as e:
                        print(f"Error selecting date: {str(e)}")
                        # Continue anyway
                    
                    # Step 3: Look for available time slots with enhanced detection
                    print("Looking for available time slots...")
                    time_slots = []
                    try:
                        # First take a screenshot of the current state
                        driver.save_screenshot(f"before_time_slots_{date}_{num_adults}.png")
                        
                        # Try different selectors for time slots
                        time_slot_selectors = [
                            ".time-slot:not(.disabled)",
                            "[data-testid='time-slot']:not([disabled])",
                            ".available-time",
                            "button.available",
                            "button:not([disabled])",
                            "[role='button']:not([disabled])",
                            "a.time-slot",
                            "div.time-slot"
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
                        
                        # If no slots found, try XPath approach
                        if not time_slots:
                            try:
                                # Look for any clickable elements that might be time slots
                                time_slots = driver.find_elements(By.XPATH, "//button[not(@disabled)] | //div[@role='button' and not(@disabled)] | //a[contains(@class, 'time') or contains(@class, 'slot')]")
                                if time_slots:
                                    print(f"Found {len(time_slots)} potential time slots using XPath")
                            except Exception as e:
                                print(f"Could not find time slots using XPath: {str(e)}")
                        
                        # Take screenshot of available slots
                        driver.save_screenshot(f"time_slots_{date}_{num_adults}.png")
                        
                        if time_slots:
                            print(f"Found {len(time_slots)} potential time slots!")
                            
                            # Try to extract text from the slots
                            available_times = []
                            for slot in time_slots:
                                try:
                                    # Try to get text using different methods
                                    slot_text = slot.text.strip()
                                    if not slot_text:
                                        # Try to get text using JavaScript
                                        slot_text = driver.execute_script("return arguments[0].textContent", slot).strip()
                                    
                                    if slot_text and slot_text not in ['FULL', 'CLOSED', 'UNAVAILABLE']:
                                        available_times.append(slot_text)
                                        print(f"Found available time: {slot_text}")
                                except Exception as e:
                                    print(f"Error extracting text from slot: {str(e)}")
                            
                            # If we couldn't extract any text, just use the slots themselves
                            if not available_times and time_slots:
                                print("Could not extract text from slots, using slots directly")
                                # Just use the first slot
                                first_slot = time_slots[0]
                                
                                # Send email notification
                                subject = f"Pizza 4P's Slots Available - {date} for {num_adults} adults"
                                message = f"Found available slots on {date} for {num_adults} adults!\n\n"
                                message += "Time text could not be extracted, but slots are available.\n"
                                message += "\n\nBook now at: " + BOOKING_URL
                                send_email(subject, message)
                                
                                # Try to book by directly clicking the slot
                                print("Attempting to book by directly clicking the slot...")
                                try:
                                    # Click the slot
                                    first_slot.click()
                                    time.sleep(2)
                                    driver.save_screenshot(f"clicked_slot_{date}_{num_adults}.png")
                                    
                                    # Now fill in the booking details
                                    fill_booking_details(driver, date, "Unknown Time", num_adults)
                                    return  # Exit after finding and attempting to book
                                except Exception as e:
                                    print(f"Error clicking slot: {str(e)}")
                            elif available_times:
                                # Send email notification
                                subject = f"Pizza 4P's Slots Available - {date} for {num_adults} adults"
                                message = f"Found {len(available_times)} available slots on {date} for {num_adults} adults:\n\n"
                                message += "\n".join(available_times)
                                message += "\n\nBook now at: " + BOOKING_URL
                                send_email(subject, message)
                                
                                # Try to book the first available slot
                                print(f"Attempting to book slot: {available_times[0]}")
                                try:
                                    # Find and click the slot with this text
                                    slot_to_book = None
                                    for slot in time_slots:
                                        if slot.text.strip() == available_times[0] or driver.execute_script("return arguments[0].textContent", slot).strip() == available_times[0]:
                                            slot_to_book = slot
                                            break
                                    
                                    if slot_to_book:
                                        slot_to_book.click()
                                        time.sleep(2)
                                        driver.save_screenshot(f"clicked_slot_{date}_{num_adults}.png")
                                        
                                        # Now fill in the booking details
                                        fill_booking_details(driver, date, available_times[0], num_adults)
                                        return  # Exit after finding and attempting to book
                                    else:
                                        print(f"Could not find slot with text: {available_times[0]}")
                                except Exception as e:
                                    print(f"Error booking slot: {str(e)}")
                            else:
                                print("Found time slots but couldn't extract any valid times")
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
