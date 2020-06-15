from selenium import webdriver
import re
import time
import os
import csv
from jobs import Jobs


# ============= This scraper gets all the news articles from https://www.covid19-archive.com/ ============

class Scraper:

    def __init__(self):

        self.global_variables = {
            'download_folder': None,
            'screenshot_folder': None,
            'log_file': None,
            'urls': {
                'covid_news': 'https://www.covid19-archive.com/'
            }
        }


    def make_browser(self, os_type):

        '''
        Sets up a Firefox browser with all the wanted parameters and settings
        :os_type: Either Mac os for laptop, or Linux for remote headless firefox
        :return: The browser object
        '''

        # Make the directory for downloaded files
        if not os.path.exists('downloaded_files'):
            os.makedirs('downloaded_files')
        self.global_variables['download_folder'] = 'downloaded_files'

        if not os.path.exists('screenshot_folder'):
            os.makedirs('screenshot_folder')
        self.global_variables['screenshot_folder'] = 'screenshot_folder'


        if os_type == 'mac_laptop':

            gecko_path = '/Users/gigglepuss/PycharmProjects/scraper/geckodriver'

            # Set download location and disable annoying pop-up
            fp = webdriver.FirefoxProfile()
            fp.set_preference("browser.download.folderList", 2)
            fp.set_preference('browser.download.manager.showWhenStarting', False)
            #fp.set_preference("browser.download.dir", '/Users/gigglepuss/PycharmProjects/scraper/downloaded_files')
            fp.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/fna, application/fna, application/x-download')  # type of file to download

            # define the browser and the driver location
            browser = webdriver.Firefox(executable_path=gecko_path, firefox_profile=fp)

        elif os_type == 'linux_server':

            gecko_path = '/home/alyssa/anacrawler/geckodriver'

            options = webdriver.FirefoxOptions()
            options.add_argument('-headless')
            browser = webdriver.Firefox(executable_path=gecko_path, firefox_options=options)

        else:
            print("Which os are you using?")
            browser = None
            quit()

        return browser


    def save_screenshot(self, filename):

        browser.save_screenshot(os.path.join(self.global_variables['screenshot_folder'], filename))


    def crawl_and_scrape(self, browser, job, restart):

        '''
        Wraps each individual job here as a general run function
        :param browser: The browser object
        :param job: str, from list of jobs
        :return: None
        '''

        # now go to main url and wait to load
        url = self.global_variables['urls'][job]
        browser.get(url)
        time.sleep(12)

        # perform the actual job
        result = eval('Jobs.' + job + '(self, browser=browser, restart=restart)')

        # check for success or error
        if not result:
            self.save_screenshot('error.png')


if __name__ == '__main__':

    scraper = Scraper()
    restart = True
    os_type = 'mac_laptop'  # mac_laptop or linux_server
    job = 'covid_news'
    browser = scraper.make_browser(os_type)
    scraper.crawl_and_scrape(browser=browser, job=job, restart=restart)
    browser.quit()
