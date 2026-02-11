"""
MakeMyTrip Hotel Booking Automation with Google Sheets + ScrapingBee
✔ Reads booking data from Google Sheets
✔ Processes multiple bookings automatically  
✔ Updates Status, Booking_id, and Price columns
✔ ScrapingBee premium India proxies
✔ UPI payment automation
✔ 15-second payment confirmation wait
✔ Automatic screenshot capture
"""

import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables from .env file
load_dotenv()

# =========================================================
# GOOGLE SHEETS MANAGER
# =========================================================

class GoogleSheetsManager:
    """Manages reading and updating Google Sheets"""
    
    def __init__(self, sheet_url):
        self.sheet_url = sheet_url
        self.sheet = None
        self.worksheet = None
        self.df = None
        self.sheet_id = None
        self.credentials = None
        self.connect()
    
    def connect(self):
        """Connect to Google Sheet"""
        try:
            print(f"  → Connecting to: {self.sheet_url[:60]}...")
            
            # Extract sheet ID from URL
            if '/d/' in self.sheet_url:
                self.sheet_id = self.sheet_url.split('/d/')[1].split('/')[0]
            else:
                self.sheet_id = self.sheet_url
            
            print(f"  → Sheet ID: {self.sheet_id}")
            
            # Try to authenticate with gspread (if credentials available)
            try:
                scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
                
                # Check for credentials file
                creds_file = 'credentials.json'
                if os.path.exists(creds_file):
                    self.credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
                    client = gspread.authorize(self.credentials)
                    self.sheet = client.open_by_key(self.sheet_id)
                    self.worksheet = self.sheet.sheet1
                    print(f"  ✓ Authenticated with Google Sheets API")
                else:
                    print(f"  ℹ️  No credentials.json found - using read-only mode")
            except Exception as e:
                print(f"  ℹ️  API auth failed: {e}")
                print(f"  → Using read-only CSV export mode")
            
            # Use pandas to read Google Sheet
            csv_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv"
            print(f"  → Reading data from CSV export...")
            
            self.df = pd.read_csv(csv_url)
            
            print(f"✅ Connected to Google Sheet")
            print(f"   Columns found: {list(self.df.columns)[:5]}...")
            print(f"   Total rows: {len(self.df)}")
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to Google Sheet: {e}")
            print(f"\n   Troubleshooting:")
            print(f"   1. Make sure the sheet is set to 'Anyone with link can view'")
            print(f"   2. Check that the URL is correct")
            print(f"   3. Verify you have internet connection")
            self.df = pd.DataFrame()
            return False
    
    def update_booking_id(self, row_number, booking_id):
        """
        Update booking ID for a specific row in Google Sheet
        """
        try:
            print(f"\n  → Updating Booking ID for row {row_number}...")
            
            # Update local DataFrame first
            if 'Booking_id' not in self.df.columns:
                self.df['Booking_id'] = ''
            
            df_index = row_number - 2  # row_number is 1-indexed with header
            
            if 0 <= df_index < len(self.df):
                self.df.at[df_index, 'Booking_id'] = booking_id
                print(f"  ✓ Booking ID updated in local data: {booking_id}")
                
                # Try to update Google Sheet directly if we have API access
                if self.worksheet:
                    try:
                        # Find Booking_id column
                        header_row = self.worksheet.row_values(1)
                        
                        # Find or create Booking_id column
                        if 'Booking_id' in header_row:
                            col_index = header_row.index('Booking_id') + 1
                        else:
                            # Add new column
                            col_index = len(header_row) + 1
                            self.worksheet.update_cell(1, col_index, 'Booking_id')
                            print(f"  ✓ Created 'Booking_id' column")
                        
                        # Update the cell
                        self.worksheet.update_cell(row_number, col_index, booking_id)
                        print(f"  ✅ Booking ID written to Google Sheet: {booking_id}")
                        return True
                        
                    except Exception as e:
                        print(f"  ⚠️  Could not write to Google Sheet: {e}")
                        print(f"  → Saved to local data only")
                else:
                    print(f"  ⚠️  No write access to Google Sheet")
                    print(f"  → To enable writing, add 'credentials.json' file")
                    print(f"  → Booking ID saved in local data only")
                
                return True
            else:
                print(f"  ✗ Invalid row number: {row_number}")
                return False
                
        except Exception as e:
            print(f"  ✗ Error updating booking ID: {e}")
            return False
    
    def update_price(self, row_number, price):
        """
        Update price for a specific row in Google Sheet
        """
        try:
            print(f"  → Updating Price for row {row_number}...")
            
            # Update local DataFrame first
            if 'Price' not in self.df.columns:
                self.df['Price'] = ''
            
            df_index = row_number - 2
            
            if 0 <= df_index < len(self.df):
                self.df.at[df_index, 'Price'] = price
                print(f"  ✓ Price updated in local data: {price}")
                
                # Try to update Google Sheet directly if we have API access
                if self.worksheet:
                    try:
                        header_row = self.worksheet.row_values(1)
                        
                        # Find or create Price column
                        if 'Price' in header_row:
                            col_index = header_row.index('Price') + 1
                        else:
                            col_index = len(header_row) + 1
                            self.worksheet.update_cell(1, col_index, 'Price')
                            print(f"  ✓ Created 'Price' column")
                        
                        # Update the cell
                        self.worksheet.update_cell(row_number, col_index, price)
                        print(f"  ✅ Price written to Google Sheet: {price}")
                        return True
                        
                    except Exception as e:
                        print(f"  ⚠️  Could not write price to Google Sheet: {e}")
                else:
                    print(f"  ⚠️  No write access - Price saved in local data only")
                
                return True
            else:
                print(f"  ✗ Invalid row number: {row_number}")
                return False
                
        except Exception as e:
            print(f"  ✗ Error updating price: {e}")
            return False
    
    def update_status(self, row_number, status):
        """
        Update status for a specific row in Google Sheet
        status: 'Completed', 'Skipped', 'Failed', etc.
        """
        try:
            print(f"  → Updating Status for row {row_number}: {status}...")
            
            # Update local DataFrame first
            if 'Status' not in self.df.columns:
                self.df['Status'] = ''
            
            df_index = row_number - 2
            
            if 0 <= df_index < len(self.df):
                self.df.at[df_index, 'Status'] = status
                print(f"  ✓ Status updated in local data: {status}")
                
                # Try to update Google Sheet directly if we have API access
                if self.worksheet:
                    try:
                        header_row = self.worksheet.row_values(1)
                        
                        # Find Status column (should already exist)
                        if 'Status' in header_row:
                            col_index = header_row.index('Status') + 1
                        else:
                            col_index = len(header_row) + 1
                            self.worksheet.update_cell(1, col_index, 'Status')
                            print(f"  ✓ Created 'Status' column")
                        
                        # Update the cell
                        self.worksheet.update_cell(row_number, col_index, status)
                        print(f"  ✅ Status written to Google Sheet: {status}")
                        return True
                        
                    except Exception as e:
                        print(f"  ⚠️  Could not write status to Google Sheet: {e}")
                else:
                    print(f"  ⚠️  No write access - Status saved in local data only")
                
                return True
            else:
                print(f"  ✗ Invalid row number: {row_number}")
                return False
                
        except Exception as e:
            print(f"  ✗ Error updating status: {e}")
            return False
    
    def get_pending_bookings(self):
        """Get all pending bookings from sheet"""
        try:
            # Check if df exists and has data
            if self.df is None or len(self.df) == 0:
                print("  ⚠️  No data in DataFrame")
                return []
            
            print(f"\n  → Available columns: {list(self.df.columns)}")
            print(f"  → Total rows in sheet: {len(self.df)}")
            
            # Filter rows where Status is 'Pending' or empty
            if 'Status' in self.df.columns:
                # Convert Status to string to handle NaN and other types
                self.df['Status'] = self.df['Status'].astype(str)
                pending = self.df[
                    (self.df['Status'] == 'nan') |  # NaN values become 'nan' string
                    (self.df['Status'].str.lower().str.strip() == 'pending')
                ]
                print(f"  → Rows with Status='Pending' or empty: {len(pending)}")
            else:
                print(f"  ⚠️  No 'Status' column found - processing all rows")
                pending = self.df
            
            bookings = []
            
            for idx, row in pending.iterrows():
                try:
                    # Map column names - support both formats
                    hotel_id = str(row.get('MMT_HOTEL_ID', row.get('Hotel ID', ''))).strip()
                    city_code = str(row.get('City Code', '')).strip().upper()
                    
                    # Handle Check-in column (might be days or actual date)
                    checkin_value = row.get('Check-in', row.get('Check-in (days)', 7))
                    try:
                        checkin_days = int(checkin_value)
                    except:
                        checkin_days = 7  # Default if can't parse
                    
                    booking = {
                        'row_number': idx + 2,  # +2 because: 0-indexed + 1 header row
                        'hotel_id': hotel_id,
                        'city_code': city_code,
                        'checkin_days': checkin_days,
                        'nights': int(row.get('Nights', 1)),
                        'adults': int(row.get('Adults', 2)),
                        'children': int(row.get('Children', 0)),
                        'rooms': int(row.get('Rooms', 1)),
                        'first_name': str(row.get('First Name', '')).strip(),
                        'last_name': str(row.get('Last Name', '')).strip(),
                        'email': str(row.get('Email', '')).strip(),
                        'mobile': str(row.get('Mobile', '')).strip(),
                        'upi_id': str(row.get('UPI ID', '')).strip()
                    }
                    
                    # Validate required fields
                    if booking['hotel_id'] and booking['city_code']:
                        bookings.append(booking)
                        print(f"  ✓ Row {booking['row_number']}: {booking['hotel_id']} - {booking['city_code']}")
                    else:
                        print(f"  ⚠️  Skipping row {booking['row_number']}: Missing Hotel ID or City Code")
                
                except Exception as e:
                    print(f"  ⚠️  Error processing row {idx + 2}: {e}")
                    continue
            
            return bookings
            
        except Exception as e:
            print(f"❌ Error reading bookings: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def refresh_data(self):
        """Refresh data from Google Sheet"""
        return self.connect()


# =========================================================
# CONFIG
# =========================================================

class Config:
    # Google Sheets
    SHEET_URL = None
    
    # Current booking data (populated from sheet)
    HOTEL_ID = None
    CITY_CODE = None
    CHECKIN_DATE = None
    CHECKOUT_DATE = None
    ADULTS = None
    CHILDREN = None
    ROOMS = None
    GUEST_FIRST_NAME = None
    GUEST_LAST_NAME = None
    GUEST_EMAIL = None
    GUEST_MOBILE = None
    UPI_ID = None
    
    # ScrapingBee settings (loaded from .env)
    SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY", "")
    SCRAPINGBEE_PREMIUM = True
    SCRAPINGBEE_COUNTRY = "in"
    SCRAPINGBEE_RENDER_JS = True
    SCRAPINGBEE_WAIT = 3000
    
    # Browser settings
    HEADLESS = False
    WINDOW_SIZE = "1920,1080"
    IMPLICIT_WAIT = 8
    EXPLICIT_WAIT = 15
    PAGE_LOAD_TIMEOUT = 30
    
    # Payment waiting settings
    PAYMENT_WAIT_TIMEOUT = 15
    PAYMENT_CHECK_INTERVAL = 5
    
    SCREENSHOT_PATH = "./screenshots/"


# =========================================================
# BOOKING DATA LOADER
# =========================================================

def load_booking_from_dict(booking_data):
    """Load booking data into Config from dictionary"""
    Config.HOTEL_ID = booking_data['hotel_id']
    Config.CITY_CODE = booking_data['city_code']
    Config.ADULTS = booking_data['adults']
    Config.CHILDREN = booking_data['children']
    Config.ROOMS = booking_data['rooms']
    Config.GUEST_FIRST_NAME = booking_data['first_name']
    Config.GUEST_LAST_NAME = booking_data['last_name']
    Config.GUEST_EMAIL = booking_data['email']
    Config.GUEST_MOBILE = booking_data['mobile']
    Config.UPI_ID = booking_data['upi_id']
    
    # Calculate dates
    checkin = datetime.now() + timedelta(days=booking_data['checkin_days'])
    checkout = checkin + timedelta(days=booking_data['nights'])
    
    Config.CHECKIN_DATE = checkin.strftime("%m%d%Y")
    Config.CHECKOUT_DATE = checkout.strftime("%m%d%Y")
    
    return checkin, checkout


def build_hotel_url():
    """Build MakeMyTrip hotel URL from Config"""
    room_qualifier = f"{Config.ADULTS}e{Config.CHILDREN}e"
    rsc = f"{Config.ROOMS}e{Config.ADULTS}e{Config.CHILDREN}e"
    
    url = (
        f"https://www.makemytrip.com/hotels/hotel-details/"
        f"?hotelId={Config.HOTEL_ID}"
        f"&_uCurrency=INR"
        f"&checkin={Config.CHECKIN_DATE}"
        f"&checkout={Config.CHECKOUT_DATE}"
        f"&city={Config.CITY_CODE}"
        f"&country=IN"
        f"&locusId={Config.CITY_CODE}"
        f"&locusType=city"
        f"&roomStayQualifier={room_qualifier}"
        f"&rsc={rsc}"
    )
    
    return url


# =========================================================
# BROWSER SETUP
# =========================================================

def setup_driver_with_scrapingbee(use_proxy=True):
    """Setup Chrome WebDriver with optional ScrapingBee proxy"""
    
    options = webdriver.ChromeOptions()
    
    # Basic options
    if Config.HEADLESS:
        options.add_argument("--headless")
    options.add_argument(f"--window-size={Config.WINDOW_SIZE}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    prefs = {
        "profile.default_content_setting_values.popups": 0,
        "profile.popup_exception": "[]"
    }
    options.add_experimental_option("prefs", prefs)
    
    # ScrapingBee proxy configuration
    if use_proxy:
        api_key = Config.SCRAPINGBEE_API_KEY
        params = []
        params.append(f"render_js={str(Config.SCRAPINGBEE_RENDER_JS).lower()}")
        params.append(f"premium_proxy={str(Config.SCRAPINGBEE_PREMIUM).lower()}")
        params.append(f"country_code={Config.SCRAPINGBEE_COUNTRY}")
        params.append(f"wait={Config.SCRAPINGBEE_WAIT}")
        params.append("block_ads=true")
        
        proxy_password = "&".join(params)
        proxy_endpoint = f"{api_key}:{proxy_password}@proxy.scrapingbee.com:8886"
        options.add_argument(f'--proxy-server=http://{proxy_endpoint}')
        print("  ✓ ScrapingBee proxy active (India)")
    else:
        print("  ✓ Direct connection (no proxy)")
    
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    driver.implicitly_wait(Config.IMPLICIT_WAIT)
    driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
    driver.maximize_window()
    
    return driver


# =========================================================
# WAIT HELPERS
# =========================================================

class WaitHelpers:

    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def wait_for_visible(self, locator, retries=2):
        """Wait for element with retry logic"""
        for attempt in range(retries):
            try:
                return self.wait.until(EC.visibility_of_element_located(locator))
            except (TimeoutException, StaleElementReferenceException):
                if attempt < retries - 1:
                    time.sleep(0.5)
                    continue
                return None

    def wait_for_clickable(self, locator, retries=2):
        """Wait for element to be clickable"""
        for attempt in range(retries):
            try:
                return self.wait.until(EC.element_to_be_clickable(locator))
            except (TimeoutException, StaleElementReferenceException):
                if attempt < retries - 1:
                    time.sleep(0.5)
                    continue
                return None


# =========================================================
# BASE PAGE
# =========================================================

class BasePage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WaitHelpers(driver)

    def find(self, locator, retries=2):
        """Find element with retry"""
        for attempt in range(retries):
            try:
                return self.driver.find_element(*locator)
            except (NoSuchElementException, StaleElementReferenceException):
                if attempt < retries - 1:
                    time.sleep(0.3)
                    continue
                return None

    def finds(self, locator):
        try:
            return self.driver.find_elements(*locator)
        except NoSuchElementException:
            return []

    def click(self, locator):
        """Click element"""
        element = self.wait.wait_for_clickable(locator)
        if element:
            try:
                element.click()
                time.sleep(0.5)
                return True
            except:
                pass
        
        # JavaScript fallback
        try:
            element = self.find(locator)
            if element:
                self.driver.execute_script("arguments[0].click();", element)
                time.sleep(0.5)
                return True
        except:
            return False

    def type(self, locator, text):
        """Type text"""
        element = self.wait.wait_for_visible(locator)
        if element:
            try:
                element.clear()
                element.send_keys(text)
                return True
            except:
                return False
        return False

    def scroll_to(self, locator):
        """Scroll to element"""
        element = self.find(locator)
        if element:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.3)

    def scroll_by(self, pixels):
        """Scroll by pixels"""
        self.driver.execute_script(f"window.scrollBy(0,{pixels});")
        time.sleep(0.3)

    def screenshot(self, name):
        """Take screenshot"""
        if not os.path.exists(Config.SCREENSHOT_PATH):
            os.makedirs(Config.SCREENSHOT_PATH)
        
        # Sanitize filename - remove special characters
        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"{Config.SCREENSHOT_PATH}{safe_name}_{timestamp}.png"
        self.driver.save_screenshot(path)
        print(f"  📸 Screenshot: {path}")
        return path


# =========================================================
# HOTEL PAGE
# =========================================================

class HotelPage(BasePage):

    BOOK_NOW = (By.CSS_SELECTOR, ".appBtn.filled.large.bkngOption__cta.fullWidth")
    BOOK_NOW_ALT = (By.XPATH, "//button[contains(@class,'bkngOption__cta')]")

    def click_book_now(self):
        """Click Book Now"""
        print("\n[Step 1] Clicking Book Now...")
        try:
            time.sleep(3)
            self.scroll_by(500)
            time.sleep(1.5)
            
            if self.click(self.BOOK_NOW):
                print("  ✓ Book Now clicked")
                time.sleep(2)
                return True
            
            if self.click(self.BOOK_NOW_ALT):
                print("  ✓ Book Now clicked (alt)")
                time.sleep(2)
                return True
            
            print("  ✗ Book Now not found")
            return False
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False


# =========================================================
# BOOKING PAGE
# =========================================================

class BookingPage(BasePage):

    FIRST_NAME = (By.ID, "fName")
    LAST_NAME = (By.ID, "lName")
    EMAIL = (By.ID, "email")
    MOBILE = (By.ID, "mNo")
    
    # Payment elements
    PAY_NOW = (By.CSS_SELECTOR, ".btnContinuePayment.primaryBtn.capText")
    PAY_NOW_ALT = (By.XPATH, "//button[contains(@class,'btnContinuePayment')]")
    
    # UPI elements
    UPI_CONTAINER = (By.CSS_SELECTOR, ".paymode__container__038c1.make-flex.align-center.gap12")
    UPI_INPUT_TESTID = (By.CSS_SELECTOR, "[data-testid='upi-collect-upi-id-input']")
    UPI_INPUT_NAME = (By.NAME, "UPI_COLLECT|UPI_COLLECT|efb0975372e3")
    UPI_INPUT_ID = (By.ID, "UPI_COLLECT|UPI_COLLECT|efb0975372e3")
    UPI_SEND_BUTTON = (By.CSS_SELECTOR, ".upiCollectForm__buttonClass__bd48b.cursor-pointer.make-flex.perfect-center.noshrink.lato-bold.font16.border-none.width100.white-text")
    
    # Payment confirmation/decline indicators
    PAYMENT_SUCCESS_INDICATORS = [
        (By.XPATH, "//*[contains(text(), 'Payment Successful')]"),
        (By.XPATH, "//*[contains(text(), 'payment successful')]"),
        (By.XPATH, "//*[contains(text(), 'Payment Complete')]"),
        (By.XPATH, "//*[contains(text(), 'Confirmed')]"),
        (By.XPATH, "//*[contains(text(), 'confirmed')]"),
        (By.CSS_SELECTOR, ".payment-success"),
        (By.CSS_SELECTOR, ".success-message"),
    ]
    
    PAYMENT_PENDING_INDICATORS = [
        (By.XPATH, "//*[contains(text(), 'Waiting for payment')]"),
        (By.XPATH, "//*[contains(text(), 'Pending')]"),
        (By.XPATH, "//*[contains(text(), 'pending')]"),
        (By.XPATH, "//*[contains(text(), 'Processing')]"),
    ]
    
    # Popup close button
    CLOSE_POPUP = (By.CSS_SELECTOR, ".close[data-testid='closeButtonClick'][data-cy='closeButtonClick_']")
    CLOSE_POPUP_ALT = (By.CSS_SELECTOR, "[data-testid='closeButtonClick']")
    CLOSE_POPUP_ALT2 = (By.CSS_SELECTOR, "[data-cy='closeButtonClick_']")
    CLOSE_POPUP_ALT3 = (By.CSS_SELECTOR, ".close")
    
    # Booking ID element
    BOOKING_ID = (By.CSS_SELECTOR, ".latoBlack.blackText")
    BOOKING_ID_ALT = (By.XPATH, "//*[contains(@class, 'latoBlack') and contains(@class, 'blackText')]")
    
    # Price element
    PRICE = (By.CSS_SELECTOR, ".latoBlack.font22.dirLeft")
    PRICE_ALT = (By.XPATH, "//*[contains(@class, 'latoBlack') and contains(@class, 'font22') and contains(@class, 'dirLeft')]")

    def enter_guest_details(self):
        """Enter guest details"""
        print("\n[Step 2] Entering guest details...")
        try:
            time.sleep(3)
            
            if self.type(self.FIRST_NAME, Config.GUEST_FIRST_NAME):
                print(f"  ✓ First Name: {Config.GUEST_FIRST_NAME}")
            
            time.sleep(0.5)
            if self.type(self.LAST_NAME, Config.GUEST_LAST_NAME):
                print(f"  ✓ Last Name: {Config.GUEST_LAST_NAME}")
            
            time.sleep(0.5)
            if self.type(self.EMAIL, Config.GUEST_EMAIL):
                print(f"  ✓ Email: {Config.GUEST_EMAIL}")
            
            time.sleep(0.5)
            if self.type(self.MOBILE, Config.GUEST_MOBILE):
                print(f"  ✓ Mobile: {Config.GUEST_MOBILE}")
            
            return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def click_pay_now(self):
        """Click Pay Now"""
        print("\n[Step 3] Looking for Pay Now button...")
        
        try:
            time.sleep(3)
            
            pay_now_selectors = [
                self.PAY_NOW,
                self.PAY_NOW_ALT,
                (By.XPATH, "//button[contains(text(),'Pay Now')]"),
                (By.XPATH, "//button[contains(text(),'pay now')]"),
            ]
            
            for scroll_amount in [300, 600, 900]:
                self.scroll_by(scroll_amount)
                time.sleep(0.5)
                
                for i, selector in enumerate(pay_now_selectors):
                    try:
                        element = self.find(selector)
                        if element and element.is_displayed():
                            try:
                                element.click()
                                print("  ✓ Pay Now clicked")
                                time.sleep(2)
                                return True
                            except:
                                pass
                            
                            try:
                                self.driver.execute_script("arguments[0].click();", element)
                                print("  ✓ Pay Now clicked (JS)")
                                time.sleep(2)
                                return True
                            except:
                                pass
                    except:
                        continue
            
            all_buttons = self.finds((By.TAG_NAME, "button"))
            for btn in all_buttons:
                try:
                    if "pay" in btn.text.lower():
                        self.driver.execute_script("arguments[0].click();", btn)
                        print(f"  ✓ Clicked: '{btn.text}'")
                        time.sleep(2)
                        return True
                except:
                    continue
            
            print("  ✗ Pay Now button not found")
            self.screenshot("pay_now_not_found")
            return False
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def select_upi_payment(self):
        """Select UPI payment option"""
        print("\n[Step 4] Selecting UPI payment method...")
        
        try:
            time.sleep(3)
            
            upi_element = self.wait.wait_for_visible(self.UPI_CONTAINER)
            
            if upi_element:
                self.scroll_to(self.UPI_CONTAINER)
                time.sleep(0.5)
                
                if self.click(self.UPI_CONTAINER):
                    print("  ✓ UPI payment method selected")
                    time.sleep(1)
                    return True
            
            upi_elements = self.finds((By.CSS_SELECTOR, ".paymode__container__038c1"))
            
            for elem in upi_elements:
                try:
                    if "upi" in elem.text.lower():
                        self.driver.execute_script("arguments[0].click();", elem)
                        print("  ✓ UPI selected (text match)")
                        time.sleep(1)
                        return True
                except:
                    continue
            
            print("  ✗ UPI payment method not found")
            self.screenshot("upi_not_found")
            return False
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def enter_upi_id(self):
        """Enter UPI ID - tries multiple locator strategies"""
        print("\n[Step 5] Entering UPI ID...")
        
        try:
            time.sleep(3)
            
            # Strategy 1: data-testid
            upi_input = self.wait.wait_for_visible(self.UPI_INPUT_TESTID)
            
            if upi_input:
                self.scroll_to(self.UPI_INPUT_TESTID)
                time.sleep(0.5)
                
                try:
                    upi_input.clear()
                    upi_input.send_keys(Config.UPI_ID)
                    print(f"  ✓ UPI ID entered: {Config.UPI_ID}")
                    time.sleep(1)
                    return True
                except Exception as e:
                    print(f"  ⚠️ testid method failed: {e}")
            
            # Strategy 2: name attribute
            try:
                upi_input = self.find(self.UPI_INPUT_NAME)
                if upi_input and upi_input.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", upi_input)
                    time.sleep(0.5)
                    upi_input.clear()
                    upi_input.send_keys(Config.UPI_ID)
                    print(f"  ✓ UPI ID entered: {Config.UPI_ID}")
                    time.sleep(1)
                    return True
            except:
                pass
            
            # Strategy 3: ID attribute
            try:
                upi_input = self.find(self.UPI_INPUT_ID)
                if upi_input and upi_input.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", upi_input)
                    time.sleep(0.5)
                    upi_input.clear()
                    upi_input.send_keys(Config.UPI_ID)
                    print(f"  ✓ UPI ID entered: {Config.UPI_ID}")
                    time.sleep(1)
                    return True
            except:
                pass
            
            # Strategy 4: Generic search
            all_inputs = self.finds((By.TAG_NAME, "input"))
            
            for inp in all_inputs:
                try:
                    inp_id = inp.get_attribute("id") or ""
                    inp_name = inp.get_attribute("name") or ""
                    inp_testid = inp.get_attribute("data-testid") or ""
                    
                    if ("upi" in inp_id.lower() or "upi" in inp_name.lower() or "upi" in inp_testid.lower()):
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", inp)
                        time.sleep(0.5)
                        inp.clear()
                        inp.send_keys(Config.UPI_ID)
                        print(f"  ✓ UPI ID entered: {Config.UPI_ID}")
                        time.sleep(1)
                        return True
                except:
                    continue
            
            # Strategy 5: JavaScript
            js_selectors = [
                "[data-testid='upi-collect-upi-id-input']",
                "input[name*='UPI_COLLECT']",
                "input[id*='UPI_COLLECT']"
            ]
            
            for selector in js_selectors:
                script = f"""
                    var input = document.querySelector("{selector}");
                    if (input) {{
                        input.value = '{Config.UPI_ID}';
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                """
                
                result = self.driver.execute_script(script)
                if result:
                    print(f"  ✓ UPI ID entered (JavaScript): {Config.UPI_ID}")
                    time.sleep(1)
                    return True
            
            print("  ✗ UPI input field not found")
            self.screenshot("upi_input_not_found")
            return False
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def send_payment_request(self):
        """Click Send Payment Request button"""
        print("\n[Step 6] Sending payment request...")
        
        try:
            time.sleep(2)
            
            send_button = self.wait.wait_for_clickable(self.UPI_SEND_BUTTON)
            
            if send_button:
                self.scroll_to(self.UPI_SEND_BUTTON)
                time.sleep(0.5)
                
                if self.click(self.UPI_SEND_BUTTON):
                    print("  ✓ Payment request sent!")
                    time.sleep(2)
                    return True
                
                try:
                    btn = self.find(self.UPI_SEND_BUTTON)
                    if btn:
                        self.driver.execute_script("arguments[0].click();", btn)
                        print("  ✓ Payment request sent (JS)")
                        time.sleep(2)
                        return True
                except:
                    pass
            
            all_buttons = self.finds((By.TAG_NAME, "button"))
            
            for btn in all_buttons:
                try:
                    btn_text = btn.text.lower()
                    if "send" in btn_text or "payment" in btn_text or "request" in btn_text:
                        self.driver.execute_script("arguments[0].click();", btn)
                        print(f"  ✓ Clicked: '{btn.text}'")
                        time.sleep(2)
                        return True
                except:
                    continue
            
            print("  ✗ Send payment button not found")
            self.screenshot("send_button_not_found")
            return False
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def wait_for_payment_status(self):
        """
        Wait for payment confirmation for 30 seconds
        Does NOT take screenshot - that happens later with booking ID
        Returns: tuple (status, message)
            status: 'success' or 'timeout'
            message: descriptive message
        """
        print("\n[Step 7] Waiting for payment confirmation...")
        print(f"  ⏳ Waiting for {Config.PAYMENT_WAIT_TIMEOUT} seconds")
        print(f"  🔄 Checking every {Config.PAYMENT_CHECK_INTERVAL} seconds")
        
        start_time = time.time()
        check_count = 0
        payment_confirmed = False
        
        try:
            while (time.time() - start_time) < Config.PAYMENT_WAIT_TIMEOUT:
                check_count += 1
                elapsed = int(time.time() - start_time)
                
                if check_count % 2 == 0:  # Print every 10 seconds (2 checks * 5 seconds)
                    remaining = Config.PAYMENT_WAIT_TIMEOUT - elapsed
                    print(f"  ⏱️  Waiting... ({elapsed}s elapsed, {remaining}s remaining)")
                
                # Check for success indicators
                for indicator in self.PAYMENT_SUCCESS_INDICATORS:
                    try:
                        element = self.find(indicator)
                        if element and element.is_displayed():
                            success_text = element.text if element.text else "Payment confirmed"
                            print(f"\n  ✅ PAYMENT CONFIRMED!")
                            print(f"     Message: {success_text}")
                            payment_confirmed = True
                            break
                    except:
                        continue
                
                if payment_confirmed:
                    break
                
                # Check page source for keywords as fallback
                page_source = self.driver.page_source.lower()
                success_keywords = ['payment successful', 'payment complete', 'booking confirmed', 'transaction successful']
                
                for keyword in success_keywords:
                    if keyword in page_source:
                        print(f"\n  ✅ PAYMENT CONFIRMED (detected via page source)")
                        print(f"     Keyword found: {keyword}")
                        payment_confirmed = True
                        break
                
                if payment_confirmed:
                    break
                
                # Wait before next check
                time.sleep(Config.PAYMENT_CHECK_INTERVAL)
            
            # After waiting period
            elapsed = int(time.time() - start_time)
            
            if payment_confirmed:
                print(f"  ✅ Payment confirmed in {elapsed} seconds")
                return 'success', f"Payment confirmed in {elapsed} seconds"
            else:
                print(f"\n  ⏱️  {Config.PAYMENT_WAIT_TIMEOUT} seconds elapsed")
                print(f"  ℹ️  Payment status unknown - will check after popup close")
                return 'timeout', f"Waited {Config.PAYMENT_WAIT_TIMEOUT} seconds - status unknown"
            
        except Exception as e:
            print(f"\n  ❌ ERROR while waiting for payment: {e}")
            return 'error', f"Error while waiting: {str(e)}"

    def close_popup_if_present(self):
        """
        Close popup if it appears after payment confirmation
        Returns: True if popup was closed, False if no popup found
        """
        print("\n[Step 8] Checking for popup...")
        
        try:
            time.sleep(2)  # Wait for potential popup to appear
            
            # Try multiple selectors
            close_selectors = [
                self.CLOSE_POPUP,
                self.CLOSE_POPUP_ALT,
                self.CLOSE_POPUP_ALT2,
                self.CLOSE_POPUP_ALT3,
            ]
            
            for selector in close_selectors:
                try:
                    close_button = self.find(selector)
                    if close_button and close_button.is_displayed():
                        print(f"  ✓ Popup found - closing it...")
                        
                        # Try clicking
                        try:
                            close_button.click()
                            time.sleep(1)
                            print(f"  ✓ Popup closed successfully")
                            return True
                        except:
                            # JavaScript fallback
                            self.driver.execute_script("arguments[0].click();", close_button)
                            time.sleep(1)
                            print(f"  ✓ Popup closed successfully (JS)")
                            return True
                except:
                    continue
            
            # Try finding any close button with common attributes
            all_buttons = self.finds((By.TAG_NAME, "button"))
            for btn in all_buttons:
                try:
                    data_testid = btn.get_attribute("data-testid") or ""
                    data_cy = btn.get_attribute("data-cy") or ""
                    class_name = btn.get_attribute("class") or ""
                    
                    if ("close" in data_testid.lower() or 
                        "close" in data_cy.lower() or 
                        "close" in class_name.lower()):
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1)
                        print(f"  ✓ Popup closed (found close button)")
                        return True
                except:
                    continue
            
            print(f"  ℹ️  No popup found - continuing...")
            return False
            
        except Exception as e:
            print(f"  ⚠️  Error checking for popup: {e}")
            return False

    def extract_booking_id(self):
        """
        Extract booking ID from the confirmation page
        Takes ONE screenshot at the end with booking ID as filename
        Returns: booking_id (string) or None
        """
        print("\n[Step 9] Extracting Booking ID...")
        
        try:
            time.sleep(2)  # Wait for page to load
            
            booking_id = None
            
            # Try primary selector
            booking_id_selectors = [
                self.BOOKING_ID,
                self.BOOKING_ID_ALT,
            ]
            
            for selector in booking_id_selectors:
                try:
                    elements = self.finds(selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            # Check if it looks like a booking ID (contains numbers/alphanumeric)
                            if text and any(char.isdigit() for char in text):
                                print(f"  ✓ Booking ID found: {text}")
                                booking_id = text
                                break
                    
                    if booking_id:
                        break
                except:
                    continue
            
            # Fallback: Search page source for booking ID patterns
            if not booking_id:
                print(f"  ℹ️  Searching page source for booking ID...")
                page_source = self.driver.page_source
                
                # Common booking ID patterns
                import re
                patterns = [
                    r'Booking ID[:\s]+([A-Z0-9]{6,})',
                    r'Booking Number[:\s]+([A-Z0-9]{6,})',
                    r'Confirmation Number[:\s]+([A-Z0-9]{6,})',
                    r'Reference[:\s]+([A-Z0-9]{6,})',
                    r'Order ID[:\s]+([A-Z0-9]{6,})',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_source, re.IGNORECASE)
                    if match:
                        booking_id = match.group(1)
                        print(f"  ✓ Booking ID found (regex): {booking_id}")
                        break
            
            # Try finding all elements with latoBlack class
            if not booking_id:
                all_elements = self.finds((By.CSS_SELECTOR, "[class*='latoBlack']"))
                for elem in all_elements:
                    try:
                        text = elem.text.strip()
                        if text and len(text) >= 6 and any(char.isdigit() for char in text):
                            print(f"  ✓ Potential Booking ID: {text}")
                            booking_id = text
                            break
                    except:
                        continue
            
            # NOW take the single screenshot
            print(f"\n  📸 Taking final screenshot...")
            if booking_id:
                # Screenshot with booking ID as name
                self.screenshot(f"booking_id_{booking_id}")
                print(f"  ✅ Screenshot saved with booking ID: {booking_id}")
                return booking_id
            else:
                # Screenshot showing booking ID not found
                self.screenshot("booking_id_not_found")
                print(f"  ✗ Booking ID not found")
                return None
            
        except Exception as e:
            print(f"  ✗ Error extracting booking ID: {e}")
            self.screenshot("booking_id_error")
            return None

    def extract_price(self):
        """
        Extract booking price from the confirmation page
        Returns: price (string) or None
        """
        print("\n[Step 10] Extracting Price...")
        
        try:
            time.sleep(1)  # Wait briefly
            
            price = None
            
            # Try primary selector
            price_selectors = [
                self.PRICE,
                self.PRICE_ALT,
            ]
            
            for selector in price_selectors:
                try:
                    elements = self.finds(selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            # Check if it looks like a price (contains numbers and currency symbols)
                            if text and (any(char.isdigit() for char in text) or '₹' in text or 'Rs' in text.upper()):
                                print(f"  ✓ Price found: {text}")
                                price = text
                                break
                    
                    if price:
                        break
                except:
                    continue
            
            # Fallback: Search for price in page source
            if not price:
                print(f"  ℹ️  Searching page source for price...")
                page_source = self.driver.page_source
                
                # Common price patterns
                import re
                patterns = [
                    r'₹\s*([0-9,]+(?:\.[0-9]{2})?)',
                    r'Rs\.?\s*([0-9,]+(?:\.[0-9]{2})?)',
                    r'INR\s*([0-9,]+(?:\.[0-9]{2})?)',
                    r'Total[:\s]+₹?\s*([0-9,]+(?:\.[0-9]{2})?)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_source, re.IGNORECASE)
                    if match:
                        price = f"₹{match.group(1)}"
                        print(f"  ✓ Price found (regex): {price}")
                        break
            
            # Try finding elements with price-related classes
            if not price:
                price_elements = self.finds((By.CSS_SELECTOR, "[class*='price'], [class*='amount'], [class*='total']"))
                for elem in price_elements:
                    try:
                        text = elem.text.strip()
                        if text and ('₹' in text or 'Rs' in text.upper()) and any(char.isdigit() for char in text):
                            print(f"  ✓ Price found (class search): {text}")
                            price = text
                            break
                    except:
                        continue
            
            if price:
                return price
            else:
                print(f"  ✗ Price not found")
                return None
            
        except Exception as e:
            print(f"  ✗ Error extracting price: {e}")
            return None


# =========================================================
# BOOKING AUTOMATION
# =========================================================

def process_single_booking(booking_data, driver, hotel_page, booking_page):
    """Process a single booking"""
    try:
        print("\n" + "="*70)
        print(f" PROCESSING BOOKING - Row {booking_data['row_number']}")
        print("="*70)
        
        # Load booking data into Config
        checkin, checkout = load_booking_from_dict(booking_data)
        
        # Display booking details
        print(f"  Hotel ID: {Config.HOTEL_ID}")
        print(f"  City: {Config.CITY_CODE}")
        print(f"  Check-in: {checkin.strftime('%B %d, %Y')}")
        print(f"  Check-out: {checkout.strftime('%B %d, %Y')}")
        print(f"  Guests: {Config.ADULTS} adults, {Config.CHILDREN} children")
        print(f"  Rooms: {Config.ROOMS}")
        print(f"  Guest: {Config.GUEST_FIRST_NAME} {Config.GUEST_LAST_NAME}")
        print(f"  UPI ID: {Config.UPI_ID}")
        
        # Build URL and navigate
        hotel_url = build_hotel_url()
        print(f"\n🌐 Opening hotel page...")
        driver.get(hotel_url)
        time.sleep(5)
        
        # Execute booking flow
        if not hotel_page.click_book_now():
            print("\n⚠️  SKIPPING BOOKING - Book Now button not found")
            print("   Moving to next booking...")
            return False, "Skipped - Book Now button not found", 'skipped', None, None
        
        if not booking_page.enter_guest_details():
            return False, "Failed to enter guest details", None, None, None
        
        if not booking_page.click_pay_now():
            return False, "Pay Now button not found", None, None, None
        
        if not booking_page.select_upi_payment():
            return False, "UPI option not found", None, None, None
        
        if not booking_page.enter_upi_id():
            return False, "Failed to enter UPI ID", None, None, None
        
        if not booking_page.send_payment_request():
            return False, "Failed to send payment request", None, None, None
        
        # *** NEW: Wait for payment confirmation (15 seconds) ***
        payment_status, payment_message = booking_page.wait_for_payment_status()
        
        booking_id = None
        price = None
        
        if payment_status == 'success':
            print("\n✅ BOOKING COMPLETED SUCCESSFULLY!")
            print(f"  💳 {payment_message}")
            
            # Close popup if present
            booking_page.close_popup_if_present()
            
            # Extract booking ID
            booking_id = booking_page.extract_booking_id()
            
            # Extract price
            price = booking_page.extract_price()
            
            if booking_id:
                return True, "Success - Payment Confirmed", payment_status, booking_id, price
            else:
                return True, "Success - Booking ID not found", payment_status, None, price
            
        elif payment_status == 'timeout':
            print("\n⏱️  15 SECONDS ELAPSED!")
            print(f"  💳 {payment_message}")
            print(f"  📸 Screenshot will be taken after extracting booking ID")
            
            # Still try to close popup and get booking ID
            booking_page.close_popup_if_present()
            booking_id = booking_page.extract_booking_id()
            price = booking_page.extract_price()
            
            return True, "Completed - Verify payment manually", payment_status, booking_id, price
            
        else:  # error
            print("\n❌ ERROR DURING WAIT!")
            print(f"  💳 {payment_message}")
            return False, f"Error - {payment_message}", payment_status, None, None
        
    except Exception as e:
        print(f"\n❌ BOOKING FAILED: {e}")
        return False, str(e), 'error', None, None


# =========================================================
# MAIN EXECUTION
# =========================================================

def main():
    print("\n" + "="*70)
    print(" MAKEMYTRIP AUTOMATION - GOOGLE SHEETS + SCRAPINGBEE")
    print(" Automated Bulk Booking with India Premium Proxies")
    print(" ✨ 15s Payment Wait | Booking ID | Price | Auto Status Update")
    print("="*70 + "\n")
    
    # Get Google Sheet URL
    print("--- GOOGLE SHEET CONFIGURATION ---")
    default_url = os.getenv("SHEET_URL", "")
    if default_url:
        print(f"Default sheet (from .env): {default_url[:60]}...")
    sheet_url = input(f"\nEnter Google Sheet URL (or press Enter to use .env default): ").strip()

    if not sheet_url:
        if default_url:
            sheet_url = default_url
            print(f"✓ Using sheet from .env")
        else:
            print("❌ No sheet URL provided and SHEET_URL not set in .env")
            return
    
    Config.SHEET_URL = sheet_url
    
    # Payment waiting configuration
    print("\n--- PAYMENT WAITING CONFIGURATION ---")
    print(f"✓ Will wait {Config.PAYMENT_WAIT_TIMEOUT} seconds after payment request")
    print(f"✓ Screenshot will be taken after {Config.PAYMENT_WAIT_TIMEOUT} seconds")
    print(f"✓ Checking for confirmation every {Config.PAYMENT_CHECK_INTERVAL} seconds")
    
    # ScrapingBee configuration
    print("\n--- PROXY CONFIGURATION ---")
    use_proxy = input("Do you want to use proxy? (yes/no): ").strip().lower()
    
    if use_proxy in ['yes', 'y']:
        print(f"\n🐝 ScrapingBee: ENABLED")
        print(f"   Country: India | Premium: True | JS Rendering: True")
        USE_PROXY_FLAG = True
    else:
        print(f"\n🚫 Proxy: DISABLED (Direct connection)")
        USE_PROXY_FLAG = False

    # Connect to Google Sheets
    print("\n🔗 Connecting to Google Sheets...")
    print("\n  ℹ️  GOOGLE SHEETS WRITE ACCESS:")
    print("     To write booking IDs directly to Google Sheets, add 'credentials.json'")
    print("     Without it, booking IDs will be saved in local data only")
    print("     (Sheet must still be shared publicly for reading)\n")
    
    sheets_manager = GoogleSheetsManager(Config.SHEET_URL)
    
    # Get pending bookings
    print("\n📋 Loading pending bookings...")
    bookings = sheets_manager.get_pending_bookings()
    
    if not bookings:
        print("\n⚠️  No pending bookings found!")
        print("   Make sure your sheet has:")
        print("   - 'Status' column with 'Pending' or empty")
        print("   - Required columns: Hotel ID, City Code, etc.")
        return
    
    print(f"\n✅ Found {len(bookings)} pending bookings")
    
    # Confirm
    confirm = input(f"\n✅ Process {len(bookings)} bookings? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled.")
        return
    
    # Setup Chrome
    print("\n🔧 Initializing browser...")
    driver = setup_driver_with_scrapingbee(USE_PROXY_FLAG)
    
    # Initialize pages
    hotel_page = HotelPage(driver)
    booking_page = BookingPage(driver)
    
    # Process each booking
    results = []
    
    for i, booking in enumerate(bookings, 1):
        print(f"\n{'='*70}")
        print(f" BOOKING {i}/{len(bookings)}")
        print(f"{'='*70}")
        
        success, message, payment_status, booking_id, price = process_single_booking(
            booking, 
            driver, 
            hotel_page, 
            booking_page
        )
        
        # Determine status based on result
        if payment_status == 'skipped':
            status = 'Skipped'
        elif success and booking_id:
            status = 'Completed'
        elif success:
            status = 'Pending Verification'
        else:
            status = 'Failed'
        
        # Update Google Sheet with all data
        print(f"\n📝 Updating Google Sheet for row {booking['row_number']}...")
        
        # Update Status
        sheets_manager.update_status(booking['row_number'], status)
        
        # Update Booking ID if available
        if booking_id:
            sheets_manager.update_booking_id(booking['row_number'], booking_id)
        
        # Update Price if available
        if price:
            sheets_manager.update_price(booking['row_number'], price)
        
        results.append({
            'row': booking['row_number'],
            'success': success,
            'message': message,
            'payment_status': payment_status,
            'booking_id': booking_id,
            'price': price,
            'status': status
        })
        
        # Wait between bookings - automatically proceed after 90 second wait
        if i < len(bookings):
            print(f"\n⏳ Waiting 10 seconds before next booking...")
            time.sleep(10)
    
    # Summary
    print("\n" + "="*70)
    print(" AUTOMATION SUMMARY")
    print("="*70)
    
    successful = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'] and r.get('payment_status') != 'skipped')
    skipped = sum(1 for r in results if r.get('payment_status') == 'skipped')
    
    print(f"  Total Bookings: {len(results)}")
    print(f"  ✅ Successful: {successful}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Failed: {failed}")
    
    # Payment status breakdown
    payment_confirmed = sum(1 for r in results if r.get('payment_status') == 'success')
    payment_unknown = sum(1 for r in results if r.get('payment_status') == 'timeout')
    
    print(f"\n  Payment Status Breakdown:")
    print(f"  💚 Confirmed within 15s: {payment_confirmed}")
    print(f"  ⏱️  Status Unknown (verify manually): {payment_unknown}")
    
    # Booking IDs captured
    booking_ids_found = sum(1 for r in results if r.get('booking_id'))
    prices_found = sum(1 for r in results if r.get('price'))
    
    print(f"\n  Data Captured:")
    print(f"  🎫 Booking IDs: {booking_ids_found}/{len(results)}")
    print(f"  💰 Prices: {prices_found}/{len(results)}")
    
    if booking_ids_found > 0:
        print(f"\n  Booking Details:")
        for r in results:
            if r.get('booking_id'):
                price_str = f" | Price: {r['price']}" if r.get('price') else ""
                status_str = f" | Status: {r.get('status', 'Unknown')}"
                print(f"    - Row {r['row']}: {r['booking_id']}{price_str}{status_str}")
    
    if skipped > 0:
        print("\n  Skipped Bookings:")
        for r in results:
            if r.get('payment_status') == 'skipped':
                print(f"    - Row {r['row']}: {r['message']}")
    
    if failed > 0:
        print("\n  Failed Bookings:")
        for r in results:
            if not r['success'] and r.get('payment_status') != 'skipped':
                print(f"    - Row {r['row']}: {r['message']}")
    
    print("\n⏳ Browser will stay open for 30 seconds...")
    time.sleep(30)
    
    # Cleanup
    print("\n🔒 Closing browser...")
    driver.quit()
    print("✅ Done!\n")


if __name__ == "__main__":
    main()
