from itertools import count
from operator import index
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
    wordList = []
    frequencyList = []
    soup, outlinks, crawledOut, wordList, frequencyList  = crawl_domain(mainURL,crawled, wordList, frequencyList)
    crawled = crawledOut

    counter = 0
    urlList = []
    outlinkCount = []
    allSoup = []
    masterSoup = []
    soupString = ''
    

    for links in outlinks:
        if counter > 100:
            break
        thisCounter, url, thisSoup, validOutlinks, soupText, wordList, frequencyList = goCrawl(mainURL, links, crawled, wordList, frequencyList, counter) 

        allSoup.append(thisSoup)
        masterSoup.append(soupText)
        
        crawled.append(links)
        urlList.append(url)
        outlinkCount.append(thisCounter)
        counter += 1

    for x in range(len(wordList)):
        print(wordList[x])      #check the words and which html/doc it appears in
        print(frequencyList[x])

    for soup in masterSoup:
        soupString = soupString + soup
    
    words_in_corpus, unique_words, crawledWords = language_processing(soupString)

    print("The URL is in the following language: ", detect(soupString))
    print("Total words in the collection: ", words_in_corpus)
    print("Number of unique words in the collection: ", unique_words)
    
    query = input("\nPlease enter your query: \n")
    query = query.lower()
    querySet = query.split(" ")
    result = ' '
    #print(querySet)
    frequencyListSmall = []
    for word in querySet:
        if word in wordList:
            for x in range(len(wordList)):
                if wordList[x] == word:
                    frequencyListSmall.append(frequencyList[x])
    #print(frequencyListSmall)
    if len(frequencyListSmall) != 0:
        intersect = set(frequencyListSmall[0]).intersection(*frequencyListSmall)
        relevent = list(intersect)
        for x in range(len(relevent)):
            if x == len(relevent)-1:
                result += relevent[x]
            else:
                result += relevent[x] +', '
        print ("Relevent results are: " + result)
    else: 
        print("No relevent documents are available.")


    report.append(urlList)
    report.append(outlinkCount)
    save_htmls(file_path, file_num, allSoup)
    save_files(file_path,file_num,crawledWords,soup,urlList, outlinkCount)


#detects if the html string is in either Korean or Non-Korean language.
#Counts the 100 most frequent words, total words in the collection, and the number of unique words and returns them.
def language_processing(soupString):
    #print(soupString)
    #@TODO: I feel like this is repeated somewhere 
    if detect(soupString) != "ko": 
        #@AttemptHere~~
        #soupString = (''.join([x for x in soupString if x in string.ascii_letters + '\'- ']))
        #zipf = soupString.lower().split()
        zipf=collect_words(soupString)
        countTrue = Counter(soupString.lower().split())
        words_in_corpus = len(soupString)       #Total words in the collection
        unique_words = len(countTrue)           #Vocabulary size (number of unique words)
        crawledWords = (countTrue.most_common(100))
        zipfs_law(zipf)                    #Pass total words to zipf's method
    #process korean words    
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
    plt.xticks(rotation = 90)
    
    for word, freq in collection[:30]:
        plt.bar(word,freq)
    plt.show()
    
def crawl_domain(mainURL,crawled, wordList, frequencyList):
    
    #response = requests.get(mainURL, verify = False)
    #creates session for requests so parameters persist 
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    response = session.get(mainURL)

    #take text of response and parse it 
    html = response.text
    soup = BeautifulSoup(html, 'lxml')   # Request html from the url and use Beautifulsoup to parse
    soupMainText = soup.get_text()

    currentMainSoup = soupMainText
    currentMainText = ''
    #@TODO: this is repeated for english processing of soup 
    if detect(currentMainSoup) != "ko":
        #@AttemptHere~~~~
        #currentMainSoup = (''.join([x for x in currentMainSoup if x in string.ascii_letters + '\'- ']))
        #currentMainText = currentMainSoup.lower().split()
        currentMainText=collect_words(currentMainSoup)
    else: 
        okt1 = Okt()
        currentMainText = okt1.nouns(currentMainSoup)
    
    newMainWordList = wordList 
    newMainFrequencyList = frequencyList 

    for word in currentMainText:
        if word not in wordList:
            newMainWordList.append(word)
            newMainFrequencyList.append(["doc 1"])
        if word in wordList:
            for x in range(len(newMainWordList)):
                if "doc 1" not in frequencyList[x]:
                    if word == newMainWordList[x]:
                        newMainFrequencyList[x].append("doc 1")

    for script in soup(["script", "style"]):    # Get rid of javascript and css from the html
        script.decompose()
    #go through html and pull out outlinks
    outlinks = []           
    outlinksCounter = 0               
    for append_url in soup.find_all('a', href= True):
        append_url = append_url.get('href')
        append_url = urljoin(mainURL, append_url)
        if append_url == mainURL:
            pass
        elif 'javascript:void' in append_url:
            pass
        else:
            outlinks.append(append_url)  
            outlinksCounter += 1
        """
        else:
            if "javascript:void(0)" == append_url:
                pass
            elif "javascript:void(0);" == append_url:
                pass
            else:
                outlinks.append(append_url)  
                outlinksCounter += 1
        """

        """
        
        """
        #@TODO: can these be condensed into a contains? 
        """
        
        """
    crawled.append(mainURL)
    #print(outlinks)

    return soup, outlinks, crawled, newMainWordList, newMainFrequencyList

def getDisallowed(mainURL, pageVisting):
    robots = urllib.robotparser.RobotFileParser()
    robotsURL = mainURL + "/robots.txt"
    robots.set_url(robotsURL)
    robots.read()
    check = robots.can_fetch("*", pageVisting)
    return check 

def goCrawl(mainURL, url, crawled, wordList, frequencyList, counter):
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
    
    currentSoup = soupText
    currentText = ''
    #@TODO: this is the third reptition of this block
    if detect(currentSoup) != "ko":
        #@AttemptHere~~~~
        #currentSoup = (''.join([x for x in currentSoup if x in string.ascii_letters + '\'- ']))
        #currentText = currentSoup.lower().split()
        currentText =collect_words(currentSoup)
    else:
        okt2 = Okt()                             
        currentText = okt2.nouns(currentSoup)


    newWordList = wordList
    newFrequencyList = frequencyList

    for word in currentText:
        if word not in wordList:
            newWordList.append(word)
            newFrequencyList.append(["doc " + str(counter + 2)])
        if word in wordList:
            for x in range(len(newWordList)):
                if "doc " + str(counter + 2) not in frequencyList[x]:
                    if word == newWordList[x]:
                        newFrequencyList[x].append("doc " + str(counter + 2))
               

    for script in thisSoup(["script", "style"]):
        script.decompose()
    #@TODO: this is also outlinks-- rep 1 
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

    return thisCounter, url, thisSoup, validOutlinks, soupText, newWordList, newFrequencyList 


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
def collect_words(soup):
    #function collects all of the words in soup and returns a string of only them and a few accepted characters
    soupString = (''.join([x for x in soup if x in string.ascii_letters + '\'- ']))
    revised_soup_string = soupString.lower().split()
    return revised_soup_string

if __name__ == "__main__":
    main()