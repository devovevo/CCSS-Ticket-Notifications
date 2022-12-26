import time
import sys
import atexit

from selenium import webdriver

from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options

from win11toast import notify

wait_time_before_ticket_check = 120
wait_time_for_button_load = 90
wait_time_for_cancel_load = 20

wait_time_for_bad_connection = 5
max_num_failed_loads = 5

current_num_failed_loads = 0

tdx_url = "https://tdx.cornell.edu/TDNext/Home/Desktop/Default.aspx"

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
chrome_custom_options.add_argument("--headless")

driver = webdriver.Chrome(options=chrome_custom_options)

def exit_handler():
    driver.quit()

atexit.register(exit_handler)

def loginCornellSSO():
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
            print("Couldn't find login elements, and as such can't move on")
            current_num_failed_loads += 1

            if (current_num_failed_loads > max_num_failed_loads):
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
    duoPushButton = None
    driver.switch_to.frame("prompt")

    while(duoPushButton == None and driver.current_url != tdx_url):
        try:
            duoPushButton = WebDriverWait(driver, wait_time_for_button_load).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "auth-button positive"))
            )
            
            duoPushButton.click()
            current_num_failed_loads = 0
        except TimeoutException:
            print("Could not find duo login button, so can't login to system")
            current_num_failed_loads += 1

            if(current_num_failed_loads > max_num_failed_loads):
                logfile = open("logfile.txt", "a")
                logfile.write("Current number of failed loads: " + current_num_failed_loads)
                
                driver.quit()
                sys.exit()
        
            time.sleep(wait_time_for_bad_connection)

def checkTickets():
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
            ticketElements = WebDriverWait(driver, wait_time_for_button_load).until(
                EC.visibility_of_any_elements_located((By.XPATH, "//tr[not(contains(@class, 'TDGridHeader'))]"))
            )
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

            ticketDescription = None

            while(ticketDescription == None):
                try:
                    descriptionElement = WebDriverWait(driver, wait_time_for_button_load).until(
                        EC.visibility_of_element_located((By.ID, "ttDescription"))
                    )

                    ticketDescription = descriptionElement.text
                except TimeoutException:
                    print("No description found")

                    time.sleep(wait_time_for_bad_connection)

            newTicket.description = ticketDescription

            notify(newTicket.title + " from " + newTicket.requestor, newTicket.description, icon=ccss_icon, button={'activationType': 'protocol', 'arguments': newTicket.url, 'content': 'Open Ticket'})

        ticketElements.clear()
        newTickets.clear()
        
        time.sleep(wait_time_before_ticket_check)
        driver.get(tdx_url)

driver.get(tdx_url)

checkTickets()