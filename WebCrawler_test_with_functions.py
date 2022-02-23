import os
import requests
import re
from langdetect import detect
from bs4 import BeautifulSoup
from konlpy.tag import Okt
from collections import Counter
from string import punctuation
from urllib.parse import urljoin
from urllib.request import urlopen

def crawl_domain():
    options = ["https://www.cau.ac.kr","https://www.ipn.mx/","https://www.devry.edu/"]
    print("Which url would you like to crawl")
    count=0

    for each in options: 
        print(count, " ",each)
        count = count + 1
    
    num = int(input())
    file_num = num + 1
    url = options[num]
    file_path = input("Please enter the file path that you would like to use: ")
    response = requests.get(url, verify = False)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')   # Request html from the url and use Beautifulsoup to parse

    for script in soup(["script", "style"]):    # Get rid of javascript and css from the html
        script.decompose()

    outlinks = []                          
    for append_url in soup.find_all('a', href= True):
        append_url = append_url.get('href')
        append_url = urljoin(url, append_url)
        outlinks.append(append_url)  

    return file_num, file_path, soup, url

def get_disallowed(soup, url):
    #robotsDUrl = "https://www.devry.edu/robots.txt"
    #robotsDUrl = url + "/robots.txt"
    response = requests.get(url, verify = False)
    html2 = response.text
    soup2 = BeautifulSoup(html2, 'lxml')

    for script in soup(["script", "style"]):
        script.decompse()
    
    robot = (soup2.get_text())
    robots = re.split( ':|\n', robot)
    dont_need = ['Disallow', ' *','# FOR ALL OTHER USER AGENTS','User-agent', '',
    '# BLOCKED AGENTS', ' Zing-BottaBot*', ' /', '# SITEMAP LOCATION', 'Sitemap', 
    ' https', '//www.devry.edu/sitemap.xml']
    for word in list(robots):
        if word in dont_need:
            robots.remove(word)

    #print(robots)
    #print(type(rs))
    #print(type(soup2))
    #print(soup2.prettify)

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

def save_files(file_path, file_num, words_list, soup):
    filename_words = f"{file_path}/repository/words{file_num}.csv"
    filename_html = f"{file_path}/repository/html_output{file_num}.html"

    os.makedirs(os.path.dirname(filename_html), exist_ok=True)
    with open(filename_html, "w") as file:
        file.write(str(soup))

    os.makedirs(os.path.dirname(filename_words), exist_ok=True)     # Create a folder named repository and save files
    with open(filename_words, 'w', encoding = "utf-8-sig") as file:
        for noun, number in words_list:
            file.write("{}, {}\n".format(noun, number))

def main():
    file_num, file_path, soup, url = crawl_domain()
    get_disallowed(soup, url)
    words_list = check_language(soup)
    save_files(file_path, file_num, words_list, soup)
    
if __name__ == "__main__":
    main()