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

#url = ""
#url = ""
#url = ""
options = ["https://www.cau.ac.kr","https://www.ipn.mx/","https://www.devry.edu/"]
print("Which url would you like to crawl")
count=0

for each in options: 
    print(count, " ",each)
    count = count+1
num = int(input())
file_num = num+1
url = options[num]
file_path =input("Please enter the file path that you would like to use: ")
response = requests.get(url, verify = False)
html = response.text
soup = BeautifulSoup(html, 'lxml')   # Request html from the url and use lxml is a more robust parser

for script in soup(["script", "style"]):    # Get rid of javascript and css from the html
    script.decompose()

outlinks = []                          
for append_url in soup.find_all('a', href= True):
    append_url = append_url.get('href')
    append_url = urljoin(url, append_url)
    outlinks.append(append_url)                      # I was able to extract the links inside outlinks[], but can't figure out how to crawl each one of them.

def getDisallowed():
    #robotsDUrl = "https://www.devry.edu/robots.txt"
    robotsDUrl = url + "/robots.txt"
    html2 = urlopen(robotsDUrl).read()
    soup2 = BeautifulSoup(html2, 'html.parser')

    for script in soup(["script", "style"]):
        script.decompse()
    
    robot = (soup2.get_text())
    robots = re.split( ':|\n', robot)
    dontNeed = ['Disallow', ' *','# FOR ALL OTHER USER AGENTS','User-agent', '',
    '# BLOCKED AGENTS', ' Zing-BottaBot*', ' /', '# SITEMAP LOCATION', 'Sitemap', 
    ' https', '//www.devry.edu/sitemap.xml']
    for word in list(robots):
        if word in dontNeed:
            robots.remove(word)

    print(robots)
    #print(type(rs))
    #print(type(soup2))
    #print(soup2.prettify)

# I made an if else statement that checks the language of the html.
# If it is not Korean, then count top 100 most frequent words without using the konply library
# If it is in Korean, then use the konlpy library and count top 100 most frequent words.
text = soup.get_text()
if detect(text) != "ko":                            
    text = (''.join(s.findAll(text=True))for s in soup.findAll('p'))
    count_words = Counter((a.rstrip(punctuation).lower() for b in text for a in b.split()))
    words_list = (count_words.most_common(100))
else:
    soup_string = str(soup)                 # Convert the html into string
    okt = Okt()                             
    korean_noun = okt.nouns(soup_string)    # From the converted string, extract only Korean nouns
    count_words = Counter(korean_noun)      
    words_list = count_words.most_common(100)   # Count the 100 most frequent words
    
print("The URL is in the following language: ", detect(soup.text))  #Brought this outside because it was only being used in the else statement  

filename_words = f"{file_path}/repository/words{file_num}.csv"
filename_html = f"{file_path}/repository/html_output{file_num}.html"

os.makedirs(os.path.dirname(filename_html), exist_ok=True)
with open(filename_html, "w") as file:
    file.write(str(soup))

os.makedirs(os.path.dirname(filename_words), exist_ok=True)     # Create a folder named repository and save files
with open(filename_words, 'w', encoding = "utf-8-sig") as file:
    for noun, number in words_list:
        file.write( "{}, {}\n".format(noun, number) )

# This for loop iterates through all the links in the outlinks list and requests the html, but currently missing a feature to
# save the visited link's html to a new file, e.g. html_output(2).html for the second visited link, html_outout(3).html for the third link, ...
"""
for item in outlinks:
    outlink_response = requests.get(item, verify = False)
    outlink_html = outlink_response.text
    outlink_soup = BeautifulSoup(outlink_html, 'html.parser')
    for script in outlink_soup(['script', 'style']):
        script.decompose()
"""

def main():
    getDisallowed()
if __name__ == "__main__":
    main()





