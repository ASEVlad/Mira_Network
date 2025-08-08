import random
import time
from loguru import logger

from src.llm_helper import generate_test_prompt
from src.profile_manager import ProfileManager
from src.utils import wait_until_element_is_visible, trim_stacktrace_error, send_keys, get_full_xpath_element


class Profile(ProfileManager):
    def __init__(self, profile_id: str, anty_type: str, prompts_limit: int):
        super().__init__(profile_id, anty_type)
        self.prompts_limit = prompts_limit


def run_profile_farm(web_profile: Profile, profile_num: int):
    try:
        time.sleep(profile_num)
        start_profile(web_profile)

        start_points = get_earned_points(web_profile)
        prompts_to_farm = random.randint(int(web_profile.prompts_limit * 0.8), web_profile.prompts_limit)

        for i in range(prompts_to_farm):
            farm_prompt_point(web_profile)

        end_points = get_earned_points(web_profile)

        logger.info(f"Profile_id: {web_profile.profile_id}. SUCCESSFULLY FARMED. Earned {end_points - start_points}. Total points: {end_points}")
        finalize_profile(web_profile)

    except Exception as e:
        handle_error(web_profile, e)

def start_profile(web_profile):
    # open profile
    web_profile.open_profile()
    time.sleep(1)
    web_profile.driver.switch_to.new_window('tab')
    time.sleep(1)
    sign_in(web_profile)

def finalize_profile(web_profile):
    web_profile.close_profile()

def handle_error(web_profile, error):
    trimmed_error_log = trim_stacktrace_error(str(error))
    logger.error(f"Profile_id: {web_profile.profile_id}. {trimmed_error_log}")

    try:
        finalize_profile(web_profile)
    except Exception as e:
        trimmed_error_log = trim_stacktrace_error(str(e))
        logger.error(f"Profile_id: {web_profile.profile_id}. {trimmed_error_log}")

def sign_in(web_profile):
    try:
        web_profile.driver.get("https://klokapp.ai?referral_code=LL7CBV44")
        wait_until_element_is_visible(web_profile, "xpath", "//body")
        mira_handle = web_profile.driver.current_window_handle
        window_handles = web_profile.driver.window_handles
        time.sleep(10)

        sign_in_elements = web_profile.driver.find_elements("xpath", "//button[text()='Continue with Google']")
        if sign_in_elements:
            sign_in_elements[0].click()

            # wait till the window for sign in is open
            while True:
                if len(window_handles) == len(web_profile.driver.window_handles):
                    time.sleep(2)
                else:
                    break

            try:
                web_profile.driver.switch_to.window(web_profile.driver.window_handles[-1])
                account_element = wait_until_element_is_visible(web_profile, "xpath", "//li", 60)
            except Exception as e:
                if str(e).split("\n")[0] != "target window already closed from unknown error: web view not found":
                    raise e

            if len(window_handles) != len(web_profile.driver.window_handles):
                account_element = wait_until_element_is_visible(web_profile, "xpath", "//li")
                account_element.click()

                # click on NEXT button on different languages
                time.sleep(20)
                next_german_elements = web_profile.driver.find_elements("xpath", "//span[text()='Weiter']")
                next_ukrainian_elements = web_profile.driver.find_elements("xpath", "//span[text()='Продовжити']")
                next_english_elements = web_profile.driver.find_elements("xpath", "//span[text()='Continue']")

                if len(next_german_elements) != 0:
                    next_german_elements[0].click()
                elif len(next_ukrainian_elements) != 0:
                    next_ukrainian_elements[0].click()
                elif len(next_english_elements) != 0:
                    next_english_elements[0].click()

                # wait till the window for sign in is closed
                while True:
                    if len(window_handles) != len(web_profile.driver.window_handles):
                        time.sleep(2)
                    else:
                        break

                web_profile.driver.switch_to.window(mira_handle)
                time.sleep(20)

                next_elements = web_profile.driver.find_elements("xpath", "//button[text()=\"Let's go!\"]")
                if len(next_elements) != 0:
                    next_elements[0].click()
                    wait_until_element_is_visible(web_profile, "xpath", "//button[text()='Close']").click()

            # check if signed in
            web_profile.driver.find_element("xpath", "//textarea[@placeholder='Ask me anything ']")
            logger.info(f"Profile_id: {web_profile.profile_id}. Successfully logged in")

        else:
            logger.info(f"Profile_id: {web_profile.profile_id}. No need in sign in")

    except Exception as e:
        trimmed_error_log = trim_stacktrace_error(str(e))
        logger.error(f"Profile_id: {web_profile.profile_id}. {trimmed_error_log}")
        raise

def farm_prompt_point(web_profile):
    # open main page
    web_profile.driver.get("https://klokapp.ai")
    time.sleep(15)

    try:
        # generate and write a prompt
        prompt_area = wait_until_element_is_visible(web_profile, "xpath", "//textarea[@placeholder='Ask me anything ']")
        prompt_to_test = generate_test_prompt()
        send_keys(prompt_area, prompt_to_test)

        # cloudflare test
        cloudflare_element = wait_until_element_is_visible(web_profile, "xpath", "//div[@id='cf-turnstile']")
        cloudflare_element.click()
        time.sleep(10)
        cloudflare_elements = web_profile.driver.find_elements("xpath", "//div[@id='cf-turnstile']")
        if len(cloudflare_elements) != 0:
            logger.error(f"Profile_id: {web_profile.profile_id}. Could not pass the CLOUDFLARE check.")
            return False

        # send prompt to get responses
        submit_button = wait_until_element_is_visible(web_profile, "xpath", "//button[@type='submit']")
        submit_button.click()

        # wait a bit
        time_to_sleep = 50 + random.randint(1, 20)
        time.sleep(time_to_sleep)

        return True

        logger.info(f"Profile_id: {web_profile.profile_id}. Prompt is sent.")



    except Exception as e:
        trimmed_error_log = trim_stacktrace_error(str(e))
        logger.error(f"Profile_id: {web_profile.profile_id}. {trimmed_error_log}")
        return False

def get_earned_points(web_profile: Profile):
    try:
        web_profile.driver.get("https://klokapp.ai?referral_code=LL7CBV44")

        points_presenting_element = wait_until_element_is_visible(web_profile, "xpath", "//div[text()='Total Mira Points']")
        points_presenting_xpath = get_full_xpath_element(web_profile.driver, points_presenting_element)
        time.sleep(10)

        points_element = wait_until_element_is_visible(web_profile, "xpath", points_presenting_xpath + "[2]")
        points = int(points_element.text)
        return points

    except Exception as e:
        trimmed_error_log = trim_stacktrace_error(str(e))
        logger.error(f"Profile_id: {web_profile.profile_id}. {trimmed_error_log}")
        return 0
