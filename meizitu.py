import requests
from bs4 import  BeautifulSoup
import _thread
import hashlib
import pymysql
from DBUtils.PooledDB import PooledDB


class meizitu():
    MYSQL_HOST = 'localhost'
    USER = 'root'
    PASSWORD = '123456'
    DB = 'photogallery'
    PORT = 3306

    mainurl = "http://www.meizian.com"
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept - Encoding': 'gzip, deflate, br',
        'Accept - Language': 'zh - CN, zh;q = 0.9',
        'Upgrade - Insecure - Requests': '1',
        'User - Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
    }

#String 转md5
    def get_md5_value(self,src):
        myMd5 = hashlib.md5()
        myMd5.update(src.encode("UTF-8"))
        myMd5_Digest = myMd5.hexdigest()
        return myMd5_Digest

#分类
    def tpyeClassify(self):
        html = requests.get(self.mainurl, headers=self.headers)
        soup = BeautifulSoup(html.text, 'lxml')
        lis = soup.find_all(attrs={'class': "new-has-sub"})
        for li in lis:
            href=li.find("a")
            url=self.mainurl+str(href['href'])
            print(url)
            phototype=li.find("span").string
            pool = PooledDB(pymysql, 10, host=self.MYSQL_HOST, user=self.USER, passwd=self.PASSWORD, db=self.DB,
                            port=self.PORT)  # 10为连接池里的最少连接数
            # self.pageClassify(url,phototype,pool)
            _thread.start_new_thread(self.pageClassify, (url,phototype,pool))

#分页
    def pageClassify(self,url,phototype,pool):
        html = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(html.text, 'lxml')
        options = soup.find_all("option")
        for option in options:
            value=str(option['value'])
            everyPageURL=url+"?p="+value
            print(everyPageURL)
            self.albumClassify(everyPageURL,phototype,pool)

#分相册
    def albumClassify(self,url,phototype,pool):
        html = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(html.text, 'lxml')
        album_infos = soup.find_all("div", {"class": "image gallery-group-1"})
        for album_info in album_infos:
            info=album_info.find("a")
            img=info.find("img")
            album_url=self.mainurl+str(info['href'])
            album=str(img['alt'])
            print(album_url)
            print(album)
            self.savePhotoURL(album_url,phototype,pool,album)

#存储图片URL
    def savePhotoURL(self,url,phototype,pool,album):
        html = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(html.text, 'lxml')
        gallery=soup.find(id = "gallery")
        imgs = gallery.find_all("div", {"class": "image gallery-group-1"})
        for img in imgs:
            img_url = img.find("a")
            photourl=img_url.get('href')
            photoid=self.get_md5_value(img_url)
            conn = pool.connection()
            cur = conn.cursor()
            SQL = "select count(*) from meizi where photoid = '%s'"%(photoid)
            cur.execute(SQL)
            rows = cur.fetchone()
            print(rows[0])
            if(rows[0]==0):
                SQL="insert into meizi VALUES ('%s', '%s', '%s', '%s')"%(photoid,photourl,phototype,album)
                print(SQL)
                cur.execute(SQL)
                conn.commit()
            cur.close()
            conn.close()

    def __init__(self):
        self.tpyeClassify()


test=meizitu()