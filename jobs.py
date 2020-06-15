from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import time
import os
import pickle
import pandas as pd
import csv


# ============= This scraper gets all the news articles from https://www.covid19-archive.com/ ============

class Jobs():

    def __init__(self):

        pass

    def covid_news(self, browser, restart):

        '''
        Starts at the last page and goes to most recent!
        :param browser: made from make_browser()
        :return: None
        Crawls each page from this website, saves the result of each page to a file in the data folder
        '''

        # click stupid load button
        #browser.find_elements_by_class_name('//*[@id="content"]/div/small/div[2]/div[1]/a')[0].click()
        #time.sleep(10)

        # Click show X results per page first (so the memory doesn't break)
        #button_xpath = "//select[@class='nt_pager_selection']/option[text()='20']"
        #browser.find_element_by_xpath(button_xpath).click()
        #time.sleep(1)

        # start at LAST page and go forwards
        time.sleep(10)
        nav_buttons = browser.find_elements_by_class_name('footable-page-link')
        nav_buttons[-1].click()

        # For going backwards
        next_page_index = 1

        # restart it where it broke
        if restart:

            # read in log, get last page it was on
            f = open("log.txt", "r")
            log_contents = f.read()
            last_page = re.findall('page \d+', log_contents)[-1]
            last_page = int(last_page.split()[-1])

            for _ in range(last_page):
                nav_buttons = browser.find_elements_by_class_name('footable-page-link')
                nav_buttons[next_page_index].click()
                time.sleep(1)
            time.sleep(5)

        # Get the current page number, so we know which page we are on
        pages = browser.find_element_by_class_name("label.label-default").text
        numbers = re.findall(' \d+ ', pages)
        page_here = int(numbers[0].strip())
        page_last = int(numbers[1].strip())


        # ============ GO THROUGH EACH PAGE, BACKWARDS ===============

        while page_here > 0:

            # for going forwards
            #page_number = page_here

            # for going backwards
            page_number = page_last-page_here+1


            # ---------- Table of links ----------

            # get titles and dates from table
            time.sleep(5)
            table = browser.find_element_by_class_name("foo-table")
            rows = table.find_elements_by_tag_name("tr")
            rows = rows[3:]

            data = {}

            for i, row in enumerate(rows):

                row_content = row.find_elements_by_tag_name("td")

                title = row_content[0].text
                # the titles sometimes have commas at the end randomly!?
                title = re.sub('\,$', '', title)

                # if row is empty, then skip
                if title == '':

                    message = 'skipped ' + title + ' on page ' + str(page_number)

                    # save to log
                    with open("log.txt", "a+") as file_object:
                        file_object.write(message + '\n')

                    continue

                try:
                    archive_button = row_content[1]
                    archive_link = archive_button.find_elements_by_tag_name('a')[0].get_attribute('href')
                except:
                    archive_button = None
                    archive_link = row_content[0]
                    archive_link = archive_link.find_elements_by_tag_name('a')[0]
                    archive_link = archive_link.get_attribute('href')


                # They are always changing the format of this website >>

                source = row_content[2].text
                date = row_content[3].text

                #author = row_content[2].text
                #source = row_content[3].text
                #date = row_content[4].text

                # convert date to standard slash date
                date = re.sub('\.', '/', date)


                # save to dict
                data[i] = {
                    'title': title,
                    'archive_link': archive_link,
                    #'archive_button': archive_button,
                    #'author': author,
                    'source': source,
                    'date': date,
                    'link': '',
                    'text': '',
                    'content_links': ''
                }

            # get handle for this window, so we can come back to it
            window_before = browser.window_handles[0]


            # ---------- Loop through archive links to click on each page and get info ----------

            # for each title, click on that element to get the link, text, and any urls in the text
            for i in list(data.keys()):

                title = data[i]['title']

                # save this window handle
                # if this breaks, then it means the button isn't clickable for some reason, and skip
                try:
                    link = browser.find_elements_by_xpath('//*[text()="' + title + '"]')[0]
                    link.click()
                    time.sleep(10)
                    window_after = browser.window_handles[1]
                    browser.switch_to.window(window_after)

                except:
                    message = 'skipped ' + title + ' on page ' + str(page_number)

                    # save to log
                    with open("log.txt", "a+") as file_object:
                        file_object.write(message + '\n')

                    continue

                # check if its that weird redirect page
                if browser.find_elements_by_class_name("THUMBS-BLOCK"):

                    # if there are no imgs, skip
                    if len(browser.find_elements_by_tag_name("img")) == 0:
                        message = 'skipped ' + title + ' on page ' + str(page_number)
                        # save to log
                        with open("log.txt", "a+") as file_object:
                            file_object.write(message + '\n')
                        continue

                    # click the FIRST one
                    browser.find_elements_by_tag_name("img")[0].click()

                # try to get the info off the page, if not then it didn't load after 10 seconds
                try:
                    # get all links in the page
                    links = []
                    elems = browser.find_elements_by_xpath("//a[@href]")
                    for elem in elems:
                        link = elem.get_attribute("href")
                        links.append(link)

                    # get page text by selecting all, then copying, basically
                    #body = browser.find_element_by_tag_name('body')
                    #text = body.text

                    # get entire page HTML source, can parse with BS later
                    text = browser.page_source

                # otherwise just skip the page
                except:

                    # if in article window, close the window, go back to last window, and get new link
                    if window_before != browser.current_window_handle:
                        browser.close()
                        browser.switch_to.window(window_before)

                    message = 'skipped ' + title + ' on page ' + str(page_number)

                    # save to log
                    with open("log.txt", "a+") as file_object:
                        file_object.write(message + '\n')

                    continue

                # get the url
                try:
                    url = browser.find_element_by_xpath("//input[@type='text']").get_attribute('value')
                except:
                    try:
                        url = links[-1].split('https://')[-1]
                    except:
                        url = ''

                # if an older archive site, get url a different way:
                if url == '':
                    url = browser.current_url.split('https://')[-1]

                data[i]['link'] = url
                data[i]['text'] = text
                data[i]['content_links'] = links


                # ========== SAVE THESE TO A FILE ==========

                message = 'got ' + title + ' on page ' + str(page_number)
                print(message)

                # save to log
                with open("log.txt", "a+") as file_object:
                    file_object.write(message + '\n')

                # close the window, go back to last window, and get new link
                browser.close()
                browser.switch_to.window(window_before)


            # save to file
            df = pd.DataFrame(data)
            df = df.transpose()
            #df = df.drop(['archive_button'], axis=1)
            df.to_csv(os.path.join(self.global_variables['download_folder'], "data_df_" + str(page_number) + ".csv"))
            print('saved page ' + str(page_number))

            # go to the next page of urls
            nav_buttons = browser.find_elements_by_class_name('footable-page-link')
            nav_buttons[next_page_index].click()
            time.sleep(5)

            pages = browser.find_element_by_class_name("label.label-default").text
            numbers = re.findall(' \d+ ', pages)

            # see if it actually went to the next page
            # if these are the same, then it didn't go to the next page and need to try higher button (it added pages)
            if int(numbers[0].strip()) == page_here:
                next_page_index += 1
                nav_buttons = browser.find_elements_by_class_name('footable-page-link')
                nav_buttons[next_page_index].click()
                time.sleep(5)

                # if still didn't work, then there's a problem
                pages = browser.find_element_by_class_name("label.label-default").text
                numbers = re.findall(' \d+ ', pages)
                if int(numbers[0].strip()) == page_here:
                    quit()

            page_here = int(numbers[0].strip())
