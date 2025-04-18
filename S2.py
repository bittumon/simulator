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
def create_pdf(data, html_content, output_filename,email_date):
    try:
        data["yesterdaysDate"] =email_date
        # Replace placeholders in the HTML string with actual data
        for key, value in data.items():
            placeholder = f"{{{{ {key} }}}}"  # e.g., {{ key }}
            html_content = html_content.replace(placeholder, str(value))

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
    """Fetch the link and date from today's unread emails using IMAP based on sender and subject."""
    # Connect to Gmail IMAP server
    imap_url = 'imap.gmail.com'
    mail = imaplib.IMAP4_SSL(imap_url)

    try:
        # Log in using provided credentials
        mail.login(user, password)
        print("Logged in successfully.")

        # Select the mailbox (default is "INBOX")
        mail.select("inbox")

        # Search for today's unread emails with the specified sender and subject
        search_query = f'(UNSEEN FROM "{sender_email}" SUBJECT "{subject_keyword}")'
        status, messages = mail.search(None, search_query)

        # Get the list of email IDs
        email_ids = messages[0].split()
        if not email_ids:
            print(f"No matching unread emails found for subject: '{subject_keyword}'")
            return None, None

        # Fetch the latest email
        latest_email_id = email_ids[-1]  # Get the most recent email ID
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

                # Calculate one day before the email date
                previous_date = email_date - timedelta(days=1)
                previous_date_str = previous_date.strftime("%d-%m-%Y")

                # Check if the email has a multipart payload
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            # Decode the email body
                            body = part.get_payload(decode=True).decode()
                            # Extract the link using regex
                            link_match = re.search(r'(https://portal\.isolarcloud\.com/[^\s"]+)', body)
                            if link_match:
                                print(f"Link found for subject: '{subject_keyword}'")
                                return link_match.group(1), previous_date_str
                else:
                    # Handle non-multipart emails
                    body = msg.get_payload(decode=True).decode()
                    link_match = re.search(r'(https://portal\.isolarcloud\.com/[^\s"]+)', body)
                    if link_match:
                        print(f"Link found for subject: '{subject_keyword}'")
                        return link_match.group(1), previous_date_str

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
    service = Service(r'C:Users\lcd-user\source\repos\datalogger sunguard\chromedriver')  # Replace with your ChromeDriver path  r'C:\Users\Bittu\Projetto Python\email scrapper without assignment\Log\geckodriver.exe
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
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><img src="data:image/png;base64,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" style="width: 968px;"><br></span></p>
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
        <p style="margin-top:0pt; margin-bottom:0pt; line-height:6%; font-size:10pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
    </div>
    <p><span style='font-family: "Times New Roman", Times, serif; font-size: 18px;'><br></span></p><span style='font-family: "Times New Roman", Times, serif; font-size: 26px;'><u><strong>&nbsp;</strong></u><u><strong>Ta Cenc 4 - Daily Production Report ({{ yesterdaysDate }})</strong></u></span><span style='font-family: "Times New Roman", Times, serif; font-size: 22px;'><u><strong><br></strong></u></span><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><u><br></u></span><span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'><u><br></u></span>
    <h1 style='margin-top:0cm;margin-right:0cm;margin-bottom:0cm;margin-left:0cm;font-size:13px;font-family:"Microsoft YaHei",sans-serif;font-weight:normal;'><span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'>&nbsp;</span></h1>
    <table style="border: none; margin-left: 29.1pt; border-collapse: collapse; width: 94%; margin-right: calc(2%);">
        <tbody>
            <tr>
                <td style="width: 23.0252%; border: 1pt solid windowtext; background: rgb(240, 240, 240); padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:  13.4pt;margin-bottom:.0001pt;margin-left:0cm;'><span style='font-size: 16px; color: black; font-family: "Times New Roman", Times, serif;'>Yield Today</span></p>
                </td>
                <td style="width: 10.4551%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.1pt;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>{{ yieldToday }}</span></p>
                </td>
                <td style="width: 9.8858%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; background: rgb(240, 240, 240); padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.25pt;'><span style='font-size: 16px; color: black; font-family: "Times New Roman", Times, serif;'>Total&nbsp;Yield</span></p>
                </td>
                <td style="width: 9.345%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.3pt;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>{{ totalYield }}</span><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                </td>
                <td style="width: 13.2395%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; background: rgb(240, 240, 240); padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:8.35pt;margin-bottom:.0001pt;margin-left:5.0pt;line-height:65%;'><span style='font-size: 16px; line-height: 65%; color: black; font-family: "Times New Roman", Times, serif;'>CO</span><span style='font-size: 16px; line-height: 65%; font-family: "Times New Roman", Times, serif; color: black;'>2&nbsp;</span><span style='font-size: 16px; line-height: 65%; color: black; font-family: "Times New Roman", Times, serif;'>reduction</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:8.35pt;margin-bottom:.0001pt;margin-left:5.0pt;line-height:65%;'><span style='font-size: 16px; line-height: 65%; color: black; font-family: "Times New Roman", Times, serif;'>&nbsp;Today</span></p>
                </td>
                <td style="width: 9.8374%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.05pt;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>{{ co2ReductionToday }}</span></p>
                </td>
                <td style="width: 13.3138%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; background: rgb(240, 240, 240); padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:25.75pt;margin-bottom:.0001pt;margin-left:5.0pt;line-height:65%;'><span style='font-size: 16px; line-height: 65%; color: black; font-family: "Times New Roman", Times, serif;'>Total</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:25.75pt;margin-bottom:.0001pt;margin-left:5.0pt;line-height:65%;'><span style='font-size: 16px; line-height: 65%; color: black; font-family: "Times New Roman", Times, serif;'>&nbsp;CO</span><span style='font-size: 16px; line-height: 65%; font-family: "Times New Roman", Times, serif; color: black;'>2&nbsp;</span><span style='font-size: 16px; line-height: 65%; color: black; font-family: "Times New Roman", Times, serif;'>reduction</span></p>
                </td>
                <td style="width: 10.8449%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; padding: 0cm; height: 32.35pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:8.3pt;margin-right:0cm;margin-bottom:.0001pt;margin-left:5.05pt;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>{{ totalCO2Reduction }} &nbsp;</span></p>
                </td>
            </tr>
            <tr>
                <td style="width: 23.0252%; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-left: 1pt solid windowtext; border-image: initial; border-top: none; background: rgb(240, 240, 240); padding: 0cm; height: 31.75pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:25.75pt;margin-bottom:.0001pt;margin-left:5.1pt;line-height:65%;'><span style='font-size: 16px; line-height: 65%; color: black; font-family: "Times New Roman", Times, serif;'>Revenue Today</span></p>
                </td>
                <td colspan="7" style="width: 76.8546%; border-top: none; border-left: none; border-bottom: 1pt solid windowtext; border-right: 1pt solid windowtext; padding: 0cm; height: 31.75pt; vertical-align: top;">
                    <p style='font-size: 15px; font-family: "Microsoft YaHei", sans-serif; margin: 8.3pt 0cm 0.0001pt 5.1pt; text-align: left;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>{{ revenueToday }} &#8364;</span></p>
                </td>
            </tr>
            <tr>
                <td style="width: 23.0252%; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-left: 1pt solid windowtext; border-image: initial; border-top: none; background: rgb(240, 240, 240); padding: 0cm; height: 31.75pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-top:7.2pt;margin-right:7.95pt;margin-bottom:.0001pt;margin-left:5.1pt;line-height:65%;'><span style='font-size: 16px; line-height: 65%; color: black; font-family: "Times New Roman", Times, serif;'>Cumulative Total Revenue</span></p>
                </td>
                <td colspan="7" style="width: 76.8546%; border-top: none; border-left: none; border-bottom: 1pt solid windowtext; border-right: 1pt solid windowtext; padding: 0cm; height: 31.75pt; vertical-align: top;">
                    <p style='font-size: 15px; font-family: "Microsoft YaHei", sans-serif; margin: 8.3pt 0cm 0.0001pt 5.1pt; text-align: left;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>{{ cumulativeTotalRevenue }} &#8364;</span></p>
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
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>Plant</span></p>
                </td>
                <td style="width: 19.5864%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; background: rgb(242, 242, 242); padding: 0cm 5.4pt; height: 32.7pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>Installed&nbsp;Power&nbsp;(kWp)</span></p>
                </td>
                <td style="width: 17.0316%; border-top: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext; border-image: initial; border-left: none; background: rgb(242, 242, 242); padding: 0cm 5.4pt; height: 32.7pt; vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>Yield&nbsp;Today&nbsp;(kWh)</span></p>
                </td>
                <td style="width: 3cm;border-top: 1pt solid windowtext;border-right: 1pt solid windowtext;border-bottom: 1pt solid windowtext;border-image: initial;border-left: none;background: rgb(242, 242, 242);padding: 0cm 5.4pt;height: 32.7pt;vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.45pt;text-align:  center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.45pt;text-align:  center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>Total&nbsp;Yield&nbsp;(kWh)</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:10.65pt;text-align:  center;line-height:7.1pt;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                </td>
                <td style="width: 78pt;border-top: 1pt solid windowtext;border-right: 1pt solid windowtext;border-bottom: 1pt solid windowtext;border-image: initial;border-left: none;background: rgb(242, 242, 242);padding: 0cm 5.4pt;height: 32.7pt;vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.6pt;text-align:  center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.6pt;text-align:  center;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>Revenue&nbsp;Today</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:10.6pt;text-align:  center;line-height:7.1pt;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; font-family: "Times New Roman", Times, serif;'>&nbsp;</span></p>
                </td>
                <td style="width: 77.95pt;border-top: 1pt solid windowtext;border-right: 1pt solid windowtext;border-bottom: 1pt solid windowtext;border-image: initial;border-left: none;background: rgb(242, 242, 242);padding: 0cm 5.4pt;height: 32.7pt;vertical-align: top;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.2pt;text-align:  center;line-height:12.45pt;'><span style="font-size: 16px;"><br></span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.2pt;text-align:  center;line-height:12.45pt;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>Total CO</span><span style='font-size: 16px; font-family: "Times New Roman", Times, serif; color: rgb(51, 51, 51);'>2</span></p>
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;margin-left:6.2pt;text-align:  center;line-height:12.45pt;'><span style='font-size: 16px; color: rgb(51, 51, 51); font-family: "Times New Roman", Times, serif;'>reduction (kg)</span></p>
                </td>
            </tr>
            <tr>
                <td style="width: 70.9pt; padding: 5px; vertical-align: top; border-left: 1pt solid windowtext; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(33, 33, 33); font-family: "Times New Roman", Times, serif;'>Ta Cenc 4</span></p>
                </td>
                <td style="width: 19.5864%; padding: 10px; vertical-align: top; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(33, 33, 33); font-family: "Times New Roman", Times, serif;'>685.93</span></p>
                </td>
                <td style="width: 17.0316%; padding: 5pt; vertical-align: top; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'>{{ installedPower }}</span></p>
                </td>
                <td style="width: 3cm; padding: 5pt; vertical-align: middle; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'>{{ yieldTodayPlant }}</span></p>
                </td>
                <td style="width: 78pt; padding: 10px; vertical-align: top; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'><span style='font-size: 16px; color: rgb(33, 33, 33); font-family: "Times New Roman", Times, serif;'>{{ revenueToday }} &#8364;</span></p>
                </td>
                <td style="width: 77.95pt; padding: 5pt; vertical-align: top; border-right: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
                    <p style='margin:0cm;font-size:15px;font-family:"Microsoft YaHei",sans-serif;text-align:center;'> <span style='font-family: "Times New Roman", Times, serif; font-size: 16px;'>{{ totalCO2Reduction }}</span></p>
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
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>


    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><br></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
    <p style="margin-top:0pt; margin-bottom:0pt; font-size:8pt;"><span style='font-family: "Times New Roman", Times, serif; font-size: 14px;'><br></span></p>
    <div style="clear:both;">
        <p style="margin-top:0pt; margin-bottom:0pt; text-align:center;"><span style='font-family: "Times New Roman", Times, serif; font-size: 12px;'><strong><span style="color: rgb(192, 80, 77);">Myenergy S.p.A.</span></strong></span><span style='font-size: 12px; color: rgb(0, 112, 192); font-family: "Times New Roman", Times, serif;'>Sede legale Via Angelo Moro,109-20097 San Donato Milanese (MI)|Fax. 0251621694|Tel.0236798760&nbsp;</span><span style='font-family: "Times New Roman", Times, serif; font-size: 12px;'><a href="http://www.myenergy.it" style="text-decoration:none;"><u><span style="color: rgb(0, 112, 192);">www.myenergy.it</span></u></a></span><span style='font-size: 12px; color: rgb(0, 112, 192); font-family: "Times New Roman", Times, serif;'>&nbsp;|&nbsp;</span><span style='font-family: "Times New Roman", Times, serif; font-size: 12px;'><a href="mailto:info@myenergy.it" style="text-decoration:none;"><u><span style="color: rgb(0, 0, 255);">info@myenergy.it</span></u></a></span><span style='font-size: 12px; color: rgb(0, 112, 192); font-family: "Times New Roman", Times, serif;'>&nbsp;| Numero di REA: MI-1830429 | Partita Iva e Codice Fiscale: 05528670960</span></p>
        <p style="margin-top:0pt; margin-bottom:0pt; text-align:justify; font-size:4pt;"><span style='color: rgb(196, 188, 150); font-family: "Times New Roman", Times, serif; font-size: 9px;'>Informativa art. 13 circa il trattamento dei dati personali ai sensi del D. LGS 196/2003: Vi comunichiamo che nel nostro archivio informatico sono contenuti i Vostri dati personali e che gli stessi verranno utilizzati ed elaborati direttamente (o tramite soggetti esterni) per finalit&agrave; gestionali, commerciali e contrattuali. L&rsquo;art. 7 della legge sopra citata Vi d&agrave; diritto in qualsiasi momento di conoscere, cancellare, rettificare, aggiornare, integrare ed opporsi al trattamento dei dati personali. Il titolare del trattamento &egrave;: &nbsp;MYENERGY S.p.A. con sede in San Donato Milanese (MI) in Via Angelo Moro n&deg;109</span><span style='font-size: 9px; color: rgb(196, 188, 150); font-family: "Times New Roman", Times, serif;'>.</span></p>
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
            to_email="powerbi@wsc.com.mt",
            cc_email="manutenzione@myenergy.it",
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
