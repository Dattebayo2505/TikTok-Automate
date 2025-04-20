from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from colorama import Fore # For colored text

from selenium_driverless import webdriver
from selenium_driverless.types.by import By

import asyncio
import os
import sys
import requests

import time
import warnings
warnings.filterwarnings('ignore', message='got execution_context_id and unique_context=True.*')


###########################################     
DEBUGGING = True

WAIT_TIME = 3 # element wait timeout
live_mode_active = True # Set to False for production

email = "seankyled1st@gmail.com"
password = ""
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
    if DEBUGGING:
        print(Fore.YELLOW + text)
        reset_color()

def print_intro(title):
    print_color(f'[{title}]', 'GREEN')

def live_mode():
    global live_mode_active
    choice = input('Y - See automation live\nN - Put automation in background: ')
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

def blob_url_to_base64(driver, blob_url):
    # Use JavaScript to fetch the blob data and convert it to Base64
    script = """
    return new Promise((resolve) => {
        fetch(arguments[0])
            .then(response => response.blob())
            .then(blob => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                reader.readAsDataURL(blob);
            });
    });
    """
    base64_string = driver.execute_script(script, blob_url)

    return base64_string

async def login(driver):
    global email, password

    log_in = await wait_for_element(driver, "//button[@class='TUXButton TUXButton--default TUXButton--medium TUXButton--primary css-18fmjv5-StyledLeftSidePrimaryButtonRedesign enq7hkb0']", 15)
    await log_in.click()

    try:
        other_text = await wait_for_element(driver, "//div[@class='TUXSegmentedControl-itemTitle' and text()='Other']", 5)
        await other_text.click()

        other_login_method = await wait_for_element(driver, "//div[text()='Other login options']", 5)
        await other_login_method.click()

        log_in_mode = await wait_for_element(driver, "//div[text()='Use phone / email / username']", 5)
        await log_in_mode.click()
    except Exception as e:
        try:
            print_color("Other login options not found, proceeding...", "BLUE")
            other_login_method = await wait_for_element(driver, "//div[text()='Other login options']", 5)
            await other_login_method.click()
            
            log_in_mode = await wait_for_element(driver, "//div[text()='Use phone / email / username']", 5)
            await log_in_mode.click()
        except Exception as e:
            print_color("Other login options not found, proceeding...", "BLUE")
            log_in_mode = await wait_for_element(driver, "//div[text()='Use phone / email / username']", 5)
            await log_in_mode.click()

    log_in_mode_2 = await wait_for_element(driver, "//a[text()='Log in with email or username']")
    await log_in_mode_2.click()

    # email = await input('Enter your email: ')
    email_input = await wait_for_element(driver, "//input[@placeholder='Email or username']")
    await driver.execute_script("arguments[0].value = arguments[1];", email_input, email)

    password = input('Enter your password: ')
    password_input = await wait_for_element(driver, "//input[@placeholder='Password']")
    await driver.execute_script("arguments[0].value = arguments[1];", password_input, password)  
    # await password_input.send_keys(password)

    # await email_input.send_keys(Keys.END)
    await driver.execute_script("arguments[0].focus(); arguments[0].setSelectionRange(arguments[0].value.length, arguments[0].value.length);", email_input)
    await driver.execute_script("arguments[0].value = arguments[0].value.slice(0, -1);", email_input)
    await email_input.send_keys(email[-1])

    await driver.execute_script("arguments[0].focus(); arguments[0].setSelectionRange(arguments[0].value.length, arguments[0].value.length);", password_input)
    await driver.execute_script("arguments[0].value = arguments[0].value.slice(0, -1);", password_input)
    await password_input.send_keys(password[-1])

    log_in_2 = await wait_for_element(driver, "//button[@type='submit' and @data-e2e='login-button']")
    await log_in_2.click()

async def handle_3d_captcha(driver, captcha_element):
    """Handle 3D CAPTCHA."""
    blob_url = await driver.execute_script("return arguments[0].src;", captcha_element)
    debug_print(f"3D CAPTCHA Blob URL: {blob_url}")

    # Convert blob URL to Base64
    base64_string = await blob_url_to_base64(driver, blob_url)
    debug_print(f"3D CAPTCHA Base64: {base64_string}")

    # Send Base64 string to the API
    url = "https://tiktok-captcha-solver2.p.rapidapi.com/tiktok/captcha"
    payload = {
        "cap_type": "3d",
        "image_base64": base64_string
    }
    headers = {
        "x-rapidapi-key": "a5b34a0923msh74303821e5dac68p1f0367jsnd801f84bc0ed",
        "x-rapidapi-host": "tiktok-captcha-solver2.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    debug_print(f"3D CAPTCHA API Response: {result}")

    # Handle the API response (e.g., simulate solving the CAPTCHA)
    if "solution" in result:
        debug_print(f"3D CAPTCHA Solved: {result['solution']}")
    else:
        print_color("Failed to solve 3D CAPTCHA.", "RED")

async def handle_puzzle_captcha(driver, captcha_element):
    """Handle Puzzle CAPTCHA."""
    # Locate the puzzle and piece images
    puzzle_image = await wait_for_element(driver, "//img[contains(@src, 'blob:') and contains(@alt, 'Captcha')]", setwaittime=5)
    piece_image = await wait_for_element(driver, "//img[contains(@src, 'blob:') and contains(@alt, 'Captcha') and contains(@class, 'cap-absolute')]", setwaittime=5)

    # Extract blob URLs
    puzzle_blob_url = await driver.execute_script("return arguments[0].src;", puzzle_image)
    piece_blob_url = await driver.execute_script("return arguments[0].src;", piece_image)

    debug_print(f"Puzzle Blob URL: {puzzle_blob_url}")
    debug_print(f"Piece Blob URL: {piece_blob_url}")

    # Send blob URLs to the API
    url = "https://tiktok-captcha-solver2.p.rapidapi.com/tiktok/captcha"
    payload = {
        "cap_type": "puzzle",
        "puzzle_url": puzzle_blob_url,
        "piece_url": piece_blob_url
    }
    headers = {
        "x-rapidapi-key": "a5b34a0923msh74303821e5dac68p1f0367jsnd801f84bc0ed",
        "x-rapidapi-host": "tiktok-captcha-solver2.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    debug_print(f"Puzzle CAPTCHA API Response: {result}")

    # Handle the API response (e.g., simulate solving the CAPTCHA)
    if "solution" in result:
        debug_print(f"Puzzle CAPTCHA Solved: {result['solution']}")
    else:
        print_color("Failed to solve Puzzle CAPTCHA.", "RED")

async def handle_whirl_captcha(driver, captcha_element):
    """Handle Whirl CAPTCHA."""
    # Locate the two images for the Whirl CAPTCHA
    image1 = await wait_for_element(driver, "//img[contains(@src, 'blob:') and contains(@alt, 'captcha_whirl_title')]", setwaittime=5)
    image2 = await wait_for_element(driver, "//div[contains(@class, 'cap-flex')]/img[contains(@src, 'blob:')]", setwaittime=5)

    # Extract blob URLs
    url1 = await driver.execute_script("return arguments[0].src;", image1)
    url2 = await driver.execute_script("return arguments[0].src;", image2)

    debug_print(f"Whirl CAPTCHA URL1: {url1}")
    debug_print(f"Whirl CAPTCHA URL2: {url2}")

    # Send blob URLs to the API
    url = "https://tiktok-captcha-solver2.p.rapidapi.com/tiktok/captcha"
    payload = {
        "cap_type": "whirl",
        "url1": url1,
        "url2": url2
    }
    headers = {
        "x-rapidapi-key": "a5b34a0923msh74303821e5dac68p1f0367jsnd801f84bc0ed",
        "x-rapidapi-host": "tiktok-captcha-solver2.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    debug_print(f"Whirl CAPTCHA API Response: {result}")

    # Handle the API response (e.g., simulate solving the CAPTCHA)
    if "solution" in result:
        debug_print(f"Whirl CAPTCHA Solved: {result['solution']}")
    else:
        print_color("Failed to solve Whirl CAPTCHA.", "RED")

async def solve_captcha(driver):
    # Three captcha exist (By chance):
    # Links below are ONLY examples, but actual links follow the same format.

    # For 3D Captcha
    # <img src="blob:https://www.tiktok.com/c54d4e07-7a14-47f7-845f-b2c1536d8989" alt="Verify that you’re not a robot" class="cap-rounded-lg cap-cursor-pointer cap-w-full cap-h-auto" draggable="false" style="display: flex;">

    # Puzzle Captcha
    # <div class="cap-flex cap-flex-col cap-justify-center cap-items-center "><img src="blob:https://www.tiktok.com/43435b8c-a066-4f9f-8a53-d273b304fca8" alt="Captcha" class="cap-h-[170px] sm:cap-h-[210px]" draggable="false" style="clip-path: circle(50%); display: flex; transform: rotate(0deg);"><img src="blob:https://www.tiktok.com/a75b5b73-4dfa-44f2-b16a-eed0193f4a88" alt="Captcha" class="cap-absolute cap-h-[105px] sm:cap-h-[128px]" draggable="false" style="clip-path: circle(50%); transform: rotate(0deg); display: flex;"></div>

    # Whirl Captcha
    # <div class="cap-flex cap-flex-col cap-relative"><img id="captcha-verify-image" src="blob:https://www.tiktok.com/35436773-f55c-41d5-846a-f511a59d82a4" alt="captcha_whirl_title" class="cap-rounded-lg cap-w-full cap-h-auto" draggable="false" style="display: block;"><div draggable="true" class="cap-flex cap-absolute " style="cursor: grab; transform: translateX(0px); top: 41px; left: 0px;"><img src="blob:https://www.tiktok.com/669d547a-2b65-42bc-b186-a070c0338194" alt="Captcha" draggable="false" style="width: 57.5581px; height: 57.5581px; display: block;"></div></div>

    """Solve CAPTCHA by trying all possible types."""
    try:
        # Define possible CAPTCHA types and their corresponding handling logic
        captcha_types = [
            {
                "name": "3D Captcha",
                "xpath": "//img[contains(@src, 'blob:') and contains(@alt, 'Verify that you’re not a robot')]",
                "handler": handle_3d_captcha
            },
            {
                "name": "Puzzle Captcha",
                "xpath": "//div[contains(@class, 'cap-flex') and contains(@class, 'cap-justify-center')]",
                "handler": handle_puzzle_captcha
            },
            {
                "name": "Whirl Captcha",
                "xpath": "//img[@id='captcha-verify-image']",
                "handler": handle_whirl_captcha
            }
        ]

        # Iterate through each CAPTCHA type
        for captcha_type in captcha_types:
            try:
                debug_print(f"Trying {captcha_type['name']}...")
                captcha_element = await wait_for_element(driver, captcha_type["xpath"], setwaittime=5)
                if captcha_element:
                    debug_print(f"{captcha_type['name']} detected!")
                    await captcha_type["handler"](driver, captcha_element)
                    return  # Exit the function once a CAPTCHA is successfully solved
            except TimeoutException:
                debug_print(f"{captcha_type['name']} not found. Trying the next one...")

        # If no CAPTCHA is solved
        print_color("No valid CAPTCHA found or solved.", "RED")

    except Exception as e:
        print_color(f"Error solving CAPTCHA: {e}", "RED")

async def func2(driver):
    pass

async def main2():
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--detach")
    # options.use_extension = False

    # Need to pay for this lol DON'T USE FOR NOW
    # options.add_extension(resource_path("TikTok-Captcha-Solver-Chrome-Web-Store.zip"))

    if not live_mode_active:
        options.add_argument("--headless")

    async with webdriver.Chrome(options=options) as driver:
        await asyncio.gather(
            driver.get("https://tiktok.com"),
            asyncio.sleep(0.5),
            driver.wait_for_cdp("Page.domContentEventFired", timeout=15)
        )

        await login(driver)
        # await func2(driver)
        await asyncio.sleep(999)
            

def main():
    print_intro("TikTok Automate")
    # live_mode() # SHOULD BE COMMENTED DURING PROD
    asyncio.run(main2())

if __name__ == "__main__":
    main()