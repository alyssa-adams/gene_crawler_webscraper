from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import time
import os
import pickle
import pandas as pd
import csv


# ============= This scraper gets all the news articles from https://www.covid19-archive.com/ ============

class Scraper:


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


    def get_data(self, browser):

        '''
        Navigates to the page to get all the file urls
        :param browser: made from make_browser()
        :return: None
        Crawls each page from this website, saves the result of each page to a file in the data folder
        '''

        # now go to main url and get the data
        url = 'https://www.covid19-archive.com/'
        browser.get(url)
        time.sleep(10)

        # Click show 25 results per page first (so the memory doesn't break)
        button_xpath = "//select[@class='nt_pager_selection']/option[text()='25']"
        browser.find_element_by_xpath(button_xpath).click()
        time.sleep(10)

        # restart it where it broke
        nav_buttons = browser.find_elements_by_class_name('footable-page-link')
        nav_buttons[-1].click()
        for _ in range(4):
            nav_buttons = browser.find_elements_by_class_name('footable-page-link')
            nav_buttons[2].click()
            time.sleep(5)
        nav_buttons = browser.find_elements_by_class_name('footable-page-link')
        nav_buttons[94].click()
        time.sleep(5)


        # Keep doing this and then clicking next until there isn't any next to click
        pages = browser.find_element_by_class_name("label.label-default").text
        numbers = re.findall(' \d+ ', pages)
        page1 = int(numbers[0].strip())
        page2 = int(numbers[1].strip())

        next_page_index = len(nav_buttons)-2-1

        while page1 <= page2:

            # get titles and dates from table
            table = browser.find_element_by_class_name("foo-table")
            rows = table.find_elements_by_tag_name("tr")
            rows = rows[3:]

            data = {}

            for i, row in enumerate(rows):

                row_content = row.find_elements_by_tag_name("td")
                date = row_content[0].text
                # convert to datetime
                title = row_content[1].text

                # save to dict
                data[i] = {
                    'date': date,
                    'title': title,
                    'archive_url': '',
                    'url': '',
                    'text': '',
                    'links': ''
                }

            # get handle for this window, so we can come back to it
            window_before = browser.window_handles[0]

            # for each title, click on that element to get the link, text, and any urls in the text
            for i in list(data.keys()):

                # the titles sometimes have commas at the end randomly!?
                title = data[i]['title']
                if re.search('\,$', title):
                    title = title[:-1]

                # sometimes the title contains quotes, just skip those
                try:
                    link = browser.find_elements_by_xpath('//*[text()="' + title + '"]')[0]
                    link.click()
                    time.sleep(10)

                    # save this window handle
                    window_after = browser.window_handles[1]
                    browser.switch_to.window(window_after)

                    # get all links in the page
                    links = []
                    elems = browser.find_elements_by_xpath("//a[@href]")
                    for elem in elems:
                        link = elem.get_attribute("href")
                        links.append(link)

                    # get page text by selecting all, then copying
                    body = browser.find_element_by_tag_name('body')
                    text = body.text

                except:
                    message = 'skipped ' + title
                    print(message)

                    # save to log
                    with open("data/log.txt", "a+") as file_object:
                        # Append 'hello' at the end of file
                        file_object.write(message + '\n')

                    # if in article window, close the window, go back to last window, and get new link
                    if window_before != browser.current_window_handle:
                        browser.close()
                        browser.switch_to.window(window_before)
                    continue

                # fill in the rest of the values
                try:
                    url = browser.find_element_by_xpath("//input[@type='text']").get_attribute('value')
                except:
                    url = ''
                data[i]['url'] = url
                data[i]['archive_url'] = browser.current_url
                data[i]['text'] = text
                data[i]['links'] = links

                message = 'got ' + title
                print(message)

                # save to log
                with open("data/log.txt", "a+") as file_object:
                    # Append 'hello' at the end of file
                    file_object.write(message + '\n')

                # close the window, go back to last window, and get new link
                browser.close()
                browser.switch_to.window(window_before)


            # pickle df
            df = pd.DataFrame(data)
            df = df.transpose()
            pickle.dump(df, open("data/data_df_" + str(page1) + ".pickle", "wb"))
            print('saved page ' + str(page1))

            # go to the next page of urls
            nav_buttons = browser.find_elements_by_class_name('footable-page-link')
            nav_buttons[next_page_index].click()
            time.sleep(5)

            pages = browser.find_element_by_class_name("label.label-default").text
            numbers = re.findall(' \d+ ', pages)

            # see if it actually went to the next page
            # if these are the same, then it didn't go to the next page and need to try higher button (it added pages)
            if int(numbers[0].strip()) == page1:
                next_page_index += 1
                nav_buttons = browser.find_elements_by_class_name('footable-page-link')
                nav_buttons[next_page_index].click()
                time.sleep(5)

                # if still didn't work, then there's a problem
                pages = browser.find_element_by_class_name("label.label-default").text
                numbers = re.findall(' \d+ ', pages)
                if int(numbers[0].strip()) == page1:
                    quit()

            page1 = int(numbers[0].strip())



if __name__ == '__main__':

    scraper = Scraper()
    browser = scraper.make_browser()
    scraper.get_data(browser)
    browser.quit()
