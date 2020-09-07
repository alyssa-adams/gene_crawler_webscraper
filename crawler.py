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
                'covid_news': 'https://www.covid19-archive.com/',
                'donut_ig': 'https://www.instagram.com/',
                'jgi_taxonomy': 'https://img.jgi.doe.gov/cgi-bin/m/main.cgi?section=TreeFile&page=domain&domain=all'
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

        if os_type == 'mac':

            gecko_path = '/Users/gigglepuss/PycharmProjects/scraper/geckodriver'

            # Set download location and disable annoying pop-up
            fp = webdriver.FirefoxProfile()
            fp.set_preference("browser.download.folderList", 2)
            fp.set_preference('browser.download.manager.showWhenStarting', False)
            #fp.set_preference("browser.download.dir", '/Users/gigglepuss/PycharmProjects/scraper/downloaded_files')
            fp.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/fna, application/fna, application/x-download')  # type of file to download

            # define the browser and the driver location
            browser = webdriver.Firefox(executable_path=gecko_path, firefox_profile=fp)

        elif os_type == 'linux':

            gecko_path = '/home/alyssa/anacrawler/geckodriver'
            options = webdriver.FirefoxOptions()
            options.add_argument('-headless')
            browser = webdriver.Firefox(executable_path=gecko_path, options=options)

        elif os_type == 'windows':

            gecko_path = 'C:\\Users\\Dr GigglePuss\\PycharmProjects\\gene_crawler_webscraper\\geckodriver.exe'
            browser = webdriver.Firefox(executable_path=gecko_path)

        else:
            print("Which os are you using?")
            browser = None
            quit()

        # Set max loading time
        browser.set_page_load_timeout(20)

        return browser


    def save_screenshot(self, filename):  #TODO: Screenshot on break doesn't work

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
        time.sleep(5)

        # perform the actual job
        result = eval('Jobs.' + job + '(self, browser=browser, restart=restart)')

        # check for success or error
        if not result:
            # TODO: result needs to return T/F, save screenshot of error
            #self.save_screenshot('error.png')
            result


if __name__ == '__main__':

    # TODO: Make this command-line friendly with options: os_type, job, restart
    scraper = Scraper()
    restart = True  # TODO: Generalize restart a little better
    os_type = 'windows'  # mac linux or windows
    job = 'donut_ig'
    browser = scraper.make_browser(os_type)
    scraper.crawl_and_scrape(browser=browser, job=job, restart=restart)
    browser.quit()
