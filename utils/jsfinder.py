# -*- coding: utf-8 -*
# 用来爬取网站连接
# 参考链接https://github.com/Threezh1/JSFinder/blob/master/JSFinder.py
from bs4 import BeautifulSoup
from utils.common import *
import threading
from queue import Queue     # 接收域名
import pymysql


class Jsfinder(object):
    def __init__(self,file,a,b):
        #self.domain = domain
        self.a = a
        self.b = b
        self.file = file
        self.queue = Queue()
        self.thread_count = thread_count_Jsfinder
        self.result = []

    def run(self):
        logger.log('INFOR','开始进行爬取url链接!')
        db = connet()
        cursor = db.cursor()
        sql = """SELECT * FROM """ + str(self.file.replace('.', '_'))
        #print(sql)
        try:
            # 执行SQL语句
            cursor.execute(sql)
            # 获取所有记录列表
            results = cursor.fetchall()
            #print(results)
            for row in results:
                self.a = row[self.b]
                #print(self.a)
                # 打印结果
                if self.a == '' or self.a == None:
                    pass
                else:
                    self.queue.put(str(self.a))  # 从数据中进行查询收集的域名
        except Exception as e:
            logger.log('ALERT',e)
        # cursor.execute(sql3)
        db.close()
        threads = []

        for i in range(self.thread_count):
            threads.append(self.Jsfinder_Run(self.queue,self.result, self.thread_count,self.file))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        logger.log('INFOR',"链接爬取完成,连接保存至result/"+self.file+'_link')
        logger.log('INFOR',"子域名保存至result/"+self.file+'_sub')

    class Jsfinder_Run(threading.Thread):
        def __init__(self, queue, result, thread_count,file):
            self.file = file
            threading.Thread.__init__(self)
            self.queue = queue
            self.result = result
            self.thread_count = thread_count


        # Regular expression comes from https://github.com/GerbenJavado/LinkFinder
        def extract_URL(self,JS):
            pattern_raw = r"""
              (?:"|')                               # Start newline delimiter
              (
                ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
                [^"'/]{1,}\.                        # Match a domainname (any character + dot)
                [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
                |
                ((?:/|\.\./|\./)                    # Start with /,../,./
                [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
                [^"'><,;|()]{1,})                   # Rest of the characters can't be
                |
                ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
                [a-zA-Z0-9_\-/]{1,}                 # Resource name
                \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
                (?:[\?|/][^"|']{0,}|))              # ? mark with parameters
                |
                ([a-zA-Z0-9_\-]{1,}                 # filename
                \.(?:php|asp|aspx|jsp|json|
                     action|html|js|txt|xml)             # . + extension
                (?:\?[^"|']{0,}|))                  # ? mark with parameters
              )
              (?:"|')                               # End newline delimiter
            """
            pattern = re.compile(pattern_raw, re.VERBOSE)
            result = re.finditer(pattern, str(JS))
            if result == None:
                return None
            js_url = []
            return [match.group().strip('"').strip("'") for match in result
                    if match.group() not in js_url]


        # Get the page source
        def Extract_html(self,URL):
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36"}
            try:
                raw = requests.get(URL, headers=header, timeout=3, verify=False)
                raw = raw.content.decode("utf-8", "ignore")
                return raw
            except:
                return None


        # Handling relative URLs
        def process_url(self,URL, re_URL):
            black_url = ["javascript:"]  # Add some keyword for filter url.
            URL_raw = urlparse(URL)
            ab_URL = URL_raw.netloc
            host_URL = URL_raw.scheme
            if re_URL[0:2] == "//":
                result = host_URL + ":" + re_URL
            elif re_URL[0:4] == "http":
                result = re_URL
            elif re_URL[0:2] != "//" and re_URL not in black_url:
                if re_URL[0:1] == "/":
                    result = host_URL + "://" + ab_URL + re_URL
                else:
                    if re_URL[0:1] == ".":
                        if re_URL[0:2] == "..":
                            result = host_URL + "://" + ab_URL + re_URL[2:]
                        else:
                            result = host_URL + "://" + ab_URL + re_URL[1:]
                    else:
                        result = host_URL + "://" + ab_URL + "/" + re_URL
            else:
                result = URL
            return result

        def find_last(self,string, str):
            positions = []
            last_position = -1
            while True:
                position = string.find(str, last_position + 1)
                if position == -1: break
                last_position = position
                positions.append(position)
            return positions


        def find_by_url(self,url, js=False):
            if js == False:
                try:
                    logger.log('INFOR',"url:" + url)
                except:
                    logger.log('ALERT',"Please specify a URL like https://www.baidu.com")
                html_raw = self.Extract_html(url)
                if html_raw == None:
                    logger.log('ALERT',"Fail to access " + url)
                    return None
                # print(html_raw)
                html = BeautifulSoup(html_raw, "html.parser")
                html_scripts = html.findAll("script")
                script_array = {}
                script_temp = ""
                for html_script in html_scripts:
                    script_src = html_script.get("src")
                    if script_src == None:
                        script_temp += html_script.get_text() + "\n"
                    else:
                        purl = self.process_url(url, script_src)
                        script_array[purl] = self.Extract_html(purl)
                script_array[url] = script_temp
                allurls = []
                for script in script_array:
                    # print(script)
                    temp_urls = self.extract_URL(script_array[script])
                    if len(temp_urls) == 0: continue
                    for temp_url in temp_urls:
                        allurls.append(self.process_url(script, temp_url))
                result = []
                for singerurl in allurls:
                    url_raw = urlparse(url)
                    domain = url_raw.netloc
                    positions = self.find_last(domain, ".")
                    miandomain = domain
                    if len(positions) > 1: miandomain = domain[positions[-2] + 1:]
                    # print(miandomain)
                    suburl = urlparse(singerurl)
                    subdomain = suburl.netloc
                    # print(singerurl)
                    if miandomain in subdomain or subdomain.strip() == "":
                        if singerurl.strip() not in result:
                            result.append(singerurl)
                return result
            return sorted(set(self.extract_URL(self.Extract_html(url)))) or None


        def find_subdomain(self,urls, mainurl):
            url_raw = urlparse(mainurl)
            domain = url_raw.netloc
            miandomain = domain
            positions = self.find_last(domain, ".")
            if len(positions) > 1: miandomain = domain[positions[-2] + 1:]
            subdomains = []
            for url in urls:
                suburl = urlparse(url)
                subdomain = suburl.netloc
                # print(subdomain)
                if subdomain.strip() == "": continue
                if miandomain in subdomain:
                    if subdomain not in subdomains:
                        subdomains.append(subdomain)
            return subdomains


        def find_by_url_deep(self,url):
            html_raw = self.Extract_html(url)
            if html_raw == None:
                logger.log('ALERT',"Fail to access " + url)
                return None
            html = BeautifulSoup(html_raw, "html.parser")
            html_as = html.findAll("a")
            links = []
            for html_a in html_as:
                src = html_a.get("href")
                if src == "" or src == None: continue
                link = self.process_url(url, src)
                if link not in links:
                    links.append(link)
            if links == []: return None
            logger.log('INFOR',"ALL Find " + str(len(links)) + " links")
            urls = []
            i = len(links)
            for link in links:
                temp_urls = self.find_by_url(link)
                if temp_urls == None: continue
                logger.log('INFOR',"Remaining " + str(i) + " | Find " + str(len(temp_urls)) + " URL in " + link)
                for temp_url in temp_urls:
                    if temp_url not in urls:
                        urls.append(temp_url)
                i -= 1
            return urls



        def giveresult(self,urls, domian):
            #args = self.parse_args()
            if urls == None:
                return None
            logger.log('INFOR',"Find " + str(len(urls)) + " URL:")
            content_url = ""
            content_subdomain = ""
            for url in urls:
                #content_url += url + "\n"
                #print(url)
                with open("result/"+self.file+'_link', "a", encoding='utf-8') as fobject:
                    fobject.write(url+'\n')
            subdomains = self.find_subdomain(urls, domian)
            logger.log('INFOR',"\nFind " + str(len(subdomains)) + " Subdomain:")
            for subdomain in subdomains:
                content_subdomain += subdomain + "\n"
                #logger.log('INFOR',subdomain)
                with open("result/"+self.file+'_sub', "a", encoding='utf-8') as fobject:
                    fobject.write(subdomain + '\n')


        def run(self):
            while not self.queue.empty():
                url = self.queue.get_nowait()
                try:
                    logger.log('INFOR',"当前url:" + url)
                    urls = self.find_by_url_deep(url)
                    self.giveresult(urls,url)
                    #print("最后的url:" + content_url)
                except Exception as e:
                    logger.log('ALERT',e)
            #print("最后的url:"+content_url)
