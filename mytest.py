from cmath import log
import os
from numpy import append
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry 
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
import networkx as nx
import math

G = nx.DiGraph()

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
    dl_List = []
    wordFrequencyList = []
    soup, outlinks, crawledOut, wordList, frequencyList, dl_List, wordFrequencyList = crawl_domain(mainURL,crawled, wordList, frequencyList, dl_List, wordFrequencyList)
    crawled = crawledOut
    print(dl_List)
 

    counter = 0
    urlList = []
    outlinkCount = []
    allSoup = []
    masterSoup = []
    soupString = ''
    
    for links in outlinks:
        if counter > 3:
            break
        thisCounter, url, thisSoup, validOutlinks, soupText, wordList, frequencyList, dl_List, wordFrequencyList = goCrawl(mainURL, links, crawled, wordList, frequencyList, counter, dl_List, wordFrequencyList) 

        allSoup.append(thisSoup)
        masterSoup.append(soupText)
        
        crawled.append(links)
        urlList.append(url)
        '''print(crawled)
        print(urlList)
        print (len(crawled))
        print(dl_List)'''

        outlinkCount.append(thisCounter)
        counter += 1

    '''for x in range(len(wordList)):
        print(wordList[x])      #check the words and which html/doc it appears in
        print(len(frequencyList[x]))'''

    for soup in masterSoup:
        soupString = soupString + soup
    
    words_in_corpus, unique_words, crawledWords = language_processing(soupString)

    print("The URL is in the following language: ", detect(soupString))
    print("Total words in the collection: ", words_in_corpus)
    print("Number of unique words in the collection: ", unique_words)

    query = input("\nPlease enter your query: \n")
    query = query.lower()
    querySet = query.split(" ")
    qf = []
    usedParts = []
    for parts in querySet:  
        qfTemp = 0
        if parts not in usedParts:
            for otherPart in querySet:
                if parts == otherPart:
                    qfTemp +=1
            qf.append(qfTemp)
            usedParts.append(parts)
    '''print(qf)
    print(usedParts)'''


    result = ' '
    N = len(crawled)
    totalWordCount = 0
    for number in dl_List:
        totalWordCount += number
    avdl = totalWordCount/N
    print(N)
    print(totalWordCount)
    print(avdl)
    querySet = usedParts
    print(querySet)
    frequencyListSmall = []
    n = []
    for word in querySet:
        if word in wordList:
            for x in range(len(wordList)):
                if wordList[x] == word:
                    frequencyListSmall.append(frequencyList[x])
                    n.append(len(frequencyList[x]))
        else:
            frequencyListSmall.append([]) 
            n.append(0)       
    '''print(frequencyListSmall)
    print(n)'''
    BM25_scores = []
    for doc in wordFrequencyList:
        totalScore = 0
        for section in range(len(querySet)):
            totalScore += BM25_formula(qf[section],N,n[section],doc[querySet[section]],dl_List[section],avdl)
        BM25_scores.append(totalScore)    
    print(BM25_scores)
        
    report.append(urlList)
    report.append(outlinkCount)

    #Implementing page rank, this sorts out the page rank score
    pr = nx.pagerank(G)
    pr = sorted(pr.items(),key=lambda v:(v[1],v[0]),reverse=True)

    print("Page rank: " + str(pr))

    save_htmls(file_path, file_num, allSoup)
    save_files(file_path,file_num,crawledWords,soup,urlList,outlinkCount,pr)

    G.remove_edges_from(nx.selfloop_edges(G))

    nx.draw(G, with_labels=False)
    plt.show()

    show_sub_graph(G, pr, float(0.0050))


def BM25_formula(qf, N, n, f, dl, avdl): 

    R = 0 #assume no relevance since we dont have anything to check relevance 
    b = 0.75 #from slides
    k1 = 1.2 #typical TREC value 
    r = 0  #assume no relevance since we dont have anything to check relevance 
    k2 = 100 #slide said varies from 0-1000 so just used 100 like the example

    a = 1-b #(1-b) part of the K formula
    c = dl/avdl #dl/avdl part of the K formula
    d = b*c #(b*dl/avdl) part of the K formula
    e = a + d #parathesis part of the K formula
    K = k1*e
    #print (K)
    topFirst = (r + 0.5)/(R-r+0.5)
    bottomFirst = (n-r+0.5)/(N-n-R+r+0.5)
    first = math.log(topFirst/bottomFirst)
    topSecond = (k1 + 1) * f
    bottomSecond = K + f
    second = topSecond/bottomSecond
    topLast = (k2 + 1) * qf
    bottomLast = (k2 + qf)
    last = topLast/bottomLast
    score = first * second * last
    return score
    
#Takes our graphs and returns a subgraph with less nodes
def show_sub_graph(G, pr, weight = 0.0):
    temp = G.copy(as_view = False)
    for index, tuple in enumerate(pr):
        if float(tuple[1]) < weight:
            temp.remove_node(tuple[0])
    
    nx.draw(temp, with_labels=True)
    plt.show()

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
    #process korean words    
    else:
        okt = Okt()                             
        korean_words = okt.nouns(soupString)    # From the converted string, extract only Korean nouns
        countTrue = Counter(korean_words)
        words_in_corpus = len(korean_words)       #Total words in the collection
        unique_words = len(countTrue)            #Vocabulary size (number of unique words)   
        crawledWords = countTrue.most_common(100) 
         

    return words_in_corpus, unique_words, crawledWords

    
def crawl_domain(mainURL,crawled, wordList, frequencyList, dl_List, wordFrequencyList):
    
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
    if detect(currentMainSoup) != "ko":  
        currentMainText = collect_words(currentMainSoup)
        mainNumberOfWords = len(currentMainText) # number of words in the domain page (dl)
        dl_List.append(mainNumberOfWords) #collect word count to get avgdl
        wordFrequencyList.append(Counter(currentMainText))
        
    else: 
        okt1 = Okt()
        currentMainText = okt1.nouns(currentMainSoup)
        mainNumberOfWords = len(currentMainText) # number of words in the domain page (dl)
        dl_List.append(mainNumberOfWords) #collect word count to get avgdl
        wordFrequencyList.append(Counter(currentMainText))
    
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
            #G.add_node(append_url)
            G.add_edge(append_url, mainURL)
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

    return soup, outlinks, crawled, newMainWordList, newMainFrequencyList, dl_List, wordFrequencyList

def getDisallowed(mainURL, pageVisting):
    robots = urllib.robotparser.RobotFileParser()
    robotsURL = mainURL + "/robots.txt"
    robots.set_url(robotsURL)
    robots.read()
    check = robots.can_fetch("*", pageVisting)
    return check 

def goCrawl(mainURL, url, crawled, wordList, frequencyList, counter, dl_List, wordFrequencyList):
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

    if detect(currentSoup) != "ko":
        currentText =collect_words(currentSoup)
        numberOfWords = len(currentText) # number of words in the domain page (dl)
        dl_List.append(numberOfWords) #collect word count to get avgdl
        wordFrequencyList.append(Counter(currentText))
    else:
        okt2 = Okt()                             
        currentText = okt2.nouns(currentSoup)
        numberOfWords = len(currentText) # number of words in the domain page (dl)
        dl_List.append(numberOfWords) #collect word count to get avgdl
        wordFrequencyList.append(Counter(currentText))


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
        

        #This checks if node exist
        if not G.has_node(url):
            G.add_edge(append_url, url)
        elif G.has_node(append_url):
            #If link exist, it will link the two nodes together
            if append_url in G[url]: 
                G.add_edge(url, append_url)
            else:
                G.add_edge(append_url, url)

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

    return thisCounter, url, thisSoup, validOutlinks, soupText, newWordList, newFrequencyList, dl_List, wordFrequencyList


# I made an if else statement that checks the language of the html.
# If it is not Korean, then count top 100 most frequent words without using the konply library
# If it is in Korean, then use the konlpy library and count top 100 most frequent words.

def save_files(file_path, file_num, words_list, soup, urlList, outlinkCount,pr):
    filename_words = f"{file_path}/repository/words{file_num}.csv"
    filename_html = f"{file_path}/repository/html_output{file_num}.html"
    filename_report = f"{file_path}/repository/report{file_num}.csv"
    filename_pagerank = f"{file_path}/repository/pagerank{file_num}.csv"

    os.makedirs(os.path.dirname(filename_html), exist_ok=True)
    with open(filename_html, "w", encoding="utf-8") as file:
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


