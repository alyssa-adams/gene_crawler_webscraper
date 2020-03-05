from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import time
import os


class JGIScraper:

    def wait_to_load_xpath(self, element_xpath):

        '''
        Wait for an element to load before moving on
        :param element_xpath: xpath
        :return: element
        '''

        result = False
        while not result:
            element = browser.find_elements_by_xpath(element_xpath)
            if len(element) > 0:
                time.sleep(3)
                return element[0]


    def wait_to_load_id(self, element_id):

        '''
        Wait for an element to load before moving on
        :param element_id: id
        :return: element
        '''

        result = False
        while not result:
            try:
                element = browser.find_element_by_id(element_id)
            except:
                element = None
            if element:
                time.sleep(1)
                return element


    def make_browser(self):

        '''
        Sets up a Firefox browser with all the wanted parameters and settings
        :return: The browser object
        '''

        # Make the directory for downloaded files
        if not os.path.exists('downloaded_files'):
            os.makedirs('downloaded_files')

        # Set download location and disable annoying popup
        fp = webdriver.FirefoxProfile()
        fp.set_preference("browser.download.folderList", 2)
        fp.set_preference('browser.download.manager.showWhenStarting', False)
        fp.set_preference("browser.download.dir", '/Users/gigglepuss/PycharmProjects/scraper/downloaded_files')
        fp.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/fna, application/fna, application/x-download')  # type of file to download

        # define the browser and the driver location
        browser = webdriver.Firefox(executable_path='/Users/gigglepuss/PycharmProjects/scraper/geckodriver', firefox_profile=fp)
        return browser


    def log_in(self, browser):

        '''
        Logs into the account as the first thing the browser does
        :param browser: Created by make_browser()
        :return: None
        '''

        # Need to log in
        login = "https://signon.jgi.doe.gov/signon"
        browser.get(login)
        time.sleep(1)

        # fill in login info and hit enter
        username = browser.find_element_by_id("login")
        username.send_keys('amadams4@wisc.edu')
        password = browser.find_element_by_id("password")
        password.send_keys('poiulkjh!')
        password.send_keys(Keys.RETURN)
        time.sleep(5)


    def get_file_urls(self, browser):

        '''
        Navigates to the page to get all the file urls
        :param browser: made from make_browser()
        :return: a list of all the wanted file urls
        '''

        # now go to main url and get the data
        url = 'https://genome.jgi.doe.gov/portal/FremicLMendotaIL/FremicLMendotaIL.info.html'
        browser.get(url)

        # Click show 500 results per page first
        button_xpath = "//*[contains(text(), '500')]"

        # wait for button to load first
        button = self.wait_to_load_xpath(button_xpath)
        button.click()

        # scroll to bottom of the page with infinite loading
        SCROLL_PAUSE_TIME = 2

        # Get scroll height
        last_height = browser.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Get the whole text of the page
        text = browser.page_source

        # search for the download buttons for our wanted data sets only
        paper_regex = "High\-resolution temporal and spatial dynamics of microbially\-mediated carbon processing revealed though time\-series metagenomics in freshwater lakes\: Lake Mendota Deep Hole Epilimnion[\s\S.]*?(?=Download\<\/a\>\<br\>)"
        papers = re.findall(paper_regex, text)

        # filter out papers that aren't the date we want
        wanted_papers = list(filter(lambda x: re.search('(Jun|Jul|Aug|Sep)', x), papers))

        # get out the urls
        base_url = "https://genome.jgi.doe.gov/"
        file_regex = "portal/.*.html"
        download_urls = list(map(lambda x: base_url + re.findall(file_regex, x)[0], wanted_papers))

        return download_urls


    def download_files(self, browser, download_urls):

        '''
        Loops through the list of download_urls and downloads each one
        :param browser: made from make_browser()
        :param download_urls: made from get_file_urls()
        :return: None
        '''

        # Now go to each url and download the files
        print(download_urls)

        for download_url in download_urls:
            browser.get(download_url)

            # scroll down to bottom of page and hit agree
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            button_id = "data_usage_policy:okButton"
            agree = self.wait_to_load_id(button_id)
            agree.click()
            time.sleep(10)

            # expand IMG folder
            img = browser.find_element_by_id(
                "downloadForm:j_id181:nodeId__ALL__JAMO__0__:nodeId__ALL__JAMO__0__0__::j_id202:handle:img:collapsed")
            img.click()
            time.sleep(5)

            # get the assembled.fna files and pick the largest one
            files = browser.page_source
            assembled_regex = "\d+\.assembled\.fna[\,\s\']+Size.*\d+\sMB"
            assembleds = re.findall(assembled_regex, files)

            if assembleds == []:
                time.sleep(5)
                assembleds = re.findall(assembled_regex, files)

            assembleds = list(set(list(map(lambda x: re.sub('\s+', ' ', x), assembleds))))
            assembleds_dict = {}
            for a in assembleds:
                fileid = a.split('.')[0]
                size = int(re.findall('\d+ MB', a)[0].split()[0])
                assembleds_dict[fileid] = size
            wanted_fileid = max(assembleds_dict, key=assembleds_dict.get)

            # actually download that file
            button_xpath = "//*[contains(text(), '" + str(wanted_fileid) + '.assembled.fna' + "')]"
            download_file = self.wait_to_load_xpath(button_xpath)
            download_file.click()

            time.sleep(15)
            print(download_url)


if __name__ == '__main__':

    scraper = JGIScraper()
    browser = scraper.make_browser()
    scraper.log_in(browser)
    urls = scraper.get_file_urls(browser)

    if not urls:
        browser = scraper.make_browser()
        scraper.log_in(browser)
        urls = scraper.get_file_urls(browser)

    scraper.download_files(browser, urls)
    browser.quit()
