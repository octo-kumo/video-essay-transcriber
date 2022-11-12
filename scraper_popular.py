import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

channel=sys.argv[1]

driver=webdriver.Firefox()
driver.get("https://www.youtube.com/c/"+channel+"/videos")
driver.find_element(By.XPATH,"//*[@title=\"Popular\"]").click()

elems=driver.find_elements(By.ID,"thumbnail")

f=open("video_links/"+channel+".txt","x")

for i in elems:
	html=i.get_attribute("outerHTML")
	idx=html.find("watch")
	if (idx!=-1):
		f.write(html[idx+8:idx+19])
		f.write("\n")
		
f.close()
