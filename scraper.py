import os

from pytube import YouTube

def scrape(link,folder):
	yt=YouTube("https://www.youtube.com/watch?v="+link)
	if (not "itag=\"18\"" in str(yt.streams)):
		return False
	yt.streams.get_by_itag(18).download(output_path=folder,filename=link+".mp4")
	return True

for channel in os.listdir("video_links"):
	f=open("video_links/"+channel,"r")
	if (not os.path.exists("videos/"+channel[:-4])):
		os.makedirs("videos/"+channel[:-4])
	for i in range(10):
		link=f.readline()
		print(channel,link)
		if (not os.path.exists("videos/"+channel[:-4]+"/"+link+".mp4")):
			scrape(link,"videos/"+channel[:-4])
