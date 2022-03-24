import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry 
from langdetect import detect
from bs4 import BeautifulSoup
from konlpy.tag import Okt
from collections import Counter
from urllib.parse import urljoin
import urllib.robotparser 
import string
import matplotlib.pyplot as plt
import pandas as pd
from operator import itemgetter
from matplotlib import font_manager


def main():
    #select link
    options = ["https://www.cau.ac.kr","https://es.wikipedia.org/","https://www.devry.edu/"]
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
    
    words_in_corpus, unique_words, crawledWords = language_processing(soupString)
    
    print("The URL is in the following language: ", detect(soupString))
    print("Total words in the collection: ", words_in_corpus)
    print("Number of unique words in the collection: ", unique_words)
    

    report.append(urlList)
    report.append(outlinkCount)
    save_htmls(file_path, file_num, allSoup)
    save_files(file_path,file_num,crawledWords,soup,urlList, outlinkCount)


#detects if the html string is in either Korean or Non-Korean language.
#Counts the 100 most frequent words, total words in the collection, and the number of unique words and returns them.
def language_processing(soupString):

    if detect(soupString) != "ko": 
        soupString = (''.join([x for x in soupString if x in string.ascii_letters + '\'- ']))
        zipf = soupString.lower().split()
        countTrue = Counter(soupString.lower().split())
        words_in_corpus = len(soupString)       #Total words in the collection
        unique_words = len(countTrue)           #Vocabulary size (number of unique words)
        crawledWords = (countTrue.most_common(100))
        zipfs_law(zipf)                    #Pass total words to zipf's method
       
    else:
        okt = Okt()                             
        korean_words = okt.nouns(soupString)    # From the converted string, extract only Korean nouns
        countTrue = Counter(korean_words)
        words_in_corpus = len(korean_words)       #Total words in the collection
        unique_words = len(countTrue)            #Vocabulary size (number of unique words)   
        crawledWords = countTrue.most_common(100) 
        zipfs_law(korean_words)                    #Pass total words to zipf's method
         

    return words_in_corpus, unique_words, crawledWords

def zipfs_law(zipf):
    font_path = '/users/jjung/NotoSansKR-Medium.otf'        #Your local file path where the Korean font is located at
    font_prop = font_manager.FontProperties(fname=font_path)
    print('=' * 60)
    frequency = {}
    
    for word in zipf:
        count = frequency.get(word,0)
        frequency[word] = count +1
        
    rank = 1
    rslt = pd.DataFrame(columns=['Rank','Frequency','Frequency*Rank'])
    collection = sorted(frequency.items(),key=itemgetter(1), reverse=True)
    for word, freq in collection:
        rslt.loc[word] = [rank, freq, rank*freq]
        rank = rank + 1
    print(rslt)
    
    plt.figure(figsize=(20,20))
    plt.ylabel("Frequency")
    plt.xlabel("Words")
    plt.xticks(rotation = 90, font_properties = font_prop)
    
    for word, freq in collection[:30]:
        plt.bar(word,freq)
    plt.show()
    
def crawl_domain(mainURL,crawled):
    
    #response = requests.get(mainURL, verify = False)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.1)
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
            elif "javascript:void(0);" == append_url:
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
    retry = Retry(connect=3, backoff_factor=0.1)
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