# 1. IN COMMAND PROMPT: pip3 install selenium
# 2. Download chromedriver for correct Chrome version (Help -> About Google Chrome)
#      https://sites.google.com/a/chromium.org/chromedriver/home
# 3. Add chromedriver to execution PATH (Environmental Variables on windows)

import datetime
import time
from selenium import webdriver
import tkinter as tk
from tkinter import ttk


# noinspection PyBroadException
class BigBlueButtonAutomator:

    def __init__(self, access_code, name):
        self.access_code = access_code
        self.name = name
        self.driver = None
        self.app = None

    def click_button(self, class_name):
        self.driver.find_element_by_class_name(class_name).click()

    def login_to_big_blue_button(self):
        self.setup_driver_and_open_page()
        self.enter_access_code()
        self.enter_name()

    def setup_driver_and_open_page(self):
        self.driver = webdriver.Chrome()
        url = "https://bbb2.cybbh.space/b/nic-usy-qpd"
        self.driver.get(url)

    def enter_access_code(self):
        input_field = self.driver.find_element_by_id("room_access_code")
        input_field.send_keys(self.access_code)
        enter_button = self.driver.find_element_by_name("commit")
        enter_button.click()

    def enter_name(self):
        input_field = self.driver.find_element_by_id("_b_nic-usy-qpd_join_name")
        input_field.send_keys(self.name)
        self.click_button("input-group-append")

    def launch_app(self):
        self.app = tk.Tk()

        self.app.title("Hello!")
        self.app.geometry('400x300')
        self.app.configure(bg='white')

        # Add Label
        label = ttk.Label(self.app, text="Big Blue Button Python", background='white', font=("Verdana", 14))
        label.pack(side="top", pady=50)

        # Add Buttons
        login_button = ttk.Button(self.app, text="Launch BigBlueButton", command=self.login_to_big_blue_button)
        login_button.pack(side="top", pady=30)

        break_button = ttk.Button(self.app, text="5 Minute Break", command=self.execute_happy_status)
        break_button.pack(side="top", pady=5)

        # Execute app
        self.app.mainloop()

    def execute_happy_status(self):
        time.sleep(300)

        self.click_button('userName--6aS3s')
        self.click_status_menu(1)
        self.click_happy_status()

    # Website changes html tag number based on how many times status is changed.
    # Solution was to begin incrementing from 1 and use recursion until success.
    # 250 as upper bound to prevent infinite loop
    def click_status_menu(self, input_index):
        try:
            self.driver.find_element_by_xpath(
                "//li[@aria-describedby='dropdown-item-desc-{}']".format(input_index)).click()
        except:
            if input_index < 250:
                self.clickStatusMenu(input_index + 1)

    def click_happy_status(self):
        try:
            final_xpath = "/html[@class='animationsEnabled']/body[@class='browser-chrome os-windows']/div[@id='app']/main[@class='main--Z1w6YvE']/section[@class='wrapper--Z20hQYP']/div[2]/div[@class='userList--11btR3']/div[@class='userList--Z2q1D0p']/div[@class='content--2pnTsl']/div[@class='userListColumn--6vKQL']/div[@class='scrollableList--Z2s6Her']/div[@class='list--Z2pj65C']/div/div[@class='participantsList--1MvMwF undefined'][1]/div[@class='dropdown--Z10dYoc dropdown--2fjjUn usertListItemWithMenu--Z27EKt2']/div[@class='content--ZmitSl right-top--Z1QyptE dropdownContent--ZpTliS']/div[@class='scrollable--4fyj']/ul[@class='verticalList--Ghtxj']/li[@class='item--yl1AH'][7]/span[@class='itemLabel--Z12glHA']"
            self.driver.find_element_by_xpath(final_xpath).click()
        except:
            final_xpath = "//ul[@class='verticalList--Ghtxj']/li[@class='item--yl1AH'][7]"
            self.driver.find_element_by_xpath(final_xpath).click()


# EXECUTION
bbb_obj = BigBlueButtonAutomator(230166, "Ryan Bell")
bbb_obj.launch_app()
