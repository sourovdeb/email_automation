from playwright.sync_api import sync_playwright
import time
import os

def send_email_with_protonmail(username, password, recipient_email, subject, body, attachment_path, browser_name="chromium", headless=False):
    """
    Logs into ProtonMail and sends an email with an attachment.

    Args:
        username (str): Your ProtonMail username.
        password (str): Your ProtonMail password.
        recipient_email (str): The email address of the recipient.
        subject (str): The subject of the email.
        body (str): The body of the email.
        attachment_path (str): The absolute path to the file to be attached.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    with sync_playwright() as p:
        try:
            if browser_name == "firefox":
                browser = p.firefox.launch(headless=headless)
            else:
                browser = p.chromium.launch(headless=headless)
            page = browser.new_page()

            print("Navigating to ProtonMail login page...")
            page.goto("https://mail.proton.me/login", timeout=60000)

            # Wait for the page to load and fill in credentials
            print("Entering credentials...")
            page.fill("#username", username)
            page.fill("#password", password)
            page.click("button[type='submit']")

            # Wait for the login to complete and the main mailbox to be visible
            page.wait_for_selector(".sidebar", timeout=60000)
            print("Login successful.")

            # Click the "New message" button
            page.click("button[data-testid='sidebar:compose']")
            print("Composing new email...")

            # Fill in the recipient, subject, and body
            page.fill("input[data-testid='composer:to']", recipient_email)
            page.fill("input[data-testid='composer:subject']", subject)
            
            # The body is inside an iframe, so we need to handle that
            iframe = page.frame_locator("iframe[data-testid='rooster-iframe']")
            iframe.locator("div[aria-label='Email body']").fill(body)

            # Attach the file
            if attachment_path and os.path.exists(attachment_path):
                print(f"Attaching file: {attachment_path}")
                page.set_input_files("input[type='file']", attachment_path)
                # Wait for the attachment to upload
                page.wait_for_selector(".attachment-card", timeout=60000)
                print("Attachment uploaded.")

            # Click the send button
            page.click("button[data-testid='composer:send-button']")
            print("Sending email...")

            # Wait for a confirmation or for the composer to close
            page.wait_for_selector("div[data-testid='composer']", state='hidden', timeout=60000)
            print("Email sent successfully!")
            
            # Give it a moment before closing
            time.sleep(5)
            browser.close()
            return True

        except Exception as e:
            print(f"An error occurred while sending the email: {e}")
            if 'browser' in locals() and browser.is_connected():
                browser.close()
            return False

if __name__ == '__main__':
    # This is for testing purposes.
    # IMPORTANT: Replace with your actual credentials and file paths.
    # It's recommended to use environment variables for credentials in a real application.
    
    proton_user = os.environ.get("PROTON_USER", "your_protonmail_username")
    proton_pass = os.environ.get("PROTON_PASS", "your_protonmail_password")
    
    # The test email address provided in the prompt
    test_recipient = "sourovdeb.is@gmail.com"
    
    # Example CV path
    # cv_file_path = "/home/sourov/Documents/employment/rerappelrdvfrancetravailuesaaxeressourceconseilst/Formateurd_Anglais_Certifié_CELTA_Cambridge_Spécialiste_IELTS_TOEIC_Business_English.pdf"
    cv_file_path = "path/to/your/cv.pdf" # Make sure this path is correct

    if proton_user == "your_protonmail_username" or proton_pass == "your_protonmail_password":
        print("Please set your ProtonMail credentials as environment variables (PROTON_USER, PROTON_PASS) or directly in the script for testing.")
    elif not os.path.exists(cv_file_path):
        print(f"CV file not found at: {cv_file_path}. Please update the path for testing.")
    else:
        test_subject = "Test Email from Job Automator"
        test_body = "This is a test email sent automatically using Playwright. If you received this, the automation is working correctly."
        
        send_email_with_protonmail(
            username=proton_user,
            password=proton_pass,
            recipient_email=test_recipient,
            subject=test_subject,
            body=test_body,
            attachment_path=cv_file_path
        )
