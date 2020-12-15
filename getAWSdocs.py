#!/usr/bin/env python3

from bs4 import BeautifulSoup
import os
import argparse
from urllib.parse import urlparse, urlsplit
from urllib.request import urlopen
import json


def get_options():
    parser = argparse.ArgumentParser(
        description='AWS Documentation Downloader')
    parser.add_argument('-d', '--documentation',
                        help='Download the Documentation', action='store_true', required=False)
    parser.add_argument('-w', '--whitepapers', help='Download White Papers',
                        action='store_true', required=False)
    parser.add_argument('-b', '--builderlibrary', help='Download Documents in Builder Library',
                        action='store_true', required=False)
    parser.add_argument('-f', '--force', help='Overwrite old files',
                        action='store_true', required=False)
    args = vars(parser.parse_args())
    return (args)

# Build a list of the amazon PDF's
# update based on new Whitepaper page - DEC. 2019
def list_whitepaper_pdfs():
    # Max paging in json response for whitepaper
    PAGE_SIZE_CONST = 15
    # Parse the JSON Response
    responseAsJson = json.loads(urlopen(
           "https://aws.amazon.com/api/dirs/items/search?item.directoryId=whitepapers&sort_by=item.additionalFields.sortDate&sort_order=desc&size="+str(PAGE_SIZE_CONST)+"&item.locale=en_US&tags.id=GLOBAL%23content-type%23whitepaper").read().decode('UTF-8'))
    # Retreiving metadata json to get the lenght of the witepapers list metadata.count
    maxNumberofDocuments = responseAsJson['metadata']['totalHits']
    print("Number of Whitepapers to be retrieved: " + str(maxNumberofDocuments))
    maxPage = maxNumberofDocuments // PAGE_SIZE_CONST + 1
    print("Number of iterations :"+ str(maxPage))
    pdfs = set()
    currentPage = 0
    print("Generating PDF list (this may take some time)")
    while currentPage < maxPage:
      responseAsJson = json.loads(urlopen(
        "https://aws.amazon.com/api/dirs/items/search?item.directoryId=whitepapers&sort_by=item.additionalFields.sortDate&sort_order=desc&size="+str(PAGE_SIZE_CONST)+"&item.locale=en_US&tags.id=GLOBAL%23content-type%23whitepaper&page="+str(currentPage)).read().decode('UTF-8'))
      for item in responseAsJson['items']:
        print("URL to be added to pdf list: "+item['item']['additionalFields']['primaryURL'])
        pdfs.add(item['item']['additionalFields']['primaryURL'])
      currentPage += 1    
    return pdfs

# Build a list of the amazon builder library PDF's
def list_builderlibrary_pdfs():
    # Max paging in json response for builderlib whitepaper
    PAGE_SIZE_CONST = 15
    # Parse the JSON Response
    responseAsJson = json.loads(urlopen(
        "https://aws.amazon.com/api/dirs/items/search?item.directoryId=amazon-redwood&sort_by=item.additionalFields.customSort&sort_order=asc&size="+str(PAGE_SIZE_CONST)+"&item.locale=en_US").read().decode('UTF-8'))
    # Retreiving metadata json to get the length of the witepapers list metadata.count
    maxNumberofDocuments = responseAsJson['metadata']['totalHits']
    print("Number of builderlib papers to be retrieved: " + str(maxNumberofDocuments))
    maxPage = maxNumberofDocuments // PAGE_SIZE_CONST + 1
    print("Number of iterations :"+ str(maxPage))
    pdfs = set()
    currentPage = 0
    print("Generating PDF list (this may take some time)")
    while currentPage < maxPage:
      responseAsJson = json.loads(urlopen(
        "https://aws.amazon.com/api/dirs/items/search?item.directoryId=amazon-redwood&sort_by=item.additionalFields.customSort&sort_order=asc&size="+str(PAGE_SIZE_CONST)+"&item.locale=en_US&page="+str(currentPage)).read().decode('UTF-8'))
      for item in responseAsJson['items']:
        print("URL to be added to pdf list: "+item['item']['additionalFields']['downloadUrl'])
        try:
            downloadUrl=item['item']['additionalFields']['downloadUrl']
        except KeyError:
            print("Document with no downloadUrl")
        pdfs.add(downloadUrl)
        currentPage += 1
    return pdfs

def find_pdfs_in_html(url):
    html_page_doc = urlopen(url)
    soup_doc = BeautifulSoup(html_page_doc, 'html.parser')
    # Get the A tag from the parsed page
    pdfs = set()
    for link in soup_doc.findAll('a'):
        try:
            sub_url = link.get('href')
            if sub_url.endswith("pdf"):
                pdfs.add(sub_url)
        except:
            continue
    return pdfs


def list_docs_pdfs(start_page):
    locale_path = "en_us/"
    base_url = "http://docs.aws.amazon.com"

    page = urlopen(start_page)
    soup = BeautifulSoup(page, "xml")
    pdfs = set()
    print("Generating PDF list (this may take some time)")

    for link in soup.findAll('service'):
        try:
            uri = link.get('href')
            print('URI: ', uri)
            # if service uri is .html then parse as HTML
            if '.html' in uri:
                url = base_url + uri
                pdfs = pdfs.union(find_pdfs_in_html(url))
                continue

            # if service uri ends with "/" find and parse xml landing page
            if not uri.startswith('http'):
                url = base_url + \
                    uri.split("?")[0] + locale_path + "landing-page.xml"

            # Fetch the XML sub page (this is where the links to the pdf's live)
            sub_page_doc = urlopen(url)
            soup_doc = BeautifulSoup(sub_page_doc, 'xml')

            # Get the "tile" tag from the parsed page
            for sublink in soup_doc.findAll('tile'):
                try:
                    sub_url = sublink.get('href')
                    directory = base_url + \
                        "/".join(urlsplit(sub_url).path.split('/')[:-1])

                    guide_info_url = directory + "/meta-inf/guide-info.json"
                    print("Guide info url:", guide_info_url)
                    guide_info_doc = urlopen(guide_info_url).read()
                    guide_info = json.loads(guide_info_doc)

                    if "pdf" in guide_info:
                        pdf_url = directory + "/" + guide_info["pdf"]
                        pdfs.add(pdf_url)
                except:
                    continue
        except:
            continue
    return pdfs


def save_pdf(full_dir, filename, i):
    if not os.path.exists(full_dir):
        os.makedirs(full_dir)
    # Open the URL and retrieve data
    file_loc = full_dir + filename
    if not os.path.exists(file_loc) or force == True:
        if i.startswith("//"):
            i = "http:" + i
        print("Downloading : " + i)
        web = urlopen(i)
        print("Saving to : " + file_loc)
        # Save Data to disk
        output = open(file_loc, 'wb')
        output.write(web.read())
        output.close()
    else:
        print("Skipping " + i + " - file exists or is a dated API document, use './getAWSdocs.py --force' to force override")


def get_pdfs(pdf_list, force):
    for i in pdf_list:
        doc = i.split('/')
        doc_location = doc[3]
        filename = urlsplit(i).path.split('/')[-1]
        # Set download dir for whitepapers
        if "whitepapers" in doc_location:
            full_dir = "whitepapers/"
        if "builderslibrary" in doc_location:
            full_dir = "builderslibrary/"
        else:
            # Set download dir and sub directories for documentation
            full_dir = "documentation/"
            directory = urlsplit(i).path.split('/')[:-1]
            for path in directory:
                if path != "":
                    full_dir = full_dir + path + "/"
        try:
            save_pdf(full_dir, filename, i)
        except:
            continue


# Main
args = get_options()
pdf_list = set()
# allow user to overwrite files
force = args['force']
if args['documentation']:
    print("Downloading Docs")
    pdf_list = list_docs_pdfs(
        "https://docs.aws.amazon.com/en_us/main-landing-page.xml")
    get_pdfs(pdf_list, force)

if args['whitepapers']:
    print("Downloading Whitepapers")
    pdf_list = list_whitepaper_pdfs()
    get_pdfs(pdf_list, force)
if args['builderlibrary']:
    print("Downloading Builder Lib documents")
    pdf_list = list_builderlibrary_pdfs()
    get_pdfs(pdf_list, force)
for p in pdf_list:
    print(p)
