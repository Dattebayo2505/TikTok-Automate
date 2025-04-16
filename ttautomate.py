from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from colorama import Fore # For colored text

from selenium_driverless import webdriver
from selenium_driverless.types.by import By

import asyncio
import os
import sys

import time
import warnings
# warnings.filterwarnings('ignore', message='got execution_context_id and unique_context=True.*')


###########################################     
WAIT_TIME = 1 # element wait timeout
live_mode_active = False            
###########################################

## General Use Functions
def reset_color():
    print(Fore.RESET, end='')

# Sample - print_color('Hello, World!', 'RED')
def print_color(text, color):
    colors = {
        'WHITE': Fore.WHITE,
        'RED': Fore.RED,
        'GREEN': Fore.GREEN,
        'BLUE': Fore.BLUE,
        'YELLOW': Fore.YELLOW }
        # Add more colors if needed
    print(colors[color] + text)
    reset_color()

def debug_print(text):
    print(Fore.YELLOW + text)
    reset_color()

def print_intro():
    print_color('[APP TITLE]', 'GREEN')

def live_mode():
    global live_mode_active
    choice = input('Y - See automation (MLS) live\nN - Put automation in background: ')
    if choice.lower() == 'y':
        live_mode_active = True
        return live_mode_active
    elif choice.lower() == 'n':
        live_mode_active = False
        return live_mode_active
    else:
        print('Invalid choice. Please try again.')
        return live_mode()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

async def wait_for_element(driver, xpath, setwaittime=None):
    # Set the wait time
    wait_time = setwaittime if setwaittime else WAIT_TIME

    # Wait for the element to exist
    elem = await driver.find_element(By.XPATH, xpath, timeout=wait_time)
    
    # Optionally, click the element (if needed)
    # await elem.click(move_to=True)
    
    return elem

async def wait_for_elements(driver, xpath, setwaittime=None):
    wait_time = setwaittime if setwaittime else WAIT_TIME
    start_time = asyncio.get_event_loop().time()

    while True:
        try:
            elems = await driver.find_elements(By.XPATH, xpath)
            if elems:
                return elems
        except Exception as e:
            # Instead of printing, you could log this message if you want to keep track of it
            # import logging
            # logging.debug(f"Error while finding elements: {e}")
            pass
        
        if asyncio.get_event_loop().time() - start_time > wait_time:
            raise TimeoutError(f"Couldn't find elements with xpath '{xpath}' within {wait_time} seconds")
        
        await asyncio.sleep(1)

async def func1(driver):
    pass

async def func2(driver):
    pass

async def main2():
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--detach")
    options.use_extension = False

    if not live_mode_active:
        options.add_argument("--headless")

    async with webdriver.Chrome(options=options) as driver:
        await asyncio.gather(
            driver.get("https://example.com"),
            asyncio.sleep(0.5),
            driver.wait_for_cdp("Page.domContentEventFired", timeout=15)
        )

        await func1(driver)
        await func2(driver)
            

def main():
    print_intro()
    live_mode() # SHOULD BE COMMENTED DURING PROD
    asyncio.run(main2())

if __name__ == "__main__":
    main()