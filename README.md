# MakeMyTrip Hotel Booking Automation 🏨

Automated bulk hotel booking from Google Sheets with ScrapingBee India proxies.

## ✨ Features
- Reads bookings from Google Sheets automatically
- ScrapingBee premium India proxies (anti-block)
- Auto-fills Status, Booking_id, Price in Google Sheet
- Skips hotels where Book Now is unavailable
- UPI payment automation with 15s confirmation wait
- Screenshot saved per booking (named with Booking ID)

## 📁 Project Structure
```
makemytrip-automation/
├── makemytrip_automation_updated.py  ← Main script
├── test_scrapingbee.py               ← Test ScrapingBee before running
├── requirements.txt                   ← Python dependencies
├── .env.example                       ← Copy this to .env and fill in keys
├── .gitignore                         ← Keeps secrets out of GitHub
└── README.md                          ← This file
```

> ⚠️ `credentials.json` and `.env` are NOT included (sensitive). See setup below.

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/makemytrip-automation.git
cd makemytrip-automation
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file
```bash
cp .env.example .env
```
Then open `.env` and add your ScrapingBee API key:
```
SCRAPINGBEE_API_KEY=your_api_key_here
```

### 4. Add Google Sheets credentials
- Get `credentials.json` from Google Cloud Console (Service Account)
- Place it in the project folder
- Share your Google Sheet with: `sheets-bot@high-hue-485911-n9.iam.gserviceaccount.com`

### 5. Test ScrapingBee
```bash
python test_scrapingbee.py
```

### 6. Run automation
```bash
python makemytrip_automation_updated.py
```

---

## 📋 Google Sheet Columns Required

| Column | Description |
|--------|-------------|
| Hotel ID | MakeMyTrip hotel ID |
| City Code | City code (e.g. DEL, BOM) |
| Check-in | Days from today |
| Nights | Number of nights |
| Adults | Number of adults |
| Children | Number of children |
| Rooms | Number of rooms |
| First Name | Guest first name |
| Last Name | Guest last name |
| Email | Guest email |
| Mobile | Guest mobile number |
| UPI ID | Payment UPI ID |
| Status | Auto-updated: Completed / Skipped / Failed |
| Booking_id | Auto-filled after booking |
| Price | Auto-filled after booking |

---

## 📊 Status Column Values

| Status | Meaning |
|--------|---------|
| **Completed** | Booking confirmed, ID captured |
| **Skipped** | Book Now button not found |
| **Pending Verification** | Payment sent, ID not captured |
| **Failed** | Error occurred |

---

## ⚙️ Configuration

All settings are in the `Config` class inside `makemytrip_automation_updated.py`:

```python
PAYMENT_WAIT_TIMEOUT = 15    # Seconds to wait for payment confirmation
SCRAPINGBEE_COUNTRY  = "in"  # India IPs
SCRAPINGBEE_PREMIUM  = True  # Premium rotating proxies
```

---

