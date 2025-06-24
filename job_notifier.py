import os
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from twilio.rest import Client
import re

# === CONFIG ===
TELEGRAM_TOKEN = '7774649216:AAG9chKqDoOPfJkZbNfgi8Azv9t0vF2CniU'
CHAT_ID = '7047656011'  # Use @userinfobot to get it
SEARCH_CITY = 'Hyderabad'

# === TWILIO CONFIG ===
ACCOUNT_SID = os.getenv("TWILIO_SID")
AUTH_TOKEN = os.getenv("TWILIO_TOKEN")
FROM_WHATSAPP = os.getenv("WHATSAPP_FROM")
TO_WHATSAPP = os.getenv("WHATSAPP_TO")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")   # Your personal WhatsApp number (must be verified in Twilio)

# === TARGET ROLES ===
TARGET_ROLES = [
    "qa engineer", "quality analyst", "software tester", "test engineer",
    "data analyst", "data scientist", "ai engineer", "ml engineer",
    "artificial intelligence", "machine learning", "automation tester"
]
ROLES_PATTERN = re.compile("|".join(re.escape(role) for role in TARGET_ROLES), re.IGNORECASE)

# === URLS TO SCRAPE ===
URLS = [
    "https://www.freshersworld.com/jobs-in-hyderabad",
    "https://www.naukri.com/walkin-jobs-in-hyderabad",
    "https://www.shine.com/job-search/walk-in-jobs-in-hyderabad",
    "https://www.indeed.com/q-Walk-in-l-Hyderabad,-Telangana-jobs.html",
    "https://www.foundit.in/search?searchType=personalizedSearch&from=submit&geoId=105&sortBy=Relevance&start=0&jobType=walk-in",
    "https://www.tcs.com/careers",
    "https://career.infosys.com/joblist",
    "https://careers.wipro.com",
    "https://careers.techmahindra.com",
    "https://careers.cognizant.com/in/en"
]

# === BOT SETUP ===
bot = Bot(token=TELEGRAM_TOKEN)

# === SCRAPER FUNCTION ===
def scrape_jobs():
    jobs = []
    for url in URLS:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, 'html.parser')

            if "freshersworld" in url:
                listings = soup.select('div.job-container div.job-details')
                for job in listings[:5]:
                    title = job.select_one('h3').text.strip()
                    company = job.select_one('span.comp-name').text.strip()
                    location = job.select_one('span.loc').text.strip()
                    link = "https://www.freshersworld.com" + job.a['href']

                    if (SEARCH_CITY.lower() in location.lower()) and (
                        "walk-in" in title.lower() or "fresher" in title.lower() or ROLES_PATTERN.search(title)):
                        jobs.append(f"🧑‍💼 {title}\n🏢 {company}\n📍 {location}\n🔗 {link}")

            elif any(site in url for site in ["naukri", "shine", "indeed", "foundit"]):
                listings = soup.select('article.jobTuple')
                for job in listings[:5]:
                    title = job.select_one('a.title').text.strip()
                    company = job.select_one('a.subTitle').text.strip()
                    location = job.select_one('li.location span').text.strip()
                    link = job.select_one('a.title')['href']

                    if (SEARCH_CITY.lower() in location.lower()) and (
                        "walk-in" in title.lower() or "fresher" in title.lower() or ROLES_PATTERN.search(title)):
                        jobs.append(f"🧑‍💼 {title}\n🏢 {company}\n📍 {location}\n🔗 {link}")

        except Exception as e:
            print(f"Error scraping {url}: {e}")

    return jobs
    
# === LINKEDIN JOBS USING SERPAPI ===
def fetch_linkedin_jobs():
    params = {
        "engine": "linkedin_jobs",
        "q": "QA Engineer OR Data Analyst OR Data Scientist OR AI OR ML",
        "location": "Hyderabad, Telangana, India",
        "api_key": "0545887cf7de3b1ee7e38a50e1cefb1d428f9a52b291561769ad4a6ba35881fe",  # Replace with your actual SerpAPI key
        "hl": "en"
    }

    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    jobs = []
    for job in data.get("jobs_results", [])[:5]:
        title = job.get("title", "")
        company = job.get("company_name", "")
        location = job.get("location", "")
        link = job.get("link", "")

        if SEARCH_CITY.lower() in location.lower() and (
            "fresher" in title.lower() or "walk-in" in title.lower() or ROLES_PATTERN.search(title)
        ):
            jobs.append(f"🧑‍💼 {title}\n🏢 {company}\n📍 {location}\n🔗 {link}")

    return jobs


# === TELEGRAM NOTIFY FUNCTION ===
def send_notifications(jobs):
    try:
        if not jobs:
            bot.send_message(chat_id=CHAT_ID, text="No new Hyderabad walk-ins or fresher jobs found today.")
        else:
            for job in jobs:
                bot.send_message(chat_id=CHAT_ID, text=job)
    except Exception as e:
        print("Telegram Error:", e)

# === WHATSAPP NOTIFY FUNCTION ===
def send_whatsapp_notifications(jobs):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    if not jobs:
        client.messages.create(
            body="No new Hyderabad walk-in or fresher jobs found today.",
            from_=FROM_WHATSAPP,
            to=TO_WHATSAPP
        )
    else:
        for job in jobs:
            try:
                message = client.messages.create(
                    body=job,
                    from_=FROM_WHATSAPP,
                    to=TO_WHATSAPP
                )
                print("WhatsApp message sent:", message.sid)
            except Exception as e:
                print("Failed to send WhatsApp message:", e)

if __name__ == "__main__":
    job_list = scrape_jobs()

    # Add this line to include LinkedIn results
    job_list += fetch_linkedin_jobs()

    # Telegram Notification (optional)
    send_notifications(job_list)

    # WhatsApp Notification
    send_whatsapp_notifications(job_list)

