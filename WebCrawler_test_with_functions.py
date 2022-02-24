from itertools import count
import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry 
import nltk
from langdetect import detect
from bs4 import BeautifulSoup
from konlpy.tag import Okt
from collections import Counter
from string import punctuation
from urllib.parse import urljoin
import re
from urllib.request import urlopen
import urllib.robotparser 
import string

def main():
    #select link
    options = ["https://www.cau.ac.kr","https://www.ipn.mx/","https://www.devry.edu/"]
    print("Which url would you like to crawl")
    count=0

    for each in options: 
        print(count, " ",each)
        count = count+1
    num = int(input())
    file_num = num+1
    mainURL = options[num]
    file_path =input("Please enter the file path that you would like to use: ")
    crawled = []
    report = []
    soup, outlinks, crawledOut  = crawl_domain(mainURL,crawled)
    crawled = crawledOut

    counter = 0
    outlinksN = 500
    urlList = []
    outlinkCount = []
    allSoup = []
    masterSoup = []
    soupString = ''

    

    for links in outlinks:
        if counter > 5:
            break
        thisCounter, url, thisSoup, validOutlinks, soupText = goCrawl(mainURL, links, crawled)

        allSoup.append(thisSoup)
        masterSoup.append(soupText)
        
        crawled.append(links)
        urlList.append(url)
        outlinkCount.append(thisCounter)
        counter += 1

    for soup in masterSoup:
        soupString = soupString + soup
    
    if detect(soupString) != "ko": 
        soupString = (''.join([x for x in soupString if x in string.ascii_letters + '\'- ']))
        countTrue = Counter(soupString.lower().split())
        crawledWords = (countTrue.most_common(100))
        
        print(crawledWords)
    else:
        okt = Okt()                             
        korean_noun = okt.nouns(soupString)    # From the converted string, extract only Korean nouns
        words_only = str(korean_noun)           # Convert the nouns into string
        countTrue = Counter(korean_noun)      
        crawledWords = countTrue.most_common(100)   # Count the 100 most frequent words

    print("The URL is in the following language: ", detect(soupString)) 

    report.append(urlList)
    report.append(outlinkCount)
    save_htmls(file_path, file_num, allSoup)
    save_files(file_path,file_num,crawledWords,soup,urlList, outlinkCount)

    


def crawl_domain(mainURL,crawled):
    
    #response = requests.get(mainURL, verify = False)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    response = session.get(mainURL)

    html = response.text
    soup = BeautifulSoup(html, 'lxml')   # Request html from the url and use Beautifulsoup to parse

    for script in soup(["script", "style"]):    # Get rid of javascript and css from the html
        script.decompose()

    outlinks = []           
    outlinksCounter = 0               
    for append_url in soup.find_all('a', href= True):
        append_url = append_url.get('href')
        append_url = urljoin(mainURL, append_url)
        if append_url == mainURL:
            pass
        else:
            if "javascript:void(0)" == append_url:
                pass
            else:
                outlinks.append(append_url)  
            outlinksCounter += 1
    crawled.append(mainURL)
    #print(outlinks)

    return soup, outlinks, crawled

def getDisallowed(mainURL, pageVisting):
    robots = urllib.robotparser.RobotFileParser()
    robotsURL = mainURL + "/robots.txt"
    robots.set_url(robotsURL)
    robots.read()
    check = robots.can_fetch("*", pageVisting)
    return check 

def goCrawl(mainURL, url, crawled):
    #page = requests.get(url, verify = False)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    page = session.get(url)

    thisHTML = page.text
    thisSoup = BeautifulSoup(thisHTML,'lxml')
    soupText = thisSoup.get_text()

    for script in thisSoup(["script", "style"]):
        script.decompose()

    thisOutlinks = []
    thisCounter = 0
    for append_url in thisSoup.find_all('a', href= True):
        append_url = append_url.get('href')
        append_url = urljoin(url, append_url)
        thisOutlinks.append(append_url)  
        thisCounter += 1
    
    validOutlinks = []
    for links in thisOutlinks:
        if links in validOutlinks:
            if (links in crawled):
                pass
            else:
                if getDisallowed(mainURL, links) == True:
                    if "https://" in links:
                        if "javascript:void(0)" in links:
                            pass
                        else:
                            validOutlinks.append(links)
                    else:
                         pass
                else:
                    pass

    return thisCounter, url, thisSoup, validOutlinks, soupText

# I made an if else statement that checks the language of the html.
# If it is not Korean, then count top 100 most frequent words without using the konply library
# If it is in Korean, then use the konlpy library and count top 100 most frequent words.

def save_files(file_path, file_num, words_list, soup, urlList, outlinkCount):
    filename_words = f"{file_path}/repository/words{file_num}.csv"
    filename_html = f"{file_path}/repository/html_output{file_num}.html"
    filename_report = f"{file_path}/repository/report{file_num}.csv"

    os.makedirs(os.path.dirname(filename_html), exist_ok=True)
    with open(filename_html, "w") as file:
        file.write(str(soup))

    os.makedirs(os.path.dirname(filename_words), exist_ok=True)     # Create a folder named repository and save files
    with open(filename_words, 'w', encoding = "utf-8-sig") as file:
        for noun, number in words_list:
            file.write("{}, {}\n".format(noun, number))
    
    os.makedirs(os.path.dirname(filename_report),exist_ok=True)
    with open(filename_report, "w", encoding = "utf-8") as file:
        for i in range(len(urlList)):
            file.write("{}, {}\n".format(urlList[i], outlinkCount[i]))

def save_htmls(file_path, file_num, thisSoup):
    out =1 
    for soup in thisSoup:
        filename_outhtml = f"{file_path}/repository/html_output{file_num}({out}).html"
        os.makedirs(os.path.dirname(filename_outhtml), exist_ok=True)
        with open(filename_outhtml, "w", encoding = "utf-8-sig") as file:
            file.write(str(soup))
        out += 1
        #print(soup)
        
if __name__ == "__main__":
    main()