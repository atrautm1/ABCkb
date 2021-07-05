#!/usr/bin/env python

import concurrent.futures
import json
import logging
from os import path, getcwd, makedirs, environ
from urllib.parse import urlparse
from urllib.request import urlretrieve, urlcleanup
import requests
import shutil
import argparse

def check_directory(directory):
    "Checks if a directory exists, and if not, makes one"
    if not path.exists(directory):
        makedirs(directory)

def readArgs():
    """Reads the arguments provided by the user."""
    desc = """
    This program parses through source data and formats it
    for use in a neo4j Knowledgebase
    """
    p = argparse.ArgumentParser(description=desc, prog="download_sources.py")
    # Required arguments
    p.add_argument("-o", "--outdir", required=True, 
                   help="Specifies the directory where the data is written.")
    # Optional arguments
    p.add_argument("-v", "--verbose", default=False, help="Output verbose", action="store_true")
    args = p.parse_args()
    return args

def retrieve(url, path_and_file):
    # Get url data
    # try:
    response = requests.get(url, stream=True)
    # Raise an error if status error
    response.raise_for_status()
    with open(path_and_file,"wb") as outfile:
        for block in response: #.iter_content(1024):
            outfile.write(block)

def runner(source):
    "Download a file from a url into a directory"
    # Get the base file name
    url = source[0]
    directory = source[1]
    p = urlparse(url)
    file_name = path.basename(p.path)
    # Concatenate patha and file name

    path_and_file_name = path.join(directory, file_name)
    # Download file if not already exists
    # If you are getting errors of incomplete data, try reducing the number of max_workers
    try:
        if not path.exists(path_and_file_name):
            if url.startswith("ftp"):
                urlcleanup()
                urlretrieve(url, path_and_file_name)
            else:
                retrieve(url,path_and_file_name)
            logging.info(path_and_file_name)
        if path_and_file_name.endswith(".tar.gz"):
            shutil.unpack_archive(path_and_file_name, directory)
            logger.info(f"Unpacked: {path_and_file_name}")
    except Exception as e:
        logger.error(f"Problem with {file_name}.. You may need to manually download from: {url}")
        logger.error(e)

def main():
    args = readArgs()
    urls = []
    # Get current location
    LOCATION = path.realpath(path.join(getcwd(), path.dirname(__file__)))

    # Download directory
    DATA_DIR = path.join(args.outdir)
    # Ensure source_data directory exists
    check_directory(DATA_DIR)

    # Read sources.json file
    with open(path.join(LOCATION, "sources.json"), "r") as json_file:
        # Load the json data
        SOURCES = json.load(json_file)
        # Iterate through sources
        for source in SOURCES:
            # Where each source will go, 'source name + date'
            source_directory = path.join(DATA_DIR, source["name"])
            # Ensure directory exists
            check_directory(source_directory)
            # Iterate through files and download if not exists
            for data_file in source["files"]:
                # Set url for the file
                url = source["baseURL"]+data_file
                urls.append((url, source_directory))
                
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(runner, urls)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(asctime)s [%(funcName)s] %(levelname)s - %(message)s', 
                        datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    main()
