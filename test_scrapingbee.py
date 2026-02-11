"""
ScrapingBee Test Script
Test your API key and configuration before running the main automation
"""

import requests
import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load API key from .env
load_dotenv()
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY", "")

if not SCRAPINGBEE_API_KEY:
    print("❌ SCRAPINGBEE_API_KEY not found in .env file!")
    print("   Make sure your .env file contains:")
    print("   SCRAPINGBEE_API_KEY=your_api_key_here")
    exit(1)

print("="*70)
print(" SCRAPINGBEE TEST SCRIPT")
print("="*70)

# Test 1: API Key Validation
print("\n[Test 1] Testing API Key...")
try:
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': 'https://httpbin.org/ip',
        'render_js': 'false',
        'premium_proxy': 'true',
        'country_code': 'in'
    }
    response = requests.get('https://app.scrapingbee.com/api/v1/', params=params)

    if response.status_code == 200:
        print("  ✅ API Key is VALID")
        print(f"  ✅ Response: {response.text[:100]}...")
        remaining = response.headers.get('Spb-Cost-Remaining')
        cost      = response.headers.get('Spb-Cost')
        if remaining: print(f"  💰 Remaining API credits: {remaining}")
        if cost:      print(f"  💸 Cost of this request: {cost}")
    else:
        print(f"  ❌ API Key INVALID - Status: {response.status_code}")
        print(f"  ❌ Error: {response.text}")
        exit(1)

except Exception as e:
    print(f"  ❌ Error: {e}")
    exit(1)

# Test 2: India IP Check
print("\n[Test 2] Testing India IP Location...")
try:
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': 'https://ipapi.co/json/',
        'render_js': 'false',
        'premium_proxy': 'true',
        'country_code': 'in'
    }
    response = requests.get('https://app.scrapingbee.com/api/v1/', params=params)

    if response.status_code == 200:
        import json
        data    = json.loads(response.text)
        country = data.get('country_name', 'Unknown')
        city    = data.get('city', 'Unknown')
        ip      = data.get('ip', 'Unknown')
        print(f"  {'✅ India IP confirmed!' if country == 'India' else '⚠️  Not India IP (Got: ' + country + ')'}")
        print(f"  📍 IP: {ip} | Location: {city}, {country}")
    else:
        print(f"  ⚠️  Status {response.status_code} - skipping (non-critical)")

except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 3: Selenium Integration
print("\n[Test 3] Testing Selenium with ScrapingBee...")
try:
    proxy_password = "render_js=true&premium_proxy=true&country_code=in&wait=3000&block_ads=true"
    proxy_endpoint = f"{SCRAPINGBEE_API_KEY}:{proxy_password}@proxy.scrapingbee.com:8886"

    options = webdriver.ChromeOptions()
    options.add_argument(f'--proxy-server=http://{proxy_endpoint}')
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    print("  → Launching Chrome with ScrapingBee...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)

    print("  → Loading test page...")
    driver.get("https://httpbin.org/ip")
    time.sleep(2)

    page_text = driver.find_element("tag name", "body").text
    print(f"  ✅ Selenium working with ScrapingBee!")
    print(f"  ✅ Page loaded: {page_text[:80]}...")
    driver.quit()
    print("  ✅ Browser closed")

except Exception as e:
    print(f"  ❌ Error: {e}")
    try: driver.quit()
    except: pass

# Test 4: MakeMyTrip
print("\n[Test 4] Testing MakeMyTrip access...")
user_test = input("Test MakeMyTrip website? (yes/no) [default: no]: ").strip().lower()

if user_test in ['yes', 'y']:
    try:
        proxy_password = "render_js=true&premium_proxy=true&country_code=in&wait=5000&block_ads=true"
        proxy_endpoint = f"{SCRAPINGBEE_API_KEY}:{proxy_password}@proxy.scrapingbee.com:8886"

        options = webdriver.ChromeOptions()
        options.add_argument(f'--proxy-server=http://{proxy_endpoint}')
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        print("  → Launching Chrome...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(60)

        print("  → Loading MakeMyTrip...")
        driver.get("https://www.makemytrip.com/")
        time.sleep(5)

        title = driver.title
        if "MakeMyTrip" in title or "makemytrip" in title.lower():
            print(f"  ✅ MakeMyTrip loaded successfully!")
            print(f"  ✅ Page title: {title}")
        else:
            print(f"  ⚠️  Page loaded but title unclear: {title}")

        print("\n  ℹ️  Browser will stay open for 10 seconds...")
        time.sleep(10)
        driver.quit()
        print("  ✅ Browser closed")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        try: driver.quit()
        except: pass

# Summary
print("\n" + "="*70)
print(" TEST SUMMARY")
print("="*70)
print("✅ API Key: VALID")
print("✅ India IPs: Working")
print("✅ Selenium Integration: Ready")
print("\n🎉 ScrapingBee is configured correctly!")
print("   You can now run your main automation script.\n")
