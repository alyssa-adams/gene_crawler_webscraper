from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import re
import time
import os
import pickle
import pandas as pd
import csv
import math
import json


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

        # Set max loading time
        browser.set_page_load_timeout(10)

        # start at LAST page and go forwards
        time.sleep(10)
        nav_buttons = browser.find_elements_by_class_name('footable-page-link')
        nav_buttons[-1].click()

        # restart it where it broke
        if restart:

            # read in log, get last page it was on
            f = open("log.txt", "r")
            log_contents = f.read()
            last_page = re.findall('page \d+', log_contents)[-1]
            last_page = int(last_page.split()[-1])
            #last_page = 231  ############################ <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

            for _ in range(math.floor(last_page/5)):
                nav_buttons = browser.find_elements_by_class_name('footable-page-link')
                nav_buttons[2].click()  # jump back 5 pages
                time.sleep(1)
            for _ in range(last_page % 5):
                nav_buttons = browser.find_elements_by_class_name('footable-page-link')
                nav_buttons[-(last_page+3)].click()  # jump back 1 page
                time.sleep(1)
            time.sleep(5)

        # Get the current page number, so we know which page we are on
        pages = browser.find_element_by_class_name("label.label-default").text
        numbers = re.findall(' \d+ ', pages)
        page_here = int(numbers[0].strip())
        page_last = int(numbers[1].strip())


        # ============ GO THROUGH EACH PAGE, BACKWARDS ===============

        # put in a huge try/except here, because if there's an exception, it needs to clear out the tmp dir
        try:

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
                        'archive_button': archive_button,
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

                    # if this breaks, then it means the button isn't clickable for some reason, and skip
                    try:
                        if data[i]['archive_button']:
                            data[i]['archive_button'].click()
                        else:
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
                        try:
                            browser.find_elements_by_tag_name("img")[0].click()
                        except:
                            message = 'skipped ' + title + ' on page ' + str(page_number)
                            # save to log
                            with open("log.txt", "a+") as file_object:
                                file_object.write(message + '\n')
                            continue

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
                    time.sleep(5)
                    browser.close()
                    browser.switch_to.window(window_before)


                # save to file
                df = pd.DataFrame(data)
                df = df.transpose()
                #df = df.drop(['archive_button'], axis=1)
                df.to_csv(os.path.join(self.global_variables['download_folder'], "data_df_" + str(page_number) + ".csv"))
                print('saved page ' + str(page_number))

                # go to the next page of urls
                loaded = False
                timer = 0
                while loaded == False and timer < 20:
                    nav_buttons = browser.find_elements_by_class_name('footable-page-link')
                    time.sleep(5)
                    if len(nav_buttons) > 1:
                        nav_buttons[1].click()
                        time.sleep(5)
                        loaded = True
                    else:
                        timer += 1

                pages = browser.find_element_by_class_name("label.label-default").text
                numbers = re.findall(' \d+ ', pages)

                # see if it actually went to the next page
                # if these are the same, then it didn't go to the next page and need to try higher button (it added pages)
                if int(numbers[0].strip()) == page_here:

                    # go to the next page of urls
                    loaded = False
                    timer = 0
                    while loaded == False and timer < 20:
                        nav_buttons = browser.find_elements_by_class_name('footable-page-link')
                        time.sleep(5)
                        if len(nav_buttons) > 1:
                            nav_buttons[1].click()
                            loaded = True
                            time.sleep(5)
                        else:
                            timer += 1

                    # if still didn't work, then there's a problem
                    pages = browser.find_element_by_class_name("label.label-default").text
                    numbers = re.findall(' \d+ ', pages)
                    if int(numbers[0].strip()) == page_here:
                        browser.quit()
                        quit()

                page_here = int(numbers[0].strip())

            return True

        # Don't flood the tmp dir!!!!!!
        except:
            browser.quit()
            return False

    def donut_ig(self, browser, restart):

        '''
        Does the IG annoying work of likes and follows without getting banned.
        TODO: Add follows from post engagement, then likes
        TODO: Add follows and likes from hashtag search
        TODO: Check if followed first before new follow

        Likes:
        300-400 likes per day (of followed accounts)
        You can either like something every 28 – 36 seconds.
        Or do it at 1000 likes at a time, If you go this route you need to take a 24-hour break after hitting the limit before liking again.

        Follows:
        7-13 follows per hour or 100-150 follows per day
        one follow every 28 – 38 seconds. But also under 200 an hour.
        Similar to likes, if you hit 1000 follows a day and below 200 an hour (1000 a day, with a 24-hour break)

        :param browser: Browser object
        :param restart: Don't need
        :return: None, doesn't even need to finish, just needs to do some actions.
        '''

        # Set max loading time
        browser.set_page_load_timeout(10)

        # load in relevant data for login forms
        with open('info.json') as json_file:
            data = json.load(json_file)
            username = data['info']['username']
            password = data['info']['password']

        # ========================== log in ==========================

        username_field = browser.find_element_by_xpath('/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div[2]/div/label/input')
        username_field.send_keys(username)
        password_field = browser.find_element_by_xpath(
            '/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div[3]/div/label/input')
        password_field.send_keys(password)

        log_in = browser.find_element_by_xpath('/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div[4]/button/div')
        log_in.click()
        time.sleep(5)

        # dont save login information
        not_now = browser.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div/div/button')
        not_now.click()
        time.sleep(5)

        # dont turn on notifications
        not_now = browser.find_element_by_xpath('/html/body/div[4]/div/div/div/div[3]/button[2]')
        not_now.click()
        time.sleep(5)

        """
        300-400 likes per day (of followed accounts)
        You need to keep those under 12-14 an hour, with a 350 – 400-second break between each one
        You can either like something every 28 – 36 seconds. 
        Or do it at 1000 likes at a time, If you go this route you need to take a 24-hour break after hitting the limit before liking again.
        
        7-13 follows per hour or 100-150 follows per day
        one follow every 28 – 38 seconds. But also under 200 an hour. 
        Similar to likes, if you hit 1000 follows a day and below 200 an hour (1000 a day, with a 24-hour break)
        """

        # ========================== LIKES ==========================

        # scroll down and like 100 posts from followed accounts
        # one like per 35 seconds

        max_likes = 0
        n_likes = 0
        SCROLL_PAUSE_TIME = 25

        # Get scroll height
        last_height = browser.execute_script("return document.body.scrollHeight")

        while True and n_likes < max_likes:

            # look for a thing to like!
            like_buttons = browser.find_elements_by_xpath('//*[@aria-label="Like"]')
            if len(like_buttons) > 0:
                like_buttons[0].click()
                n_likes += 1
                print("Like!")

            # Scroll down to bottom
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height


        # ========================== FOLLOWS ==========================

        # click on "discover"
        discover_button = browser.find_element_by_xpath('//*[@aria-label="Find People"]')
        discover_button.click()
        time.sleep(5)

        max_follows = 100
        n_follows = 0
        SCROLL_PAUSE_TIME = 30

        while n_follows < max_follows:

            # Like and follow this panel only
            panel = browser.find_elements_by_class_name("pKKVh")[0]
            panel.click()
            time.sleep(2)

            # follow
            follow_button = browser.find_element_by_xpath('//*[@type="button"]')
            follow_button.click()
            print("Follow!")
            time.sleep(SCROLL_PAUSE_TIME / 2)

            # like
            like_button = browser.find_elements_by_xpath('//*[@aria-label="Like"]')[1]
            like_button.click()
            print("Like!")
            time.sleep(SCROLL_PAUSE_TIME / 2)

            # close panel
            x_button = browser.find_element_by_xpath('//*[@aria-label="Close"]')
            x_button.click()

            # refresh page
            browser.refresh()
            time.sleep(5)

    def jgi_taxonomy(self, browser, restart):

        '''

        :param browser:
        :param restart:
        :return:
        '''

        results_file = 'metadata.tsv'

        # if restart, get the line number
        if restart:
            with open(results_file, 'r') as readfilequick:
                reader = csv.reader(readfilequick)
                filecontents = readfilequick.read()
                n_lines = len(re.findall('\n', filecontents)) - 1
                last_row = filecontents.split('\n')[-2]
                last_study = last_row.split('\t')[-1]

        # save to tsv file!
        f = open(results_file, 'a+')
        tsv_writer = csv.writer(f, delimiter='\t')

        # if not restart, make a file header
        if not restart:
            header = ["taxon_object_id", "release_date", "ecosystem", "ecosystem_category", "ecosystem_subtype",
                      "habitat", "is_published", "isolation", "isolation_country", "sequencing_method",
                      "specific_ecosystem", "study"]
            tsv_writer.writerow(header)

        # make pickle jar if don't already have one 
        pickle_dir = 'pickle_jar'
        if not os.path.exists(pickle_dir):
            os.mkdir(pickle_dir)

        # check to see if there's already a pickle for this
        studies_pickle = 'studies.p'

        # if so, then load it in
        if os.path.isfile(os.path.join(pickle_dir, studies_pickle)):
            studies = pickle.load(open(os.path.join(pickle_dir, studies_pickle), "rb"))

        # if not, then save to file for later
        else:
            with open(os.path.join(pickle_dir, studies_pickle), 'wb') as f:

                # get studies that are relevant
                studies = browser.find_elements_by_xpath("//*[starts-with(@id, 'rect:')]")
                studies = list(filter(lambda x: 1028 < float(x.get_attribute('x')), studies))
                studies = list(map(lambda x: x.get_attribute('id'), studies))
                studies = list(map(lambda x: x.split(':'), studies))
                url0 = "https://img.jgi.doe.gov/cgi-bin/m/main.cgi?section=TreeFile&page=txdetails&type=taxonomy&domain="
                url1 = "&phylum="
                url2 = "&ir_class="
                url3 = "&ir_order="
                url4 = "&family="
                url5 = "&genus="
                studies = list(map(lambda x: url0 + x[1] + url1 + x[2] + url2 + x[3] + url3 + x[4] + url4 + x[5] + url5 + x[6], studies))

                pickle.dump(studies, f)


        # if restart, start on the study it left off on!
        if restart:
            n_study = studies.index(last_study)
            studies = studies[n_study:]


        # loop through each study url
        for study in studies:

            print(study)

            try:
                browser.get(study)
            except:
                browser.get(study)
            time.sleep(2)

            # show all rows in the table
            try:
                menu = Select(browser.find_element_by_id('yui-pg0-0-rpp'))
            # there may not be any data in that study table
            except:
                continue

            menu.select_by_visible_text('All')
            time.sleep(10)

            # get all the links
            url0 = 'https://img.jgi.doe.gov/cgi-bin/m/'
            links = browser.find_elements_by_xpath("//a[@href]")
            links = list(map(lambda x: x.get_attribute("href"), links))
            links = list(filter(lambda x: re.search('taxon_oid', x), links))


            for link in links[:2]:  # <<<<<<<<<<

                # go to the link
                try:
                    browser.get(link)
                except:
                    browser.get(link)
                time.sleep(2)

                # get the data from this page

                table = browser.find_element_by_xpath("/html/body/div[6]/div[4]/form/table")
                table_text = table.text

                # Taxon Object ID, Release Date, Ecosystem Category, Ecosystem Subtype, Habitat, Is Published,
                # Isolation, Sequencing Method, Specific Ecosystem, Category, subtype
                taxon_object_id_re = 'Taxon ID .*'
                release_date_re = 'Release Date .*'
                ecosystem_re = 'Ecosystem .*'
                ecosystem_category_re = 'Ecosystem Category .*'
                ecosystem_subtype_re = 'Ecosystem Subtype .*'
                habitat_re = 'Habitat .*'
                is_published_re = 'Is Published .*'
                isolation_re = 'Isolation .*'
                isolation_country_re = 'Isolation Country .*'
                sequencing_method_re = 'Sequencing Method .*'
                specific_ecosystem_re = 'Specific Ecosystem .*'

                row_regex = [taxon_object_id_re, release_date_re, ecosystem_re, ecosystem_category_re, ecosystem_subtype_re,
                             habitat_re, is_published_re, isolation_re, isolation_country_re, sequencing_method_re, specific_ecosystem_re]

                # loop through each to find a match, then parse and make a row
                row = []
                for regex in row_regex:

                    # check to see if this calue is present
                    cell = re.findall(regex, table_text)
                    if len(cell) == 0:
                        cell = None
                        row.append(cell)
                        continue
                    else:
                        cell = cell[0]

                    # get rid of the header text
                    cell = cell.split()
                    if regex in [ecosystem_re, habitat_re, isolation_re]:
                        cell = ' '.join(cell[1:])
                    else:
                        cell = ' '.join(cell[2:])

                    # save to a row
                    row.append(cell)

                # tack on the study link for restarting purposes
                row.append(study)
                tsv_writer.writerow(row)
                print(row[0])

