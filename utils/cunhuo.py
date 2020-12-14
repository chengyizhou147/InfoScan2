# -*- coding: utf-8 -*
from utils.common import *
import threading
from queue import Queue     # 接收域名
from urllib.parse import urlparse
import  pymysql


class Cunhuo_domain(object):
    # 初始化
    #q = queue.Queue()
    def __init__(self,file):
        #self.domain = domain
        self.file = file
        self.queue = Queue()
        self.thread_count = thread_count_Cunhuo
        self.result = []

    def run(self,url):
        logger.log('INFOR','开始进行url存活探测!')
        logger.log('INFOR', '请等待')
        db = connet()
        cursor = db.cursor()
        sql = """SELECT * FROM """+str(url).replace('.', '_')
        try:
            # 执行SQL语句
            cursor.execute(sql)
            # 获取所有记录列表
            results = cursor.fetchall()
            for row in results:
                sub_name = row[0]
                # 打印结果
                if sub_name == '' or sub_name == None:
                    pass
                else:
                    self.queue.put(sub_name)   # 从数据中进行查询收集的域名
        except:
            logger.log('INFOR',"Error: unable to fetch data")
        # cursor.execute(sql3)
        db.close()
        threads = []

        for i in range(self.thread_count):
            threads.append(self.Cubhuo_Run(self.queue,self.result,self.thread_count))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print_try("存活探测完成,发现" + str(len(list(set(self.result)))) + "个存活URL")
        Baocun_Cunhuo_url(url,list(set(self.result)))
        self.result.clear()
        return list(set(self.result))

    class Cubhuo_Run(threading.Thread):
        def __init__(self, queue, result,thread_count):
            threading.Thread.__init__(self)
            self.queue = queue
            self.result = result
            self.thread_count = thread_count

        def run(self):
            #print('请等待！')
            while not self.queue.empty():
                url = self.queue.get_nowait()
                try:
                    if 'http' in url:
                        head = requests.get(url, timeout=4)
                        #print(head.status_code)
                        if head.status_code != 404 and head.status_code != 500:
                            parse = urlparse(head.url)
                            new_url = "%s://%s/" % (parse.scheme, parse.netloc)
                            #logger.log('INFOR',new_url, head)
                            self.result.append(new_url)
                        else:
                            pass
                    else:
                        http_url = 'http://' + url
                        head = requests.get(http_url, timeout=4)
                        #print(head.status_code)
                        if head.status_code != 404 and head.status_code != 500:
                            parse = urlparse(head.url)
                            new_url = "%s://%s/" % (parse.scheme, parse.netloc)
                            #logger.log('INFOR',new_url, head)
                            self.result.append(new_url)
                        else:
                            pass
                except Exception as e:
                    pass
                # finally:
                #     self.thread_count.release()

        # # 显示执行情况
        # def msg(self):
        #     all_count = self.total
        #     found_count = len(list(set(self.result)))
        #     thread_count = self.thread_count
        #     use_count = self.total - self.queue.qsize()
        #     msg ='[*]ALL: '+str(all_count)+ ' | Thread: '+str(thread_count)+' | Schedule: '+ str(use_count)+' | Complete: '+str(round((use_count/all_count)*100,2)) +'% | Found: '+str(found_count) #+'\n' #+' [*] result: '+str(self.result)
        #     sys.stdout.write('\r'+str(msg))
        #     sys.stdout.flush()
