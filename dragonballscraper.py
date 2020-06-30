from bs4 import BeautifulSoup
import requests
import shutil
import os
import re

base_url = 'http://comic.dragonballcn.com/'
volumes_url = 'http://comic.dragonballcn.com/dragonball_jp_kanzenban.htm'

# get list of volume links
page = requests.get(volumes_url)
soup = BeautifulSoup(page.content, 'html.parser')

soup = soup.find_all('div', id='hdnavli4')
soup = [s.find_all('a', href=True) for s in soup]
volume_links = [vl['href'] for s in soup for vl in s]
volume_links = [base_url + vl for vl in volume_links]

re_vol_num = re.compile(r'did=\w-\w-([0-9]+)')
re_page_num = re.compile(r'DRAGONBALLvol[\w]+/([0-9\-]+)-[\w]+\.jpg')

def scrape_images(volume_links, http_fails=None):
	if http_fails is None:
		http_fails = []

	dir_path = 'data/{}'
	
	# for each volume link download all pages within
	for vl in volume_links:
		# build list of page links
		page = requests.get(vl)
		soup = BeautifulSoup(page.content, 'html.parser')	
		
		# find the links to the thumbnails
		soup = soup.find_all('li', class_='ItemThumb')
		page_links = [s.find('img')['src'] for s in soup]
		
		# get link to full image from thumbnail
		page_links = [pg.replace('_thumb.', '') for pg in page_links]
		
		# download each into the appropriate folder
		vol_num = re_vol_num.search(vl).group(1)
		
		path = dir_path.format(vol_num)
		if not os.path.exists(path):
			os.mkdir(path)
	
		for pl in page_links:
			# get the image
			try:
				page = requests.get(pl, stream=True)	
				# get page number
				page_num = re_page_num.search(pl).group(1)
			
				
				if page.status_code == 200:
					print(f"Writing {vl}, {page_num}")
			
					img_path = path + '/' + page_num + '.jpg'
					with open(img_path, 'wb') as file:
						page.raw.decode_content = True
						shutil.copyfileobj(page.raw, file)
						
			except:
				print(f"FAILED: {vl}, {pl}")
				http_fails.append((vl, pl))
							
	return http_fails

def clear_fails(http_fails, dir_path = 'data/{}'):
	new_http_fails = []
	
	for vl, pl in http_fails:
		vol_num = re_vol_num.search(vl).group(1)
		page_num = re_page_num.search(pl).group(1)
		path = dir_path.format(vol_num)
		
		try:
			page = requests.get(pl, stream=True)
	
			if page.status_code == 200:
				print(f"Writing {vl}, {page_num}")
		
				img_path = path + '/' + page_num + '.jpg'
				with open(img_path, 'wb') as file:
					page.raw.decode_content = True
					shutil.copyfileobj(page.raw, file)
					
		except:
			print(f"FAILED: {vl}, {pl}")
			new_http_fails.append((vl, pl))
			
	if len(new_http_fails) > 0:
		clear_fails(new_http_fails)
	
	
http_fails = scrape_images(volume_links)

#with open('fails.txt', 'w') as f:
#	for fail in http_fails:
#		vl, pl = *fail
#		f.write(f'({vl}, {pl})\n')
		
clear_fails(http_fails)
		
