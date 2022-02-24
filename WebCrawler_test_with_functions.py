from itertools import count
import os
import requests
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

def main():
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

    words_list = check_language(soup)
    save_files(file_path,file_num,words_list,soup,report)

    for links in outlinks:
        if counter > 5:
            break
        thisCounter, url, thisSoup, validOutlinks = goCrawl(mainURL, links, crawled)
        allSoup.append(thisSoup)
        
        crawled.append(links)
        urlList.append(url)
        outlinkCount.append(thisCounter)
        counter += 1
    report.append(urlList)
    report.append(outlinkCount)
    save_htmls(file_path, file_num, allSoup)
    print(words_list)
    print(crawled)
    print(report)

def crawl_domain(mainURL,crawled):
    
    response = requests.get(mainURL, verify = False)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')   # Request html from the url and use Beautifulsoup to parse

    for script in soup(["script", "style"]):    # Get rid of javascript and css from the html
        script.decompose()

    outlinks = []           
    outlinksCounter = 0               
    for append_url in soup.find_all('a', href= True):
        append_url = append_url.get('href')
        append_url = urljoin(mainURL, append_url)
        outlinks.append(append_url)  
        outlinksCounter += 1
    crawled.append(mainURL)

    return soup, outlinks, crawled

def getDisallowed(mainURL, pageVisting):
    robots = urllib.robotparser.RobotFileParser()
    robotsURL = mainURL + "/robots.txt"
    robots.set_url(robotsURL)
    robots.read()
    check = robots.can_fetch("*", pageVisting)
    return check 

def goCrawl(mainURL, url, crawled):
    page = requests.get(url, verify = False)
    thisHTML = page.text
    thisSoup = BeautifulSoup(thisHTML,'lxml')

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
                        validOutlinks.append(links)
                    else: pass
                else:
                    pass

    return thisCounter, url, thisSoup, validOutlinks

# I made an if else statement that checks the language of the html.
# If it is not Korean, then count top 100 most frequent words without using the konply library
# If it is in Korean, then use the konlpy library and count top 100 most frequent words.
def check_language(soup):
    
    text = soup.get_text()
    if detect(text) != "ko":                            
        text = (''.join(s.findAll(text=True))for s in soup.findAll('p'))
        count_words = Counter((a.rstrip(punctuation).lower() for b in text for a in b.split()))
        words_list = (count_words.most_common(100))
    else:
        soup_string = str(soup)                 # Convert the html into string
        okt = Okt()                             
        korean_noun = okt.nouns(soup_string)    # From the converted string, extract only Korean nouns
        words_only = str(korean_noun)           # Convert the nouns into string
        count_words = Counter(korean_noun)      
        words_list = count_words.most_common(100)   # Count the 100 most frequent words

    print("The URL is in the following language: ", detect(soup.text)) 
    return words_list

def save_files(file_path, file_num, words_list, soup, report):
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
    with open(filename_report, "w") as file2:
        for url, number in report:
            file2.write("{}, {}\n".format(url, number))

def save_htmls(file_path, file_num, thisSoup):
    out =1 
    for soup in thisSoup:
        filename_outhtml = f"{file_path}/repository/html_output{file_num}({out}).html"
        os.makedirs(os.path.dirname(filename_outhtml), exist_ok=True)
        with open(filename_outhtml, "w") as file:
            file.write(str(soup))
        out += 1
        print(soup)
        
  

# This for loop iterates through all the links in the outlinks list and requests the html, but currently missing a feature to
# save the visited link's html to a new file, e.g. html_output(2).html for the second visited link, html_outout(3).html for the third link, ...

    '''for item in outlinks:
    outlink_response = requests.get(item, verify = False)
    outlink_html = outlink_response.text
    outlink_soup = BeautifulSoup(outlink_html, 'html.parser')
    for script in outlink_soup(['script', 'style']):
        script.decompose()'''

if __name__ == "__main__":
    main()
