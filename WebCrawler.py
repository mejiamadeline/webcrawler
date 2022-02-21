# -*- coding:utf-8 -*-
import os
import requests
from langdetect import detect
from bs4 import BeautifulSoup
from collections import Counter
import re

url = "https://www.cau.ac.kr/"
#url = "https://www.jornada.com.mx/"
#url = "https://www.devry.edu/"

response = requests.get(url, verify = False)
html = response.text
soup = BeautifulSoup(html, 'lxml')   # Request html from the url and use Beautifulsoup, lxml is more robust parser than html.parse and get rid of html tags for lang

for script in soup(["script", "style"]):    # Get rid of javascript and css from the html
    script.decompose()

soup_string = str(soup.text)                 # Convert the html into string
soup_string = soup_string.replace('\n', ' ')
soup_string = re.sub(" \d+", '', soup_string)

print(soup_string)
print("The URL is in the following language: ", detect(soup.text)) #gets text context of html file

count_words = Counter(word for word in soup_string.strip().split(" ") if len(word) > 1 or word is ('a' or 'I'))      
words_list = count_words.most_common(100)   # Count the 100 most frequent words
print(words_list)

filename_words = "C:/users/semav/repository/words.csv"
filename_html = "C:/users/semav/repository/html_output.txt"

os.makedirs(os.path.dirname(filename_words), exist_ok=True)     # Create a folder named repository and save files
with open(filename_words, 'w', encoding = "utf-8-sig") as file:
    for noun, number in words_list:
        file.write( "{}, {}\n".format(noun, number) )

os.makedirs(os.path.dirname(filename_html), exist_ok=True)
with open(filename_html, "w") as file:
    file.write(str(soup))

