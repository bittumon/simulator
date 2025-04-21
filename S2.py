import imaplib
import email
from email.header import decode_header
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pyperclip
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from openpyxl import Workbook
import pandas as pd
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import traceback
import pdfkit
import re
from html import unescape

def extract_clean_link(body, pattern):
    # Extract the link using regex
    match = re.search(pattern, body)
    if match:
        raw_link = match.group(1)
        # Unescape any HTML-encoded characters
        cleaned_link = unescape(raw_link)
        # Remove any trailing or surrounding unwanted characters
        cleaned_link = cleaned_link.split('">')[0]  # Remove extra `">`
        return cleaned_link
    return None

from jinja2 import Environment, FileSystemLoader

LOG_FILE = "program_log.txt"



today = datetime.now()
day= today.strftime("%d/%m/%Y")  # Today's date in dd/mm/yyyy format
yesterday = today - timedelta(days=1)


yday = yesterday.strftime("%d/%m/%Y")  # Yesterday's date

# Function to log events
def log_event(status, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} - {status}: {message}\n")

# Function to send email with attachments
def send_email(subject, body, to_email, cc_email=None, attachments=None):
    try:
        sender_email = "bittumon@myenergy.it"
        password = "ttmphkfifekffylo"  # App password

        # Set up the email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        if cc_email:
            msg["Cc"] = cc_email
        msg["Subject"] = subject
        
        # Attach the body text
        msg.attach(MIMEText(body, "html"))

        # Attach files
        if attachments:
            for file in attachments:
                with open(file, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file)}")
                    msg.attach(part)

        # Send the email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)

        log_event("SUCCESS", f"Email sent to {to_email} with subject '{subject}'")

    except Exception as e:
        log_event("ERROR", f"Failed to send email: {str(e)}")
        raise

# Function to create a PDF from data
def create_pdf(data, html_content, output_filename, email_date):
    try:
        # Add email_date to data dictionary
        data["yesterdaysDate"] = email_date

        # Replace placeholders in the HTML string with actual data
        for key, value in data.items():
            placeholder = f"{{{{ {key} }}}}"  # e.g., {{ key }}
            html_content = html_content.replace(placeholder, str(value) if value is not None else "N/A")

        # Debug rendered HTML
        print("Rendered HTML preview (first 500 characters):")
        print(html_content[:500])  # Show the first 500 characters for verification

        # Path to wkhtmltopdf executable
        config = pdfkit.configuration(wkhtmltopdf=r'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')

        # Convert HTML to PDF using pdfkit
        pdfkit.from_string(html_content, output_filename, configuration=config)
        print(f"PDF generated successfully: {output_filename}")
        return output_filename

    except Exception as e:
        print(f"An error occurred during PDF generation: {e}")
        raise

# Wrap main logic in try-except to handle errors

def get_email_link(user, password, sender_email, subject_keyword):
    """Fetch the link and date from emails using IMAP based on sender and subject."""
    # Connect to Gmail IMAP server
    imap_url = 'imap.gmail.com'
    mail = imaplib.IMAP4_SSL(imap_url)

    try:
        # Log in using provided credentials
        mail.login(user, password)
        print("Logged in successfully.")

        # Select the mailbox (default is "INBOX")
        mail.select("inbox")

        # Search for emails with the specified sender and subject
        date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        search_query = f'(FROM "{sender_email}" SUBJECT "{subject_keyword}" SINCE {date_since})'
        status, messages = mail.search(None, search_query)

        # Get the list of email IDs
        email_ids = messages[0].split()
        if not email_ids:
            print(f"No matching emails found for subject: '{subject_keyword}'")
            return None, None

        # Fetch the latest email
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

        # Parse the email content
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # Decode email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                print(f"Processing email with subject: {subject}")

                # Extract the email date
                raw_date = msg["Date"]
                email_date = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S %z").date()

                # Check if the email has a multipart payload
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            # Decode the email body
                            body = part.get_payload(decode=True).decode()
                            print(f"Email body preview (first 200 chars): {body[:200]}...")

                            # Use the updated link extraction logic
                            pattern = r'(https?://\S*isolarcloud\S*)'
                            link = extract_clean_link(body, pattern)
                            if link:
                                print(f"Link found: {link}")
                                return link, email_date.strftime("%d-%m-%Y")
                else:
                    # Handle non-multipart emails
                    body = msg.get_payload(decode=True).decode()
                    print(f"Email body preview (first 200 chars): {body[:200]}...")

                    # Use the updated link extraction logic
                    pattern = r'(https?://\S*isolarcloud\S*)'
                    link = extract_clean_link(body, pattern)
                    if link:
                        print(f"Link found: {link}")
                        return link, email_date.strftime("%d-%m-%Y")

        print(f"No link found in email for subject: '{subject_keyword}'")
        return None, None

    finally:
        # Logout from the mail server
        mail.logout()

def fetch_data_from_link(link,link2,output_filename):
    """Fetch and parse data from the dynamic content of Link 1 using Selenium."""
    # Configure Selenium WebDriver
    option = Options()
    option.add_argument("--headless")  # Run browser in headless mode
    option.add_argument("--disable-gpu")
    option.add_argument("--no-sandbox")
    option.add_argument("--disable-dev-shm-usage")

    # Update the path to ChromeDriver
    service = Service(r'C:Users\lcd-user\source\repos\datalogger sunguard\chromedriver')  # Replace with your ChromeDriver path  r'C:\Users\Bittu\Projetto Python\email scrapper without assignment\Log\[...]
    option = webdriver.FirefoxOptions()
    option.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
    driverService = Service(r'C:\Users\Bittu\Projetto Python\email scrapper without assignment\Log\geckodriver.exe')
    driver = webdriver.Firefox(service=driverService, options=option)


   
    # Load the link
    driver.get(link)

    # Wait for the main content to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div/div[1]/div[3]/div[3]/div[3]/table/tbody/tr/td[5]/div"))
    )

    # Extract elements using XPath
    data = {
        "yieldToday": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/table/tr[1]/td[2]").text,
        "totalYield": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/table/tr[1]/td[4]").text,
        "co2ReductionToday": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/table/tr[1]/td[6]").text,
        "totalCO2Reduction": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/table/tr[1]/td[8]").text,
        "cumulativeTotalRevenue": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/table/tr[3]/td[2]").text,
        "revenueToday": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/table/tr[2]/td[2]").text,
        "cumulativeRevenue": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/div[3]/div[3]/table/tbody/tr/td[2]/div").text,
        "plantName": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/div[3]/div[3]/table/tbody/tr/td[3]/div").text,
        "installedPower": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/div[3]/div[3]/table/tbody/tr/td[3]/div").text,
        "yieldTodayPlant": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/div[3]/div[3]/table/tbody/tr/td[4]/div").text,
        "totalYieldPlant": driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/div[3]/div[3]/table/tbody/tr/td[5]/div").text,

    }


    # Convert financial values to EUR 
    data["revenueToday"] = convert_to_euro(data["revenueToday"])
    data["cumulativeTotalRevenue"] = convert_to_euro(data["cumulativeTotalRevenue"])

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    data["todaysDate"] = today.strftime("%d/%m/%Y")  # Today's date in dd/mm/yyyy format
    data["yesterdaysDate"] = yesterday.strftime("%d/%m/%Y")  # Yesterday's date

    print("Extracted Data:", data, today,yesterday)

    driver.implicitly_wait(3)
    # Load the link2
    driver.get(link2)
    driver.refresh()
    driver.refresh()

    time.sleep(2)  # Allow the page to load completely

    # Use Ctrl + A to select all text
    body_element = driver.find_element("tag name", "body")
    body_element.send_keys(Keys.CONTROL, 'a')  # For Mac, replace with Keys.COMMAND

    # Use Ctrl + C to copy the selected text
    body_element.send_keys(Keys.CONTROL, 'c')  # For Mac, replace with Keys.COMMAND

    # Wait a moment for the clipboard operation to complete
    time.sleep(2)

    # Retrieve copied content from clipboard
    copied_text = pyperclip.paste()

    # Print or process the copied content
    print("Copied text:\n", copied_text)

    # Close the browser
    driver.quit()

    # Generate today's date for file and sheet name
    today2 = datetime.today().strftime('%d-%m-%Y')
    file_name = f"Ta Cenc 4 Production data -{today2}.xlsx"
    sheet_name = today2

    # Process text and create Excel file
    process_text_to_excel(copied_text, output_filename, sheet_name)

    return data

# Conversion rate for MTL to EUR
conversion_rate_to_euro = 1

# Function to extract numeric value and convert to EUR
def convert_to_euro(value):
    if value and "MTL" in value:
        numeric_value = float(value.split()[0].replace(",", ""))
        return round(numeric_value * conversion_rate_to_euro, 2)
    return None



def process_text_to_excel(input_text, file_name, sheet_name):
    # Split the input text by lines and clean up unnecessary whitespace
    lines = [line.strip() for line in input_text.splitlines() if line.strip()]
    
    # Extract headers
    headers = ["Name", "Time", "Daily Yield(kWh)", "Daily Equivalent Hours(h)"]
    
    # Extract table rows
    data2 = []
    for i in range(len(headers), len(lines), 4):  # Data is grouped in blocks of 4
        try:
            name = lines[i + 3]
            time = lines[i]
            daily_yield = lines[i + 1]
            daily_hours = lines[i + 2]
            data2.append([name, time, daily_yield, daily_hours])
        except IndexError:
            break  # Stop if there's an incomplete row at the end

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(data2, columns=headers)

    # Reset the index to ensure sequential numbering
    df.reset_index(drop=True, inplace=True)

    # Delete rows 2 and 3 (Python indexing starts from 0)
    df = df.drop(index=[0,1], errors='ignore')
    
    # Save to Excel file
    df.to_excel(file_name, index=False, sheet_name=sheet_name)
    print(f"Excel file '{file_name}' created successfully!")



def main():
    try:
        user = 'bittumon@myenergy.it'
        password = 'ttmphkfifekffylo'

        today = datetime.now()
        day= today.strftime("%d-%m-%Y")  # Today's date in dd/mm/yyyy format
        yesterday = today - timedelta(days=1)
        yday = yesterday.strftime("%d-%m-%Y")  # Yesterday's date
        name = f"Ta Cenc 4 Production data -{yday}.xlsx"
        output_filename = f"Ta Cenc 4 Daily Report-{yday}.pdf"


        sender_email = "system@isolarcloud.com"
        subject_daily_report = "Daily Report"
        subject_daily_plant_report = "Daily Plant Report"

        # Fetch Link 1
        link1, email_date = get_email_link(user, password, sender_email, subject_daily_report)
        if link1 and email_date:
            print(f"Link: {link1}")
            print(f"Email Date: {email_date}")
        else:
            print("No matching email or link found.")

        # Fetch Link 2
        link2, email_date2 = get_email_link(user, password, sender_email, subject_daily_plant_report)
        if link2 and email_date:
            print(f"Link: {link2}")
            print(f"Email Date: {email_date2}")
        else:
            print("No matching email or link found.")


        name = f"Ta Cenc 4 Production data -{email_date}.xlsx"
        output_filename = f"Ta Cenc 4 Daily Report-{email_date}.pdf"
 
        # Fetch and parse data from Link 1
        data3 = fetch_data_from_link(link1, link2, name)

        html_content= """

        <div style="text-align: center;">
    <div style="clear:both;">
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><img src="data:image/png;base64,iVBOR[...]
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
    </div>
    <p><span style='font-family: "Times New Roman", Times, serif; font-size: 18px;'><br></span></p><span style='font-family: "Times New Roman", Times, serif; font-size: 26px;'><u><strong>&nbsp;</stron[...]
    <h1 style='margin-top:0cm;margin-right:0cm;margin-bottom:0cm;margin-left:0cm;font-size:13px;font-family:"Microsoft YaHei",sans-serif;font-weight:normal;'><span style='font-family: "Times New Roman[...]
    <table style="border: none; margin-left: 29.1pt; border-collapse: collapse; width: 94%; margin-right: calc(2%);">
        <tbody>
            <tr>
                <td style="width: 23.0252%; border: 1pt solid windowtext; background: rgb(240, 240, 240); padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:  13.4pt;margin-bottom:.0001pt;margin-left:0cm;'><span style='font-size: [...]
                </td>
                <td style="width: 10.4551%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; padding[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.1pt;'><span style='font-size: 16p[...]
                </td>
                <td style="width: 9.8858%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; backgrou[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.25pt;'><span style='font-size: 16[...]
                </td>
                <td style="width: 9.345%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; padding: [...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.3pt;'><span style='font-size: 16p[...]
                </td>
                <td style="width: 13.2395%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; backgro[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:8.35pt;margin-bottom:.0001pt;margin-left:5.0pt;line-height:65%;'><span st[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:8.35pt;margin-bottom:.0001pt;margin-left:5.0pt;line-height:65%;'><span st[...]
                </td>
                <td style="width: 9.8374%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; padding:[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.05pt;'><span style='font-size: 16[...]
                </td>
                <td style="width: 13.3138%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; backgro[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:25.75pt;margin-bottom:.0001pt;margin-left:5.0pt;line-height:65%;'><span s[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:25.75pt;margin-bottom:.0001pt;margin-left:5.0pt;line-height:65%;'><span s[...]
                </td>
                <td style="width: 10.8449%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; padding[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.05pt;'><span style='font-size: 16[...]
                </td>
            </tr>
            <tr>
                <td style="width: 23.0252%; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-left: 1pt solid windowtext; border-image: initial; border-top: none; backgro[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:25.75pt;margin-bottom:.0001pt;margin-left:5.1pt;line-height:65%;'><span s[...]
                </td>
                <td colspan="7" style="width: 76.8546%; border-top: none; border-left: none; border-bottom: 1pt solid windowtext; border-right: 1pt solid windowtext; padding: 0cm; height: 31.75pt; ver[...]
                    <p style='font-size: 15px; font-family: "Microsoft YaHei", sans-serif; margin: 8.3pt 0cm 0.0001pt 5.1pt; text-align: left;'><span style='font-size: 16px; font-family: "Times New Ro[...]
                </td>
            </tr>
            <tr>
                <td style="width: 23.0252%; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-left: 1pt solid windowtext; border-image: initial; border-top: none; backgro[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:7.95pt;margin-bottom:.0001pt;margin-left:5.1pt;line-height:65%;'><span st[...]
                </td>
                <td colspan="7" style="width: 76.8546%; border-top: none; border-left: none; border-bottom: 1pt solid windowtext; border-right: 1pt solid windowtext; padding: 0cm; height: 31.75pt; ver[...]
                    <p style='font-size: 15px; font-family: "Microsoft YaHei", sans-serif; margin: 8.3pt 0cm 0.0001pt 5.1pt; text-align: left;'><span style='font-size: 16px; font-family: "Times New Ro[...]
                </td>
            </tr>
        </tbody>
    </table>
    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;'><span style="font-size: 16px;"><br></span></p>
    <table style="margin-left: 33.75pt; border-collapse: collapse; border: none; width: 93%; margin-right: calc(2%);">
        <tbody>
            <tr>
                <td style="width: 70.9pt;border: 1pt solid windowtext;background: rgb(242, 242, 242);padding: 0cm 5.4pt;height: 32.7pt;vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman[...]
                </td>
                <td style="width: 19.5864%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; backgro[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman[...]
                </td>
                <td style="width: 17.0316%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; backgro[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>[...]
                </td>
                <td style="width: 3cm;border-top: 1pt solid windowtext;border-right: 1pt solid windowtext;border-bottom: 1pt solid windowtext;border-image: initial;border-left: none;background: rgb(24[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.45pt;text-align:  center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-fam[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.45pt;text-align:  center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-fam[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:10.65pt;text-align:  center;line-height:7.1pt;'><span style='font-size: 16px; font-family: [...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;[...]
                </td>
                <td style="width: 78pt;border-top: 1pt solid windowtext;border-right: 1pt solid windowtext;border-bottom: 1pt solid windowtext;border-image: initial;border-left: none;background: rgb(2[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.6pt;text-align:  center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-fami[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.6pt;text-align:  center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-fami[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:10.6pt;text-align:  center;line-height:7.1pt;'><span style='font-size: 16px; font-family: "[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;[...]
                </td>
                <td style="width: 77.95pt;border-top: 1pt solid windowtext;border-right: 1pt solid windowtext;border-bottom: 1pt solid windowtext;border-image: initial;border-left: none;background: rg[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.2pt;text-align:  center;line-height:12.45pt;'><span style="font-size: 16px;"><br></span><[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.2pt;text-align:  center;line-height:12.45pt;'><span style='font-size: 16px; color: rgb(51[...]
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.2pt;text-align:  center;line-height:12.45pt;'><span style='font-size: 16px; color: rgb(51[...]
                </td>
            </tr>
            <tr>
                <td style="width: 70.9pt; padding: 5px; vertical-align: top; border-left: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(33, 33, 33); font-family: "Times New Roman[...]
                </td>
                <td style="width: 19.5864%; padding: 10px; vertical-align: top; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(33, 33, 33); font-family: "Times New Roman[...]
                </td>
                <td style="width: 17.0316%; padding: 5pt; vertical-align: top; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'>{{ ins[...]
                </td>
                <td style="width: 3cm; padding: 5pt; vertical-align: middle; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'>{{ yie[...]
                </td>
                <td style="width: 78pt; padding: 10px; vertical-align: top; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(33, 33, 33); font-family: "Times New Roman[...]
                </td>
                <td style="width: 77.95pt; padding: 5pt; vertical-align: top; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'> <span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'>{{ to[...]
                </td>
            </tr>
        </tbody>
    </table>
    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'><br></span></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><span style="font-size: 16px;"><br></span></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><span style="font-size: 16px;"><br></span></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><span style="font-size: 16px;"><br></span></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>


    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
    <div style="clear:both;">
        <p style="margin-top:0pt; margin-bottom:0pt; text-align:center;"><span style='font-family: "Times New Roman", Times, serif; font-size: 12px;'><strong><span style="color: rgb(192, 80, 77);">Mye[...]
        <p style="margin-top:0pt; margin-bottom:0pt; text-align:justify; font-size:4pt;"><span style='color: rgb(196, 188, 150); font-family: "Times New Roman", Times, serif; font-size: 9px;'>Informat[...]
    </div>
</div>
<p style="bottom: 10px; right: 10px; position: absolute;"><br></p>

        """

        body2 = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ta Cenc 4 Daily Production Report</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f9; font-family: Arial, sans-serif;">
  <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border: 1px solid #ddd; text-align: center;">
    <!-- Header Section -->
    <div style="background-color: #f5f4ef; padding: 20px;">
      <img src="https://i.postimg.cc/yd33jt2P/Copy-of-icon.png" alt="Myenergy Logo" style="max-width: 180px;">
    </div>

    <!-- Content Section -->
    <div style="padding: 15px;">
      <h1 style="margin: 0; font-size: 18px; color: #4a4a4a; font-weight: bold;">Dear Client,</h1>
      <p style="font-size: 16px; color: #666666; line-height: 1.5; margin-top: 20px;">
        Please find attached daily production report of the Ta Cenc 4 plant dated <strong>{email_date}</strong>. 
        If you have any questions or need further assistance, please feel free to reach out to us.
      </p>
      <p style="font-size: 14px; color: #666666; margin-top: 2px;margin-bottom: 2px;">The Myenergy Team</p>
    </div>

    <!-- Footer Section -->
    <div style="padding: 5px; font-size: 10px; color: #999999; text-align: center;">
      <p>
        <a href="https://www.myenergy.it" target="_blank" style="color: #2f80ed; text-decoration: none; margin: 0 5px;">Myenergy</a> | 
        <a href="https://www.myenergy.it/contatti" target="_blank" style="color: #2f80ed; text-decoration: none; margin: 0 5px;">Contatti</a> | 
        <a href="https://www.myenergy.it/chi-siamo" target="_blank" style="color: #2f80ed; text-decoration: none; margin: 0 5px;">Scopri</a>
      </p>
      <div style="margin-top: 15px;">
        <p style="margin: 0; font-size: 10px; color: #666666;">
          <strong>MYENERGY S.p.A.</strong><br>
          Via Angelo Moro, 109<br>
          20097 - San Donato Milanese (MI)
        </p>
        <p style="margin: 0; font-size: 10px; color: #666666;">
          <strong>P. Iva/CF:</strong> 05528670960
        </p>
        <div style="margin-top: 8px;">
          <p style="margin: 5px 0;"><a href="tel:+39 02 3679 8760" style="color: #2f80ed; text-decoration: none;">+39 02 3679 8760</a>
           | <a href="mailto:info@myenergy.it" style="color: #2f80ed; text-decoration: none;">info@myenergy.it</a></p>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""


        # Create PDF from datato_email="powerbi@wsc.com.mt",cc_email="manutenzione@myenergy.it",

        create_pdf(data3,html_content, output_filename,email_date)

        # Send completion email
        subject = f"Ta cenc 4 Production Report - {email_date}"
        send_email(
            subject=subject,
            body=body2,
            to_email="bittumon@myenergy.it",
            cc_email="b2kbpdy@gmail.com",
            attachments=[name, output_filename]
        )

        # Delete the Excel file after sending
        os.remove(output_filename)
        os.remove(name)
        log_event("SUCCESS", "Program executed successfully.")

    except Exception as e:
        error_message = traceback.format_exc()
        log_event("ERROR", error_message)

        # Send error email
        send_email(
            subject="Program Execution Failed",
            body=f"<p>The program encountered an error:</p><pre>{error_message}</pre>",
            to_email="bittumon@myenergy.it"
        )

if __name__ == "__main__":
    main()
