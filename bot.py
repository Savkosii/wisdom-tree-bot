import os
import sys
import pickle
from time import sleep, localtime, strftime
from threading import Thread
from random import choice, randrange, uniform
from os.path import dirname, basename 
from undetected_chromedriver import Chrome as _Chrome
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from timer import Timer
from utilities import override
from utilities import as_seconds, random_string
from utilities import search_file_recursively, file_exists


class Chrome(_Chrome):
    # The following method is used to remove some flags and avoid detection in 
    # `undetected_chromedriver.Chrome.get(self, url)` originally,
    # but it will cause the blockage of the video player.
    @override
    def _hook_remove_cdc_props(self):
        pass


class Bot:
    def __init__(self, lifetime_timer: Timer=None):
        ChromeDriverManager(version="latest", path=".").install()

        self.driver_path = self.locate_latest_driver_path()

        if self.driver_path is None:
            print("Error: cannot locate driver executable path")
            exit(1)

        options = Options()
        options.add_argument("--start-maximized")

        self.browser = Chrome(driver_executable_path=
                            self.driver_path, options=options)

        if self.user_info_exists(): 
            url = self.load_user_info()
            prev_url = self.browser.current_url
            print("Notice: Prepared to go to url {}".format(url))
            print("Notice: If you want to change the url, "
                    "please do it in browser in 5 seconds".format(url))
            sleep(5)
            if self.browser.current_url == prev_url:
                self.browser.get(url)
        else:
            self.browser.get("https://passport.zhihuishu.com/login")

        while not self.site_supported():
            print("Error: unsupported site {}".format(self.browser.current_url))
            print("Please change the url to a valid one")
            sleep(2)
            if self.site_supported():
                print("Notice: Successfully jump to {}"\
                                .format(self.browser.current_url))

        if self.course_url_invalid():
            if self.login_requested():
                print("Notice: Please login first")
                print("Notice: If you have logined previously, "
                        "this may be due to the cookies are no longer valid")
                print("All you need to do is to login again")
                while self.course_url_invalid():
                    sleep(1)
            else:
                print("Error: cannot locate video player from {}" \
                    .format(self.browser.current_url))
                print("Please go to the video page manually")
                while self.course_url_invalid():
                    sleep(1)

            print("Notice: locate video player successfully in {}"\
                    .format(self.browser.current_url))

        self.save_user_info()

        self.video_timer = None
        self.lifetime_timer = lifetime_timer

        self.speed = 1.0

    def locate_latest_driver_path(self):
        drive_name = "chromedriver"
        if sys.platform.startswith('win'):
            drive_name += '.exe'
        driver_paths = search_file_recursively(drive_name)
        if not driver_paths:
            return None
        else:
            driver_paths.sort(key=lambda path: 
                              tuple(basename(dirname(path)).split('.')))
            return driver_paths[-1]

    def user_info_path(self):
        return "user.pickle"

    def user_info_exists(self):
        return file_exists(self.user_info_path()) 

    def save_user_info(self):
        cookies = self.browser.get_cookies()
        url = self.browser.current_url
        info = [cookies, url]
        if self.user_info_exists():
            self.remove_user_info()
        with open(self.user_info_path(), "wb") as stream:
            pickle.dump(info, stream)
    
    # load the cookies of user and return the url
    def load_user_info(self):
        with open(self.user_info_path(), "rb") as stream:
            # The site will redirect the user with invalid cookies to login page,
            # which has a different domain.
            # Unfortunately, selenium does not support set cookies 
            # from a difference domain.
            # But this can be solved by jumping to an error page 
            # of that domain first and set cookies then.
            # Everything is done before we request the targeted page.
            prev_url = self.browser.current_url
            [cookies, url] = pickle.load(stream)
            self.browser.get("https://studyh5.zhihuishu.com/{}".format(
                            random_string(length=randrange(8, 12))))
            for cookie in cookies:
                self.browser.add_cookie(cookie)
            self.browser.get(prev_url)
            return url

    def remove_user_info(self):
        os.remove(self.user_info_path())

    def site_supported(self):
        return self.browser.current_url.find("zhihuishu.com") != -1

    def course_url_invalid(self):
        return self.locate_player_area(patience=None) is None 

    def locate_player_area(self, patience=12):
        return self.find_element(By.XPATH, 
                    '//*[@class="videoArea"]', patience=patience) 

    def login_requested(self):
        return self.browser.current_url.find("login") != -1

    def abort_lifetime_timer(self):
        self.lifetime_timer.abort()
        Thread.join(self.lifetime_timer)
        self.lifetime_timer = None

    def life_ends(self):
        if self.lifetime_timer and not self.lifetime_timer.is_alive():
            return True
        else:
            return False

    def abort_video_timer(self):
        self.video_timer.abort()
        Thread.join(self.video_timer)
        self.video_timer = None

    def video_timer_dead(self):
        if self.video_timer and not self.video_timer.is_alive():
            return True
        else:
            return False

    def find_element(self, by, pattern, patience=12):
        try:
            if patience is not None:
                element = WebDriverWait(self.browser, patience).until(
                            EC.presence_of_element_located((by, pattern)))
            else:
                element = self.browser.find_element(by, pattern)
            return element
        except:
            return None

    def find_elements(self, by, pattern, patience=12):
        try:
            if patience is not None:
                elements = WebDriverWait(self.browser, patience).until(
                            EC.presence_of_all_elements_located((by, pattern)))
            else:
                elements = self.browser.find_elements(by, pattern)
            return elements
        except:
            return []

    # don't do any movement before move to a located element.
    def move_to_element(self, element):
        actions = ActionChains(self.browser)
        actions.move_to_element_with_offset(element, uniform(6, 10), uniform(6, 10))
        actions.pause(uniform(0.05, 0.10))
        actions.move_by_offset(uniform(-3, 3), uniform(-3, 3))
        actions.pause(uniform(0.05, 0.10))
        actions.move_by_offset(uniform(-2, 2), uniform(-2, 2))
        actions.pause(uniform(0.05, 0.10))
        actions.perform()

    def move_and_click(self, element):
        actions = ActionChains(self.browser)
        actions.move_to_element_with_offset(element, uniform(6, 10), uniform(6, 10))
        actions.move_by_offset(uniform(-3, 3), uniform(-3, 3))
        actions.pause(uniform(0.05, 0.10))
        actions.move_by_offset(uniform(-2, 2), uniform(-2, 2))
        actions.pause(uniform(0.05, 0.10))
        actions.click_and_hold()
        actions.pause(uniform(0.05, 0.10))
        actions.release()
        actions.pause(uniform(0.05, 0.10))
        actions.move_by_offset(uniform(-3, 3), uniform(-3, 3))
        actions.pause(uniform(0.05, 0.10))
        actions.move_by_offset(uniform(-2, 2), uniform(-2, 2))
        actions.perform()

    def locate_next_unwatched_video(self, patience=12):
        return self.find_element(By.XPATH, 
                    '//li[contains(@class, "clearfix video") ' + 
                    'and not(.//b[@class="fl time_icofinish"])]', 
                    patience=patience)

    def locate_speed_control_button(self, patience=12):
        control_button = self.find_element(By.XPATH, '//*[@class="speedBox"]', 
                            patience=patience)
        return control_button

    def locate_speed_choice(self, patience=12):
        speed_button = self.find_element(By.XPATH, '//*[@class="speedList"]'
                                        '//div[@class="speedTab speedTab15"]', 
                        patience=patience)
        return speed_button

    def has_speed_up(self):
        return self.find_element(By.XPATH, 
                '//*[@class="speedBox"]'
                '//span[not (.//*) and contains(text(),"1.5")]', 
                patience=None) is not None

    def locate_play_button(self):
        return self.find_element(By.XPATH, 
                    '//div[@class="playButton"]', 
                    patience=None)

    def video_length(self, patience=12):
        return as_seconds(self.find_element(By.XPATH, 
                    '//li[@class="clearfix video current_play"]'
                    '//*[@class="time fl"]',
                    patience=patience).get_attribute("textContent"))

    def video_finished(self):
        return self.find_element(By.XPATH, 
                    '//*[@class="clearfix video current_play"]'
                    '//*[@class="fl time_icofinish"]', 
                    patience=None)

    def locate_question_choice(self):
        answer_choices = self.find_elements(By.XPATH, 
                        '//ul[@class="topic-list"]//li[@class="topic-item"]',
                        patience=None)
        if answer_choices:
            return choice(answer_choices)
        else:
            return None

    def locate_question_close_button(self):
        button = self.find_element(By.XPATH, 
                    '//*[@class="el-dialog__footer"]//*[@class="btn"]', 
                    patience=None)
        return button

    def locate_notice_close_button(self):
        caution_button = self.find_element(By.XPATH, 
                            '//*[@class="el-dialog__wrapper dialog-aberrant" '
                            'and not (contains(@style, "display: none"))]'
                            '//*[@class="el-button btn el-button--primary"]', 
                            patience=None)
        if caution_button:
            print(strftime("%H:%M:%S: {}", localtime())  \
                 .format("Caution catched, aborting..."))
            self.die(close_browser=False, status=1)

        # The outermost layer
        button = self.find_element(By.XPATH, 
                        '//*[@class="el-dialog__wrapper dialog-warn" '
                        'and not (contains(@style, "display: none"))]'
                        '//button[@class="el-button btn el-button--primary"]', 
                        patience=None)
        if button:
            return button

        button = self.find_element(By.XPATH, 
                        '//*[@class="el-dialog__wrapper dialog-tips"'
                        'and not (contains(@style,"none"))]'
                        '//button[@class="el-button btn el-button--primary"]', 
                        patience=None)
        if button:
            return button
        
        # The innermost layer
        # This type of button is same as the close button of question
        # except for the different session and context.
        button = self.find_element(By.XPATH, 
                    '//*[@class="el-dialog__header"]'
                    '//*[@class="iconfont iconguanbi"]', 
                    patience=None)
        if button.is_displayed() and not self.locate_question_choice():
            return button

        return None

    def close_question_if_any(self):
        question_choice = self.locate_question_choice()
        while question_choice is not None:
            try:
                self.move_and_click(question_choice)
            except:
                self.move_and_click(self.locate_question_choice())

            close_button = self.locate_question_close_button()
            if close_button is not None:
                try:
                    self.move_and_click(close_button)
                except:
                    self.move_and_click(self.locate_question_close_button())

            sleep(uniform(0.8, 1.2))
            question_choice = self.locate_question_choice()

    def close_Notice_if_any(self):
        while self.locate_notice_close_button():
            try:
                self.close_question_if_any()
                self.move_and_click(self.locate_notice_close_button())
            except:
                self.close_question_if_any()
                self.move_and_click(self.locate_notice_close_button())
            sleep(uniform(0.8, 1.2))
    
    def close_pop_up_window_if_any(self):
        self.close_question_if_any()
        self.close_Notice_if_any()

    def select_next_unwatched_video(self):
        try:
            self.close_pop_up_window_if_any()
            self.move_and_click(self.locate_next_unwatched_video())
        except:
            self.close_pop_up_window_if_any()
            self.move_and_click(self.locate_next_unwatched_video())

    def play_video(self):
        try:
            self.close_pop_up_window_if_any()
            self.move_to_element(self.locate_player_area())
        except:
            self.close_pop_up_window_if_any()
            self.move_to_element(self.locate_player_area())
        try:
            self.close_pop_up_window_if_any()
            self.move_and_click(self.locate_play_button())
        except:
            self.play_video()
            return

    def speed_up(self):
        try:
            self.close_pop_up_window_if_any()
            self.move_to_element(self.locate_player_area())
        except:
            self.close_pop_up_window_if_any()
            self.move_to_element(self.locate_player_area())
        try:
            self.close_pop_up_window_if_any()
            self.move_to_element(self.locate_speed_control_button())
        except:
            self.speed_up()
            return
        try:
            self.close_pop_up_window_if_any()
            self.move_and_click(self.locate_speed_choice())
        except:
            self.speed_up()
            return

        self.speed = 1.5

    def die(self, close_browser=True, status=0):
        if self.video_timer:
            self.abort_video_timer()
        if self.lifetime_timer:
            self.abort_lifetime_timer()
        if close_browser:
            self.browser.close()
            self.browser.quit()
        exit(status)

    def run(self):
        if self.lifetime_timer:
            self.lifetime_timer.start()

        self.close_pop_up_window_if_any()
        while self.locate_next_unwatched_video(patience=5):
            self.select_next_unwatched_video() 
            sleep(uniform(1.0, 2.0))
            # Set timer in case of the video getting blocked unexpectedly,
            # causing the program wait endlessly,
            # which is likely to be caused by a pop-up window never handled by user
            self.video_timer = Timer(duration=self.video_length() + 600)
            self.video_timer.start()
            while not self.video_finished():
                if self.life_ends():
                    print("Notice: program exit as schedule")
                    self.die()

                if self.video_timer_dead():
                    print("Error: exception occurs: video does not end as expected")
                    self.die(close_browser=False, status=1)

                if self.locate_play_button() and not self.video_finished():
                    self.play_video()

                if not self.has_speed_up():
                    self.speed_up()
                
                sleep(uniform(2.5, 3.0))

            self.abort_video_timer()
            sleep(uniform(1.0, 2.0))

        self.die()


def main():
    lifetime_timer = None 
    if len(sys.argv) > 1:
        lifetime_timer = Timer(as_seconds(sys.argv[1])) 
    bot = Bot(lifetime_timer)
    bot.run()


if __name__ == '__main__':
    main()