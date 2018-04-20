# crawler-webpage
Introduction how to use scrapy package
There are 3 crawlers using **scrapy** including: batdongsan, vnexpress and icd9

## Set up
1. install scrapy:
    * run Anaconda Prompt as Administrator
    ```
    $ pip install scrapy
    ```
2. generate scrapy project:
    ```
    $ scrapy startproject <project_name>
    ```
    
## Run
1. list all crawler in project:
    * under the crawler directory(for example, the current position is **crawler-webpage\batdongsan_crawler**), open command line/terminal: 
    ```
    $ scrapy list
    # list of crawler_name will be displayed
    ```

2. run: 
    ```
    scrapy crawl <crawler_name> --set HTTPCACHE_ENABLED=False
    ```
    * crawler_name = links: get all links of different topics in 2016. Results are stored in XXXX.txt
    * crawler_name = news: extract data of news for each link and store in folder "XXXX" which is the number of topic.
  