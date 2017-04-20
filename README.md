# crawler-webpage
## Set up
- install scrapy:
  * run Anaconda Prompt as Administrator
  * run: pip install scrapy
## Run
- run: scrapy crawl <crawler_name> --set HTTPCACHE_ENABLED=False
  * crawler_name = links: get all links of different topics in 2016. Results are stored in XXXX.txt
  * crawler_name = news: extract data of news for each link and store in folder "XXXX" which is the number of topic.
  
