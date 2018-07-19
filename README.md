# crawler-webpage
Introduction how to use scrapy package
There are 3 crawlers using **scrapy** including: batdongsan, vnexpress and icd9

## Set up
1. install scrapy: run Anaconda Prompt as Administrator
    ```
    $ pip install scrapy
    ```
2. generate scrapy project:
    ```
    $ scrapy startproject <project_name>
    ```
    
## Run
1. List all crawlers in project:
    * under the crawler directory (for example, the current position is **crawler-webpage\batdongsan_crawler**), open command line/terminal: 
    ```
    $ scrapy list
    # list of crawler_name will be displayed
    ```

2. Run:
    * under the crawler directory (for example, the current position is **crawler-webpage\batdongsan_crawler**), open command line/terminal: 
    
    ```
    scrapy crawl <crawler_name> --set HTTPCACHE_ENABLED=False
    ```

    * ```crawler_name = links```: get all links of different topics in 2016. Results are stored in XXXX.txt
    * ```crawler_name = news```: extract data of news for each link and store in folder "XXXX" which is the number of topic.
    
3. Issues:
    - If scrapy returns "404", try to config "USER_AGENT" in **settings.py** like this ```USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'```
    - In order to do "something" **before the spider closing**, we first override ```from_crawler``` method to define what function will be called for a specific signal (see **tiki_crawler** for example and this link [scrapy signals](https://doc.scrapy.org/en/latest/topics/signals.html))
    - As you are accessing an API you most probably want to disable the duplicate filter altogether:
        ```
        DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'
        ```
        This way you don't have to clutter all your Request creation code with dont_filter=True (put in Request).
        ```
        PR = Request(
            'htp://my-api',
            headers=self.headers,
            meta={'newrequest': Request(random_form_page,  headers=self.headers)},
            callback=self.parse_PR,
            dont_filter = True
        )
        ```

    - when a page is rendered by calling javascript function (after ajax call done, for example), I use selenium [web-scraping-javascript-page-with-python](https://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python)
        + use requests-HTML(This solution is for Python's version 3.6 only (at the moment) (ERROR)

        ```
        sudo add-apt-repository ppa:jonathonf/python-3.6
        sudo apt-get update
        sudo apt-get install python3.6
        
        sudo python3.6 -m pip install requests-html
        sudo python3.6 lazada_product2.py
        ```

        + use SplashRequest: [how to use Scrapy to crawl javascript generated content](http://www.scrapingauthority.com/scrapy-javascript)
        
        ```
        sudo apt install docker.io
        sudo docker pull scrapinghub/splash
        sudo docker run -p 8050:8050 scrapinghub/splash

        sudo apt install python-scrapy
        sudo pip install scrapy-splash
        ```
        Note: CANNOT install docker.io. TRY LATER!!!

## Crawler Description
### 1. vnexpress
TODO...

### 2. facebook
TODO...

### 3. icd9
TODO...

### 4. truyenfull
TODO...
this crawler based on site map and url pattern

### 5. ecommerce_crawler
* Crawl information about products of a specific category: url, properties, introduction and all comments from some websites. Each website will be handled seperately (by different crawler)
* Run: 

    ```
    cd crawler-webpage/ecommerce_crawler
    scrapy crawl tiki_prod_links --set HTTPCACHE_ENABLED=False
    scrapy crawl tiki_comments --set HTTPCACHE_ENABLED=False
    ```
* Different kind of request/response:
    *   Tiki: 
        -  product: browse product by finding next page link, html response
        -  comment: GET API, JSON response
    *  VienthongA
        -  product links: incease pageid and put it in URL pattern
        -  product feature, description, comments: API, **XML response**
    *  Thegioididong:
        -  product links: POST API
        -  product description & feature: GET, html response
        -  product full feature: POST API, JSON response
    *  Lazada
    *  Dienmayxanh
* Output will be formatted as below:
    - **category-name_comments.csv**: comments of clients, including fields: ```product_id, comment_id, title, content, rating, thank_count```
    - **category-name_productlinks.csv**: links to products, including fields: ```product_id, product_link```
    - **category-name_products.csv**: information of products, including fields: ```product_id, top_features, features, content```.  
        -  Field ```top_features``` is formatted as *feature_1;feature_2;...*
        -  Field ```features``` is formatted as a dictionary of *feature:value*
            

