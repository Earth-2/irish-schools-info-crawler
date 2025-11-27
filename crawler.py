
#	Web scraper to collect school info from Irish government database
#	Keegan Covey, May 2024

import os						# for checking if file exists
import csv						# for writing to csv files
import requests					# for following URL links
from bs4 import BeautifulSoup	# for parsing HTML

# Globally accessible list of lists of school info (this will go directly into csv)
schools = []

# recursive function, crawls page by page, parses ugly table and puts data into schools[]
def GetPage(url, page):
	timeout = 3
	while True:		# keeps looping until it successfully parses or encounters an error
		try:
			html = requests.get(url).content
		except requests.exceptions.ConnectionError as e:
			print("Connection error encountered on page", page, "; max retries reached")
		except requests.exceptions.Timeout as e:
			print("Timeout encountered on page", page, "; trying again...")
			if timeout:
				timeout -= 1
				continue
			else:
				raise systemExit(e)
		except requests.exceptions.TooManyRedirects:
			print("Bad url on page ", page)
		except requests.exceptions.RequestException as e:
			raise SystemExit(e)

		data = BeautifulSoup(html, 'html.parser')	# parse html--then try and dive into structure and get data
		try:
			school_list = data.find('body').select_one("div:nth-of-type(6)").find_next("div").select_one("div:nth-of-type(2)").find_next("div").find_next("div").find_next("ul")
		except:
			print("Bad formatting encountered on page", page, "; trying again...")	# still not sure why this happens
		else:
			break	# parse successful; break out of loop and keep going

	for school in school_list:	# split each table item into a list
		if len(school) > 1:
			school_info = school.get_text(strip=True, separator=",").split(',')
			if school_info is not None:
				school_info = [i.strip() for i in school_info]		# strip out all the whitespace from each element
				school_info = school_info[:1] + school_info[-4:]	# keep only the relevant data especially since there's stray commas and stuff that mess this up otherwise
				schools.append(school_info)
				
	print("Page", page, "finished")
	
	next = data.find('a', attrs={"aria-label": "next"})	# iterate to next page
	if next is not None:
		page += 1
		next_url = "https://www.gov.ie"+next['href']
		GetPage(next_url, page)
	
	
####################
#    START MAIN    #
####################

# start_page should now always be 1, can be changed if the scraping quits halfway for some reason and want to keep adding rows to csv at later point
start_page = 1
start_url = "https://www.gov.ie/en/directory/category/495b8a-schools/?school_roll_number=&school_level=POST+PRIMARY&school_level=PRIMARY&page=" + str(start_page)
print("Crawling school list...")
GetPage(start_url, start_page)

print("Writing to .csv...")
file_name = 'zoe_schools.csv'

if os.path.exists(file_name):						# Probably could be changed to check for existing rows; or even better to do that check before the crawl
	print(file_name, "exists; appending rows")
	file = open(file_name, 'a+', newline = '')
	with file:
		write = csv.writer(file)
		write.writerows(schools)
else:												# File does not exist, start from scratch
	print("Creating", file_name)
	file = open(file_name, 'w', newline = '')
	with file:
		header = ['School', 'County','Eircode', 'Phone', 'E-mail']
		writer = csv.DictWriter(file, fieldnames = header)
		writer.writeheader()
		for school in schools:
			writer.writerow(dict(zip(header,school)))
