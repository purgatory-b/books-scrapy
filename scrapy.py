import base64
import configparser
import io
import json
import ntpath
import random
import re
import sys
import time
import urllib.request
from datetime import datetime

import files
import loguru
import requests
import sqlalchemy
import sqlalchemy.ext.automap
import sqlalchemy.orm
import sqlalchemy.schema
from captcha_solver import CaptchaSolver
from lxml import etree
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

#全域變數
pageLinks = []
articles = []

def dl_jpg(url,file_name):
    urllib.request.urlretrieve(url, file_name)
    with open(file_name , "rb") as f:
        data = base64.b64encode(f.read())
    return data

def main():
    global pageLinks

    login()
    hasNext = search(keyword)
    while hasNext == True:
        hasNext = fetch_list()
        #fetch_detail()
        #insert_update_db()
     #排序連結
    pageLinks = sorted(pageLinks, key=lambda k: k['link']) 
    #去除重複的連結
    pageLinks = [dict(t) for t in {tuple(d.items()) for d in pageLinks}]
    #print(len(pageLinks))

    fetch_detail()
    #print(articles)
    #fetch_detail()
    #insert_update_db()
    #寫入資料庫
    create_db_scrapy()
    time.sleep(5)

    sys.exit('爬蟲結束')

#登入        
def login():
    #進入 books 登入頁面
    driver.get(config['books']['Login'])
    login_email = driver.find_element_by_name('login_id')
    login_pass = driver.find_element_by_name('login_pswd')
    captcha = driver.find_element_by_name('captcha')
    captcha_img = driver.find_element_by_id('captcha_img')
    login_button = driver.find_element_by_id('books_login')

    captcha_img.screenshot('captcha_image.png')

    raw_data = open('captcha_image.png', 'rb').read()
    captcha_code = solver.solve_captcha(raw_data)
    
    #填入帳密並送出
    time.sleep(random.randint(2000, 3000)/1000)
    login_email.send_keys(config['books']['Mail'])
    login_pass.send_keys(config['books']['Password'])
    captcha.send_keys(captcha_code)
    time.sleep(random.randint(2000, 3000)/1000)
    login_button.click()
    time.sleep(random.randint(2000, 3000)/1000)
    driver.find_element_by_xpath('//div[@class="flash_banner_pop"]/a[@class="close"]').click()
    time.sleep(random.randint(2000, 3000)/1000)
#搜尋
def search(keyword):
    search_input = driver.find_element_by_id('key')
    search_input.clear()
    search_input.send_keys(keyword)
    search_input = driver.find_element_by_xpath('//button[@type="submit"]').click()
    search_input = driver.find_element_by_xpath('//label[@class="container2"][2]//span').click()
    search_input = driver.find_element_by_xpath('//div[@class="btn-wrap clearfix"]//button[@id="adv_btn_confirm"]').click()
    time.sleep(3)
    search_input = driver.find_element_by_xpath('//form[@id="filter_cat_2"]//label[@class="container2"][1]//span').click()
    search_input = driver.find_element_by_xpath('//div[@class="btn-wrap clearfix"]//button[@id="adv_btn_confirm"]').click()
    time.sleep(6)
    return True
#取得列表
def fetch_list():
    print('fetch_list()')
    results = driver.find_element_by_id('itemlist_table').get_attribute('innerHTML')
    if results == None:
        sys.exit('程式中止：搜尋無回應')

    dom = etree.HTML(results)
    links = dom.xpath('//div[@class="box_1"]/a/@href')
    titles = dom.xpath('//div[@class="box_1"]/a/@title')
    composeItems(links, titles)

    #利用下一頁按鈕，判讀有無下一頁
    try:
        nextPage = driver.find_element_by_xpath('//ul[@class="page"]/li[5]').get_attribute('outerHTML')
        nextPageUrl = etree.HTML(nextPage)
        driver.get('https:'+nextPageUrl.xpath('//a/@href')[0])
        time.sleep(random.randint(1000, 3000)/1000)
    except :
        print('無下一頁')
        return False

    return True
#取得內容
def fetch_detail():
    count=0
    for pageLink in pageLinks:
        try:
            read = 'https:'+pageLink['link']
            print('讀取 >>> ' + read)
            driver.get(read)
            results = driver.find_element_by_xpath('//div[@class="grid_24 main_column"]').get_attribute('outerHTML')
            if results == None:
                print('忽略本頁：無回應指定內容元素')
                return
            dom = etree.HTML(results)
            parseDetail(pageLink, dom)

        except:
            print('內容頁面錯誤。')
        count+=1
        if(count%10==0):
            time.sleep(60)
        else:
            time.sleep(random.randint(1000, 3000)/1000)
title = []        
#組合列表中的標題
def composeItems(links, titles):
    global pageLinks
    for idx, link in enumerate(links):

        print(link)
        print(titles[idx])
        pageLinks.append({"title":titles[idx], "link":link})       
#解析內容頁
def parseDetail(pageLink, dom):
    global articles
    #ISBN
    ISBN = ''
    try:
        ISBN = dom.xpath('//div[@class="bd"]/ul[1]/li[1]/text()')[0].replace('ISBN：','')
        #print(ISBN)
    except:
        print('找不到：ISBN')
    #封面 cover 
    cover = ''
    image = ''
    try:
        cover = dom.xpath('//div[@class="mod cnt_prod_img001 nolazyload_img clearfix"]//div[@class="cnt_mod002 cover_img"]//img/@src')[0]
        #print(cover)
        url = cover
        file_name = "images/"+ISBN+".jpg"
        image = dl_jpg(url,file_name)

    except:
        print('找不到：封面')
    #作者 author
    author = 'None'
    authorLink = ''
    try:
        author = dom.xpath('//div[@class="grid_24 main_column"]//div[@class="type02_p003 clearfix"]//li[1]/a[1]/text()')[0]
        authorLink = dom.xpath('//div[@class="grid_24 main_column"]//div[@class="type02_p003 clearfix"]//li[1]/a[1]/@href')[0]
        authorLink = 'https:'+ authorLink
    except:
        print('找不到：作者')
    #譯者 translator
    translatorText = ''
    translatorUrl = ''
    translator = ''
    y='譯者'
    c = 0
    translatorText = dom.xpath('//div[@class="type02_p003 clearfix"]//li[2]/text()')[0]
    if( y not in translatorText):
        c = 1
    else:
        try:
            translatorUrl = dom.xpath('//div[@class="type02_p003 clearfix"]//li[2]/a[1]/@href')[0]
            translator = dom.xpath('//div[@class="type02_p003 clearfix"]//li[2]/a[1]/text()')[0]
            translatorUrl = 'https:' + translatorUrl
            #print(translator,translatorUrl)
        except:
            print('找不到：譯者')
    #出版社 publishingHouse
    publishingHouse = ""
    publishingHouseLink = ""
    if(c==1):
        try:
            publishingHouseLink = dom.xpath('//div[@class="type02_p003 clearfix"]//li[2]/a[1]/@href')[0]
            publishingHouse = dom.xpath('//div[@class="type02_p003 clearfix"]//li[2]/a[1]//text()')[0]
            #print(publishingHouse,publishingHouseLink)
        except:
            print('找不到：出版社')
    else:
        try:
            publishingHouseLink = dom.xpath('//div[@class="type02_p003 clearfix"]//li[3]/a[1]/@href')[0]
            publishingHouse = dom.xpath('//div[@class="type02_p003 clearfix"]//li[3]/a[1]//text()')[0]
            #print(publishingHouse,publishingHouseLink)
        except:
            print('找不到：出版社')
    #出版地 publisher place
    publisherPlace = ''
    try:
        publisherPlace = dom.xpath('//div[@class="bd"]/ul[1]/li[4]/text()')[0].replace('出版地：','')
        #print(publisherPlace)
    except:
        print('找不到：出版地')
    #原價 orPrice
    orPrice = ''
    try:
        orPrice = dom.xpath('//div[@class="grid_24 main_column"]//ul[@class="price"]/li[1]/em/text()')[0]
        #print(orPrice)
    except:
        print('找不到：原價')

    #優惠價
    howto = ''
    try:
        howto = dom.xpath('//div[@class="grid_24 main_column"]//ul[@class="price"]/li[2]/strong[@class="price01"]/b/text()')[0]
        #print(howto)
    except:
        print('找不到：優惠價')

    #規格 specification 
    specification = ''
    try:
        specification = dom.xpath('//div[@class="bd"]/ul[1]/li[3]/text()')[0].replace('規格：','')
        #print(specification)
    except:
        print('找不到：規格')
    
    articles.append({
            'ISBN':str(ISBN),
            'title':str(pageLink['title']), 
            'link':'https:'+str(pageLink['link']), 
            'cover':str(cover),
            'author':str(author), 
            'author_link':str(authorLink),
            'translator':str(translator),
            'translatorUrl':str(translatorUrl),
            'publishingHouse':str(publishingHouse),
            'publishingHouseLink':str(publishingHouseLink),
            'publisherPlace':str(publisherPlace),
            'orPrice':str(orPrice),
            'howto':str(howto),
            'specification':str(specification),
            'images':image
            #'images': #解決 HTML Entity 編碼問題
        })
    title.append(str(pageLink['title']))
#清空字串內全部的 html tag，只留下內文
TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(text):
    return TAG_RE.sub('', text)
#解析檔案路徑及檔名
def path_leaf(path):
    tail = ntpath.split(path)
    return tail #or ntpath.basename(head)
#發現重複的列表項目，若有不再予以新增
def find_duplicate_db_list(item):
    sqlalchemy.Table(__listtable__, metadata, autoload=True)
    Alist = automap.classes[__listtable__]

    aList = session.query(
        Alist
    ).filter(
        Alist.source_id == 1, #item['source_id'],
        Alist.article_title == item['title'],
        Alist.article_url == item['link']
    ).first()

    if aList:
        loguru.logger.info('Find duplicate source article: ' + str(aList.id))
        return aList.id
    else:
        return False
def create_db_list_item(item):
    loguru.logger.info(item['title'])

    itemDuplicateId = find_duplicate_db_list(item)
    if itemDuplicateId != False:
        return itemDuplicateId

    created = int(time.mktime(datetime.now().timetuple()))
    sqlalchemy.Table(__listtable__, metadata, autoload=True)
    Alist = automap.classes[__listtable__]

    alist = Alist()
    alist.source_id = 1
    alist.topic = keyword
    alist.article_title = item['title']
    alist.article_url = item['link']
    alist.created = created
    session.add(alist)
    session.flush()

    return alist.id



def create_db_article(item, listId):
    created = int(time.mktime(datetime.now().timetuple()))
    sqlalchemy.Table(__articletable__, metadata, autoload=True)
    Article = automap.classes[__articletable__]

    sourceContent = {
        'keyword': keyword, 
        'translator':item['translator'],    
        'author' : item['author'],
        'authorUrl' : item['author_link'],
        'translatorUrl':item['translatorUrl'],
        'publishingHouse':item['publishingHouse'],
        'publishingHouseUrl':item['publishingHouseLink'],
    }
    sourceContent = json.dumps(sourceContent, ensure_ascii=False).encode('utf-8').decode('utf-8')
    print(sourceContent)

    article = Article()
    article.list_id = listId
    article.book_link = item['link']
    article.title = item['title']
    article.source_content = sourceContent
    article.image = item['images']
    article.image_link = item['cover']
    article.ISBN = item['ISBN']
    article.orprice = item['orPrice']
    article.howto = item['howto']
    article.specification = item['specification']
    article.created = created

    session.add(article)
    return

def create_db_scrapy():
    for item in articles:
        listId = create_db_list_item(item)
        create_db_article(item, listId)

        try:
            session.commit()
        except Exception as e:
            loguru.logger.error('新增資料失敗')
            loguru.logger.error(e)
            session.rollback()

    #session.close()
    loguru.logger.info('完成爬蟲及寫入資料.')
    return

def get_db_articles():
    loguru.logger.info('get_db_articles')
    #TODO:從資料庫合併查詢 list ,article, articlemeta 及 article_media
    sqlalchemy.Table(__listtable__, metadata, autoload=True)
    Listtable = automap.classes[__listtable__]

    sqlalchemy.Table(__articletable__, metadata, autoload=True)
    Articletable = automap.classes[__articletable__]

    articles = session.query(
        Listtable, Articletable
    ).filter(
        Listtable.source_id == 1,
        Listtable.id == Articletable.list_id
    ).with_entities(
        Listtable.id,
        Listtable.topic,
        Listtable.article_url,
        Articletable.title,
        Articletable.source_content
    ).all()

    return articles

if __name__ == '__main__':
    loguru.logger.add(
        f'{datetime.today().strftime("%Y%m%d")}.log',
        rotation='1 day',
        retention='7 days',
        level='DEBUG'
    )
    
    config = configparser.ConfigParser()
    config.read("config.ini")
    solver = CaptchaSolver('2captcha', api_key = "")
    #Selenium with webdriver
    options = Options()
    options.binary_location = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    webdriver_path = 'C:\\chromedriver_win32\\chromedriver.exe'
    driver = webdriver.Chrome(executable_path=webdriver_path, options=options)
    
    #資料庫定義
    __articletable__ = 'crawler_article'
    __articlemetatable__ = 'crawler_articlemeta'
    __fieldstable__ = 'crawler_fields'
    __listtable__ = 'crawler_list'
    __mediatable__ = 'crawler_media'

    __post_type__ = 'scrapy'
    __taxonomy_name__ = 'scrapies'

    host = config['mysql']['Host']
    port = int(config['mysql']['Port'])
    username = config['mysql']['User']
    password = config['mysql']['Password']
    database = config['mysql']['Database']
    chartset = config['mysql']['Charset']

     # 建立連線引擎
    connect_string = connect_string = 'mysql+mysqlconnector://{}:{}@{}:{}/{}?charset={}'.format(username, password, host, port, database, chartset)
    connect_args = {'connect_timeout': 10}
    engine = sqlalchemy.create_engine(connect_string, connect_args=connect_args, echo=True)
    # 取得資料庫元資料
    metadata = sqlalchemy.schema.MetaData(engine)
    # 產生自動對應參照
    automap = sqlalchemy.ext.automap.automap_base()
    automap.prepare(engine, reflect=True)
    # 準備 ORM 連線
    session = sqlalchemy.orm.Session(engine)
    
    keyword = '被討厭的勇氣'
    main()
