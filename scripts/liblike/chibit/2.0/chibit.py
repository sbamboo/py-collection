# Chibit Module 2.0 Preview made by Simon Kalmi Claesson
#
# Modules for interacting with a chibit-store
#

# Imports
import requests, zlib, os

def download_file(url, output, *args, **kwargs):
    response = requests.get(url, *args, **kwargs)
    response.raise_for_status()  # Raise an error for bad status codes
    with open(output, 'wb') as file:
        file.write(response.content)
    print(f"File downloaded successfully to {output}")

# Main class
class ChibitConnector():
    def __init__(self, host_url, fetcher=requests.get, downloader=download_file, fetcherKwargs={}, downloaderKwargs={}):
        """
        ChibitConnector is a class for interacting with a chibit-store.
        
        Parameters:
        -----------
        host_url          (str) : The URl to the chibit-store.
        fetcher      (callable) : The function used to fetch data. (Will be sent the 'url' argument)
        downloader   (callable) : The function used to download files. (Will be sent the 'url' and 'output' arguments)
        fetcherKwargs    (dict) : The keyword arguments that will get sent to the fetcher function. (Look at the function deffintions to what kwargs to send)
        downloaderKwargs (dict) : The keyword arguments that will get sent to the downloader function. (Look at the function deffintions to what kwargs to send)
        """