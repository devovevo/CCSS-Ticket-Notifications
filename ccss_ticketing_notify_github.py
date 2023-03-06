import time
import sys
import atexit
import os
import subprocess

from selenium import webdriver

from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options

from win11toast import notify

wait_time_before_ticket_check = 60
wait_time_for_button_load = 20
wait_time_for_ticket_load = 20
wait_time_for_cancel_load = 20

wait_time_for_bad_connection = 5
max_num_failed_loads = 5

current_num_failed_loads = 0

tdx_url = "https://tdx.cornell.edu/TDNext/Home/Desktop/Default.aspx"

resp_group_notify = "all"

username = ""
password = ""

ccss_icon = {
    'src': 'https://pbs.twimg.com/profile_images/1159137850388078592/Eug8aqJU_400x400.png',
    'placement': 'appLogoOverride'
}

class Ticket:
    def __init__(self, idn, title, requ, resp, date, acc, prior, link, desc):
        self.idnum = idn
        self.title = title
        self.requestor = requ
        self.respgroup = resp
        self.datecreated = date
        self.accountdep = acc
        self.priority = prior
        self.url = link
        self.description = desc

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

chrome_custom_options = Options()
chrome_custom_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_custom_options.add_argument("start-maxixmized")
chrome_custom_options.add_argument("enable-automation")
chrome_custom_options.add_argument("--headless")
chrome_custom_options.add_argument("--window-size=1280,720")
chrome_custom_options.add_argument("--disable-extensions")
chrome_custom_options.add_argument("--dns-prefetch-disable")
chrome_custom_options.add_argument("--disable-dev-shm-usage")
#chrome_custom_options.add_argument("--disable-gpu")
chrome_custom_options.add_argument("--disable-browser-side-navigation")
chrome_custom_options.page_load_strategy = 'eager'
chrome_custom_options.add_argument("enable-features=NetworkServiceInProcess")

driver = webdriver.Chrome(options=chrome_custom_options)

def exit_handler():
    driver.quit()

atexit.register(exit_handler)

def loginCornellSSO():
    global current_num_failed_loads

    username_element = None
    password_element = None
    submit_button_element = None

    while (username_element == None or password_element == None or submit_button_element == None):
        try:
            username_element = WebDriverWait(driver, wait_time_for_button_load).until(
                EC.visibility_of_element_located((By.NAME, "j_username"))
            )

            password_element = WebDriverWait(driver, wait_time_for_button_load).until(
                EC.visibility_of_element_located((By.NAME, "j_password"))
            )

            submit_button_element = WebDriverWait(driver, wait_time_for_button_load).until(
                EC.visibility_of_element_located((By.NAME, "_eventId_proceed"))
            )

            current_num_failed_loads = 0
        except TimeoutException:
            print("Couldn't find login elements, and as such can't move on. Retrying...")
            current_num_failed_loads += 1

            if (current_num_failed_loads > max_num_failed_loads):
                print("Max number of failed loads reached. Qutting...")
                logfile = open("logfile.txt", "a")
                logfile.write("Current number of failed loads: " + current_num_failed_loads)

                driver.quit()
                sys.exit()

            time.sleep(wait_time_for_bad_connection)

    username_element.click()
    username_element.send_keys(username)

    password_element.click()
    password_element.send_keys(password)

    submit_button_element.click()

def closePopup():
    try:
        close_button_element = WebDriverWait(driver, wait_time_for_cancel_load).until(
            EC.visibility_of_element_located((By.XPATH, "//button[not(contains(@id, 'notificationCloseX')) and @class='close']"))
        )

        close_button_element.click()
    except TimeoutException:
        print("No close button found, not a serious error.")

def duoLogin():
    global current_num_failed_loads
    duoPushButton = None

    while(duoPushButton == None and driver.current_url != tdx_url):
        try:
            duoIframe = WebDriverWait(driver, wait_time_for_button_load).until(
                EC.visibility_of_element_located((By.ID, "duo_iframe"))
            )

            driver.switch_to.frame(duoIframe)

            duoPushButton = WebDriverWait(driver, wait_time_for_button_load).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "auth-button positive"))
            )
            
            duoPushButton.click()
            current_num_failed_loads = 0
        except TimeoutException:
            print("Could not find duo login button, so can't login to system. Retrying...")
            current_num_failed_loads += 1

            if(current_num_failed_loads > max_num_failed_loads):
                print("Max number of failed loads reached. Quitting...")
                logfile = open("logfile.txt", "a")
                logfile.write("Current number of failed loads: " + current_num_failed_loads)
                
                driver.quit()
                sys.exit()
        
            time.sleep(wait_time_for_bad_connection)

CMD = '''
on run argv
    display notification (item 1 of argv) with title (item 2 of argv) sound name (item 3 of argv)
end run
'''

def appleNotify(title, text):
  subprocess.call(['osascript', '-e', CMD, text, title, "Glass"])

def notifyPlatformDependent(newTicket):
    oper_system = os.name()

    if (oper_system == "nt"):
        notify(newTicket.title + " from " + newTicket.requestor, newTicket.description or "No description given", icon=ccss_icon, on_click=newTicket.url, button={'activationType': 'protocol', 'arguments': newTicket.url, 'content': 'Open Ticket'})
    elif (oper_system == "unix"):
        appleNotify(newTicket.title + " from " + newTicket.requestor, newTicket.description or "No description given")

def checkTickets():
    global current_num_failed_loads

    ticketElements = []
    currentTicketIDs = []

    tickets = []
    newTickets = []

    while True:
        if (driver.current_url.startswith("https://shibidp.cit.cornell.edu/")):
            loginCornellSSO()

            if(driver.current_url != tdx_url):
                duoLogin()

        closePopup()
 
        driver.switch_to.frame("appDesktop")

        try:
            ticketElements = WebDriverWait(driver, wait_time_for_ticket_load).until(
                EC.visibility_of_any_elements_located((By.XPATH, "//div[contains(@id, '102547')]//tr[not(contains(@class, 'TDGridHeader'))]"))
            )

            print(ticketElements);
        except TimeoutException:
            print("No tickets found")

        for ticketElement in ticketElements:
            ticketInfo = ticketElement.find_elements(By.TAG_NAME, "td")

            ticketID = ticketInfo[0].text

            if (currentTicketIDs.count(ticketID) == 0):
                currentTicketIDs.append(ticketID)

                ticketTitle = ticketInfo[1].text
                ticketRequestor = ticketInfo[2].text
                ticketResponseGroup = ticketInfo[3].text
                ticketDateCreated = ticketInfo[4].text
                ticketAccountDepartment = ticketInfo[5].text
                ticketPriority = ticketInfo[6].text
                url = ticketInfo[0].find_element(By.TAG_NAME, "a").get_attribute("href")

                currentTicket = Ticket(ticketID, ticketTitle, ticketRequestor, ticketResponseGroup, ticketDateCreated, ticketAccountDepartment, ticketPriority, url, "")
                tickets.append(currentTicket)
                newTickets.append(currentTicket)
            
        for newTicket in newTickets:
            driver.get(newTicket.url)

            ticketDescription = ""

            try:
                descriptionElement = WebDriverWait(driver, wait_time_for_button_load).until(
                    EC.visibility_of_element_located((By.ID, "ttDescription"))
                )

                ticketDescription = descriptionElement.text
            except TimeoutException:
                print("No ticket description found.")

                time.sleep(wait_time_for_bad_connection)

            newTicket.description = ticketDescription

            if (newTicket.respgroup == resp_group_notify or newTicket.respgroup == "all"):
                notifyPlatformDependent()

        ticketElements.clear()
        newTickets.clear()
        
        time.sleep(wait_time_before_ticket_check)
        driver.get(tdx_url)

driver.get(tdx_url)

checkTickets()