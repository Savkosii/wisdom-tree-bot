import os
import sys
import pickle
from time import sleep, localtime, strftime
from threading import Thread, Lock
from random import choice, randrange, uniform
from os.path import dirname, basename 
from string import ascii_letters, digits
from selenium.webdriver import Chrome
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def override(method):
    method.is_overridden = True
    return method


# A decorator for method, serving like `synchronized` keyword in java
def synchronized(method):
    outer_lock = Lock()
    lock_name = "__" + method.__name__ + "_lock" + "__"

    def wrapper(self, *args, **kws):
        with outer_lock:
            if not hasattr(self, lock_name):
                setattr(self, lock_name, Lock())
            lock = getattr(self, lock_name)
            with lock:
                return method(self, *args, **kws)

    return wrapper


class Utilities:
    def as_seconds(time_str):
        mult = 1
        seconds = 0
        time_components = time_str.split(':')
        while time_components:
            seconds += int(time_components.pop().strip()) * mult
            mult *= 60
        return seconds

    def random_string(length=26, chars=ascii_letters + digits):
        return ''.join([choice(chars) for _ in range(length)])
    
    def search_file_recursively(filename, search_path="."):
        result = []
        for root, _, files in os.walk(search_path):
            if filename in files:
                result.append(os.path.join(root, filename))
        return result

    def file_exists(file_path):
        return os.path.exists(file_path)


class Timer(Thread):
    # Fields related to time are all represented as seconds
    # pivotal: flag that indicates whether when the timer is done,
    # the program needs to exit
    def __init__(self, duration=None, cycle=1.0, pivotal=False):
        Thread.__init__(self)
        self.current_time = 0
        self.duration = duration
        self.cycle = cycle
        self.stop = False
        self.pivotal = pivotal

    def run(self):
        while not self.stop and not self.reach_end():
            self.time_increment()
            sleep(self.cycle)
        if self.pivotal:
            print("Program exit as schedule")
            os._exit(0)

    @synchronized
    def abort(self):
        self.stop = True

    @synchronized
    def reach_end(self):
        if self.duration is None:
            return False
        else:
            return self.get_current_time() >= self.duration

    @synchronized
    def get_current_time(self):
        return self.current_time 

    @synchronized
    def time_increment(self):
        self.current_time += 1


class Bot:
    def __init__(self):
        service = Service(ChromeDriverManager(version="latest", path=".").install())

        self.driver_path = self.locate_latest_driver_path()

        if self.driver_path is None:
            print("Error: cannot locate driver executable path")
            exit(1)

        self.driver_version = basename(dirname(self.driver_path))

        if not self.driver_patched():
            self.patch_driver()

        options = Options()
        options.add_experimental_option("excludeSwitches", ['enable-automation']) 
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--start-maximized")

        self.browser = Chrome(service=service, options=options)

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
                sleep(1)
                # recheck
                if self.course_url_invalid():
                    print("Error: cannot locate video player from {}" \
                        .format(self.browser.current_url))
                    print("Please go to the video page manually")
                    while self.course_url_invalid():
                        sleep(1)

            print("Notice: Successfully jump to {}"\
                    .format(self.browser.current_url))

        if self.user_info_exists():
            self.remove_user_info()
        self.save_user_info()
            
        self.timer = None

        self.speed = 1.0
        
    def keys_path(self):
        return self.driver_version + '-patch.pickle'

    def original_keys(self):
        return bytes('$cdc_asdjflasutopfhvcZLmcfl_', 'utf-8')

    def save_keys(self, keys):
        with open(self.keys_path(), 'wb') as stream: 
            pickle.dump(keys, stream)

    def generate_random_keys(self):
       random_string = '$' + Utilities.random_string(len(self.original_keys()) - 1)
       return bytes(random_string, 'utf-8')

    def locate_latest_driver_path(self):
        drive_name = "chromedriver"
        if sys.platform.startswith('win'):
            drive_name += '.exe'
        driver_paths = Utilities.search_file_recursively(drive_name)
        if not driver_paths:
            return None
        else:
            driver_paths.sort(key= lambda path: tuple(basename(dirname(path)).split('.')))
            return driver_paths[-1]

    def driver_patched(self):
        return Utilities.file_exists(self.keys_path())

    # Replace a specific string in the driver executable file.
    # This helps escaping the detection of website targeted. 
    def patch_driver(self):
        new_keys = self.generate_random_keys() 
        self.save_keys(new_keys)
        with open(self.driver_path, "r+b") as stream:
            res = stream.read().replace(self.original_keys(), new_keys)
            stream.seek(0)
            stream.write(res)

    def user_info_path(self):
        return "user.pickle"

    def user_info_exists(self):
        return Utilities.file_exists(self.user_info_path()) 

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
            # Unfortunately, selenium does not support set cookies from a difference domain.
            # But this can be solved by jumping to the 404 page 
            # of that domain and set cookies there.
            # Everything is done before we request the targeted page.
            [cookies, url] = pickle.load(stream)
            self.browser.get("https://studyh5.zhihuishu.com/{}".format(randrange(1, 405)))
            for cookie in cookies:
                self.browser.add_cookie(cookie)
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

    def set_timer(self, timer: Timer):
        self.timer = timer
        self.timer.start()

    def abort_timer(self):
        self.timer.abort()
        self.timer = None

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

    def move_to_element(self, element):
        actions = ActionChains(self.browser)
        actions.move_to_element_with_offset(element, uniform(2, 12), uniform(2, 12))
        actions.perform()

    def move_and_click(self, element):
        actions = ActionChains(self.browser)
        actions.move_to_element_with_offset(element, uniform(2, 12), uniform(2, 12))
        actions.pause(uniform(0.1, 0.2))
        actions.click_and_hold(element)
        actions.pause(uniform(0.05, 0.10))
        actions.release()
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
        speed_button = self.find_element(By.XPATH, '//*[@class="speedBox"]' +
                        '//*[@class="speedList"]//div[@class="speedTab speedTab15"]', 
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
        return Utilities.as_seconds(self.find_element(By.XPATH, 
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
            self.exit_driver()
            os._exit(1)

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
        # One button of this list is same as the close button of question
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
            self.move_and_click(self.locate_play_button())
        except:
            self.close_pop_up_window_if_any()
            self.move_to_element(self.locate_player_area())
            self.move_and_click(self.locate_play_button())

    def speed_up(self):
        try:
            self.close_pop_up_window_if_any()
            self.move_to_element(self.locate_player_area())
            self.move_and_click(self.locate_speed_control_button())
        except:
            self.close_pop_up_window_if_any()
            self.move_to_element(self.locate_player_area())
            self.move_and_click(self.locate_speed_control_button())
        try:
            self.move_and_click(self.locate_speed_choice())
        except:
            self.speed_up()
            return

        self.speed = 1.5

    def exit_driver(self):
        self.browser.close()
        self.browser.quit()

    def run(self):
        count = 1
        self.close_pop_up_window_if_any()
        while self.locate_next_unwatched_video(patience=5):
            print(strftime("%H:%M:%S: play {}th unwatched video", localtime())  \
                 .format(count))

            self.select_next_unwatched_video() 
            sleep(uniform(1.0, 2.0))

            # Set timer in case of the video getting blocked unexpectedly,
            # causing the program wait endlessly,
            # which is likely to be caused by a pop-up window never handled by user
            self.set_timer(Timer(duration=self.video_length() + 600))
            while not self.video_finished():
                if not self.timer.is_alive():
                    print("Error: exception occurs: video does not end as expected")
                    self.exit_driver()
                    exit(1)

                if self.locate_play_button() and not self.video_finished():
                    self.play_video()

                if not self.has_speed_up():
                    self.speed_up()
                
                sleep(3)

            self.abort_timer()
            sleep(uniform(1.0, 2.0))

            count += 1

        self.exit_driver()


def main():
    if len(sys.argv) > 1:
        duration = Utilities.as_seconds(sys.argv[1]) 
        Timer(duration=duration, pivotal=True).start()
    bot = Bot()
    bot.run()


if __name__ == '__main__':
    main()