# Scrapes a Codechef contest page
# Creates a folder for the contest
# Extracts samples for each problem in the Contest

import concurrent.futures
from colorama import Fore
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class Codechef:
    def __init__(self, contest_link: str) -> None:
        # Contest link is of the form
        # https://www.codechef.com/<contest_code>?...
        self.contest_link = contest_link

    def __get_contest_name(self) -> str:
        # Given a contest link
        # Returns the contest name

        print(Fore.YELLOW + "Extracting contest name... ", end = "", flush = True)
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(options = options)
        driver.get(self.contest_link)

        element = WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "breadcrumbs")))
        element = driver.find_element(By.CLASS_NAME, 'breadcrumbs')
        inner_text = element.get_attribute('innerHTML')

        contest_name = inner_text[inner_text.rindex(";") + 1:].strip()
        driver.quit()
        print(Fore.GREEN + "Done", flush = True)
        print(Fore.YELLOW + "Contest Name: " + Fore.GREEN + contest_name, flush = True)
        return contest_name

    def __get_problem_links(self) -> list:
        # Given a link to a contest page
        # Returns a list of links to problem pages

        contest_link = self.contest_link

        print(Fore.CYAN + "Extracting problem links... ", end = "", flush = True)
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(options = options)

        contest_prefix = contest_link
        practice_substring = "/submit/"

        if "?" in contest_link:
            contest_prefix = contest_link[:contest_link.index("?")]

        contest_prefix += "/problems"

        driver.get(contest_link)

        # Wait until the problem links appear on the contest page
        element = WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "dataTable")))

        all_links = driver.find_elements(By.TAG_NAME, 'a')

        problem_links = []

        for link in all_links:
            try:
                link = str(link.get_attribute('href'))
                # A problem link is of the form:
                # https://www.codechef.com/<contest_code>/problems/<problem_code>
                if link.startswith(contest_prefix):
                    if problem_links != [] and problem_links[-1] == link:
                        continue
                    problem_links.append(link)
                elif practice_substring in link:
                    if problem_links != [] and problem_links[-1] == link:
                        continue
                    problem_links.append(link)
            except:
                # Probably the contest has not started yet
                # or there is issue loading problems on the page

                print(Fore.RED + "Attempt to Extract failed. Retrying... ", flush = True)
                return []
        
        driver.quit()
        if problem_links == []:
            # Probably the contest has not started yet
            # or there is issue loading problems on the page
            print(Fore.RED + "Attempt to Extract failed. Retrying... ", flush = True)
            return []
        print(Fore.GREEN + "Done\n", flush = True)
        return problem_links

    def __get_problem_codes(self, problem_links: list) -> list:
        # Given a list of problem links
        # Returns a list of problem codes

        problem_codes = []
        for link in problem_links:
            code = link[link.rindex('/') + 1:]
            problem_codes.append(code)
        
        return problem_codes

    def __get_samples(self, problem_link: str) -> list:
        # Given the link to the problem page
        # This function will return a list of strings
        # [input0, output0, input1, output1, ...]
        # Probably doesn't work for interactive problems

        xpath = "//body/div[@id='ember-root']/div[@id='ember242']/div[@id='ember251']/main[@id='content-regions']/section[1]/div[1]/span[3]/pre[1]"
        # xpath of the sample test cases

        xpath_prefix = "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div["
        xpath_suffix_1 = "]/div[2]/div[1]/pre[1]"
        xpath_suffix_2 = "]/div[2]/div[2]/pre[1]"

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(options = options)
        # Headless Chrome driver
        # Runs in background, doesn't open a Chrome window

        try:
            driver.get(problem_link)
            element = WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "_input_output__table_lulsq_184")))
        except:
            print(Fore.RED + "Error extracting samples from " + problem_link)
            return []

        samples = []
        i = 3

        tried_other_way = False

        # iterate for multiple test cases
        while True:
            absolute_xpath_1 = xpath_prefix + str(i) + xpath_suffix_1
            absolute_xpath_2 = xpath_prefix + str(i) + xpath_suffix_2
            try:
                element = driver.find_element(By.XPATH, absolute_xpath_1)
                samples.append(element.get_attribute('innerHTML'))
                element = driver.find_element(By.XPATH, absolute_xpath_2)
                samples.append(element.get_attribute('innerHTML'))
                i += 1
            except:
                if samples == []:
                    if not tried_other_way:
                        i = 2
                        tried_other_way = True
                        continue
                    else:
                        break
                else:
                    break

        driver.quit()
        print(Fore.YELLOW + "Extracting samples for " + problem_link + "... " + Fore.GREEN + "Done")
        return samples

    def extract_meta_data(self) -> dict:

        contest_link = self.contest_link

        # Contest Code
        contest_code = ""
        if "?" in contest_link:
            contest_code = contest_link[contest_link.rindex("/") + 1: contest_link.index("?")]
        else:
            contest_code = contest_link[contest_link.rindex("/") + 1:]

        # Contest Name
        contest_name = self.__get_contest_name()

        # Problem links
        problem_links = []
        while problem_links == []:
            problem_links = self.__get_problem_links()

        # Problem Codes
        problem_codes = self.__get_problem_codes(problem_links)

        # Problem Samples
        # Uses multi-threading to speed up the process
        # Creates N number of threads, where N is the number of problems
        # N = |Scorable problems| + |Non-scorable problems|

        with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
            results = executor.map(self.__get_samples, problem_links)

        problem_samples = list(results)

        # Problems Meta Data
        meta_data = {}
        meta_data['contest_code'] = contest_code
        meta_data['contest_name'] = contest_name
        meta_data['problem_links'] = problem_links
        meta_data['problem_codes'] = problem_codes
        meta_data['problem_samples'] = problem_samples

        return meta_data

# if __name__ == '__main__':
#     contest = Codechef('https://www.codechef.com/LTIME111A?order=desc&sortBy=successful_submissions')
#     print(contest.extract_meta_data())