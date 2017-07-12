#_*_ coding:utf-8 _*_
import re
from bs4 import BeautifulSoup
import xlsxwriter
import lxml
import math
import urllib
from six.moves import urllib
from urllib import quote
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class restaurant:
    def __init__(self, bs,menubs):
        self.r_rating = 0   #rating
        self.r_name = ""    #음식점이름
        self.r_address = ""  #음식점주소
        self.r_menulist = [] #메뉴리스트
        self.r_reviewtotalcnt = 0 #총리뷰수
        self.r_bs = bs       #해당 레스토랑 bs파싱내용
        self.r_menubs = menubs#menu bs파싱내용
        self.r_time = ""
    def get_info_by_bs(self):
        try:
            self.r_name = self.r_bs.find(itemprop='name').get_text()
        except:
            self.r_name = "open error"
        try:
            self.r_rating = self.r_bs.find(itemprop ='ratingValue').get_text()
        except:
            self.r_rating = 0
        try:
            self.r_address = self.r_bs.find(itemprop ='address').get_text()
        except:
            self.r_address = "open error"
        try:
            venuekey = self.r_bs.find_all("div", class_="venueRowKey")
            venueall = self.r_bs.find_all("div", class_="venueRowValue")
            for idx in range(len(venuekey)):
                tmptxt =venuekey[idx].get_text().encode("utf-8")
                if tmptxt == "메뉴":
                    self.r_time = venueall[idx].get_text().encode("utf-8")
                    break;
        except:
            self.r_time = ""
        if self.r_menubs != None: #메뉴판있음
            self.r_menulist = self.r_menubs.find_all("div", class_="menuHeader")
        try:
            self.r_reviewtotalcnt = self.r_bs.find("span", class_="sectionCount").get_text()
            self.r_reviewtotalcnt = self.r_reviewtotalcnt.replace(',', '')
        except:
            self.r_reviewtotalcnt = 49

        for idx in range(len(self.r_menulist)):
            self.r_menulist[idx] = self.r_menulist[idx].get_text().encode("utf-8")
#print self.r_reviewtotalcnt
#print self.r_menulist, len(self.r_menulist)
#print self.r_name
#print self.r_rating
#print self.r_address
class human:
    def __init__(self, link, name, date):
        self.name = name#name
        self.date = date#날짜
        self.link = link  # 아이뒤링크
        self.tip = 0 #팁개수
        self.flink = ""#페이스북링크
    def printinfo(self):
        print self.name, self.date, self.tip, self.flink
    def set_tip_and_flink(self,_tip,_flink):
        self.tip =_tip
        self.flink = _flink
class collection:
    def __init__(self, url,totalcnt,firstbs):
        self.c_menulist = [] # 언급된 메뉴리스트
        self.c_reviewlist = [] # 키워드가 언급된 리뷰리스트 1차원@
        self.c_menu_scorelist_2d = [] #각메뉴의 5등급 스코어 점수가 저장된 2차원배열
        self.c_menu_categorylist_2d = [] # 각메뉴의 카테고리가 저장되어 있는 2차원배열
        self.c_menu_foodchar =  [] #음식특징
        self.c_imglist = [] # 이미지경로저장할 배열@
        self.c_humanlist = [] # humaninfo를 저장할 클래스 리스트
        self.c_totalreviewcnt = totalcnt
        self.c_url = url
        self.c_bs = firstbs
        self.c_foodidxlist = []  # 실행속도를 높이기위해 food가 있는 review 리스트의 idx
    def extract_userinfo_byurl(self):
        errorlist = []
        for human in self.c_humanlist:
            url = "https://ko.foursquare.com" + human.link
            bs = get_bs_by_url(url)
            if bs is not None:
                try:
                    tip = bs.find("span", class_="stat").find("strong").get_text()
                except:
                    print "지금오류걸림"
                    print human.link
                    tip = 0
                try:# 페북링크없으면
                    flink = bs.find("a", class_="fbLink iconLink")
                    flink = flink['href']
                except:
                    flink = ""
                human.set_tip_and_flink(tip,flink)
                #human.printinfo()
            else:
                print "userinfo_byurl error 3->", human.link
                errorlist.append(human)
    def extract_food(self, menulist):
        global c_keword
        global G_categorylist
        global G_footcharlist
        if not menulist == []: #메뉴가 있으면
            for food in menulist:
                foodscore = [0 for i in range(c_keword.gradecnt)]  # 푸드마다 스코어 리스트생성
                idx = 0
                foodtxt = food.lower()
                for review in self.c_reviewlist:
                    foodchartxt = "" # 음식char생성
                    foodcategory = ""  # 푸드카테고리생성
                    reviewtxt = review.lower()
                    if not reviewtxt.find(foodtxt) == -1:  # 리뷰속에서 음식을 찾으면
                        for category in G_categorylist:
                            categorytxt =category.lower()
                            if not foodtxt.count(categorytxt) == 0:  # 하나라도 있다, 추가시켜주기
                                foodcategory = foodcategory + categorytxt + ","
                        IsExist = False
                        try:
                            foodidx = self.c_menulist.index(food)  # 이미 수집음식목록에 있나본다
                            foodscore = self.c_menu_scorelist_2d[foodidx] #있으면 음 음 음 기존의 푸드스코어 배열을 주고
                            self.c_foodidxlist.append(idx) # ㄱ속도향상을위해 review인덱스를 넘겨준다
                            IsExist = True
                        except: #없음
                            self.c_menulist.append(food)  # 음식을 추가하고
                            self.c_foodidxlist.append(idx)
                        #자이제 등급을매기자
                        for gradeidx in range(0, c_keword.gradecnt):  # 등급을 매기는 키워드 idx 끝까지돌면서
                            for keyword in c_keword.keyword[gradeidx]:  # 반환값은 해당 idx의 키워드 리스트
                                if not reviewtxt.count(keyword) == 0:  # 하나라도 있다, 추가시켜주기
                                    foodscore[gradeidx] = foodscore[gradeidx] + reviewtxt.count(keyword)  # 스코어 값늘려주기
                                    foodchartxt = foodchartxt + keyword + ","
                        for foodchar in G_footcharlist:
                            chartxt = foodchar.lower()
                            if not reviewtxt.count(chartxt) == 0:  # 하나라도 있다, 추가시켜주기
                                foodchartxt = foodchartxt + chartxt + ","

                        if IsExist: #이미있던거
                            self.c_menu_scorelist_2d[foodidx] = foodscore #갱신
                            self.c_menu_categorylist_2d[foodidx] = foodcategory
                            self.c_menu_foodchar[foodidx] = foodchartxt
                        else: #없었으면추가
                            self.c_menu_scorelist_2d.append(foodscore)
                            self.c_menu_categorylist_2d.append(foodcategory)
                            self.c_menu_foodchar.append(foodchartxt)
                    idx = idx + 1
#print self.c_menulist, len(self.c_menulist)
#print self.c_menu_scorelist_2d, len(self.c_menu_scorelist_2d)
#print self.c_menu_categorylist_2d, len(self.c_menu_categorylist_2d)
    def get_fillter_review(self):
        global c_keword
        query = "tipsSort=popular&tipsPage=" #?해서넘어온다
        try:
            pagecnt = int(math.ceil(int(self.c_totalreviewcnt) / 50.0))
        except:
            pagecnt = 1
        #우선첫번째꺼기입
        tmpreviewlist = self.c_bs.find_all("div",class_="tipText")
        imglist = self.c_bs.find_all("img", class_="tipPhoto")
        namelist = self.c_bs.find_all("span",class_="userName") # 이름 리스트 여기안에 href도 존재
        for remove in namelist[50:]: #50개이후는지움
            namelist.remove(remove)
        idlinklist =[]
        datelist = self.c_bs.find_all("span",class_="tipDate") #날짜리스트
        #날짜
        for i in range(len(datelist)):
            datelist[i] = datelist[i].get_text().encode('utf-8')
        #이름및 링크
        for i in range(len(namelist)):
            if namelist[i].find('a') is not None:
                idlinklist.append( namelist[i].find('a')['href'] )
                namelist[i] = namelist[i].get_text().encode('utf-8')
#print idlinklist, len(idlinklist)
#print namelist, len(namelist)
        #이미지는 다필요

        for i in imglist:
            self.c_imglist.append( i['src'] )
        idx = 0
        for tmpreview in tmpreviewlist:
            IsSearch = False
            tmpreview = tmpreview.get_text().encode('utf-8')
            tmpreview = tmpreview.lower()  # 모든 문자를 소문자로 변환
            for gradeidx in range(0, c_keword.gradecnt):  # 등급을 매기는 키워드 idx 끝까지돌면서
                if IsSearch is True:
                    break;
                for keyword in c_keword.keyword[gradeidx]:  # 반환값은 해당 idx의 키워드 리스트
                    if not tmpreview.find(keyword) == -1:  # 하나라도 찾았다
                        self.c_reviewlist.append(tmpreview)
                        try:
                            self.c_humanlist.append(human(idlinklist[idx],namelist[idx],datelist[idx]))
                        except:
                            pass
                        IsSearch = True
                        break;
            idx +=1
# print self.c_reviewlist, len(self.c_reviewlist)
# for i in self.c_humanlist:
#    i.printinfo()
# 나머지꺼 2개이상의 페이지를 가질때만 돌린다
        if pagecnt > 1:
            for i in range(2, pagecnt + 1):
                roofcnt = 0
                html = self.c_url + query + str(i)
                while (roofcnt < 2):
                    try:
                        f = urllib.request.urlopen(html)
                        break;
                    except:
                        urllib.request.urlcleanup()
                        print "get_fillter_review error 2 : urlopen재시도중"
                        roofcnt += 1
                if not roofcnt == 2:
                    resultXML = f.read()
                    bs = BeautifulSoup(resultXML, "lxml")
                    tmpreviewlist = bs.find_all("div", class_="tipText")
                    imglist = bs.find_all("img", class_="tipPhoto")
                    namelist = bs.find_all("span", class_="userName")  # 이름 리스트 여기안에 href도 존재
                    if len(namelist) > 50:
                        for remove in namelist[50:]:  # 50개이후는지움
                            namelist.remove(remove)
                    idlinklist = []
                    datelist = bs.find_all("span", class_="tipDate")  # 날짜리스트
                    # 날짜
                    for i in range(len(datelist)):
                        datelist[i] = datelist[i].get_text().encode('utf-8')
                    # 이름및 링크
                    for i in range(len(namelist)):
                        if namelist[i].find('a') is not None:
                            idlinklist.append(namelist[i].find('a')['href'])
                            namelist[i] = namelist[i].get_text().encode('utf-8')
                            # print idlinklist, len(idlinklist)
                            # print namelist, len(namelist)
                    # 이미지는 다필요
                    for i in imglist:
                        self.c_imglist.append(i['src'])
                    idx = 0
                    for tmpreview in tmpreviewlist:
                        IsSearch = False
                        tmpreview = tmpreview.get_text().encode('utf-8')
                        tmpreview = tmpreview.lower()  # 모든 문자를 소문자로 변환
                        for gradeidx in range(0, c_keword.gradecnt):  # 등급을 매기는 키워드 idx 끝까지돌면서
                            if IsSearch is True:
                                break;
                            for keyword in c_keword.keyword[gradeidx]:  # 반환값은 해당 idx의 키워드 리스트
                                if not tmpreview.find(keyword) == -1:  # 하나라도 찾았다
                                    self.c_reviewlist.append(tmpreview)
                                    self.c_humanlist.append(human(idlinklist[idx], namelist[idx], datelist[idx]))
                                    IsSearch = True
                                    break;
                        idx += 1

#print self.c_reviewlist, len(self.c_reviewlist)
#print self.c_imglist, len(self.c_imglist)
#print len(self.c_humanlist#)
#for i in self.c_humanlist:
#     i.printinfo()

def get_bs_by_url(_url):
    #KJVAVYPHOHNYVHKGOVBOQGAC5322EFAZILJE0DW3IX1DBPMW
    #SPUY1SE0AK2JEYC4NAXINQZPRMVGOJJRZ0DMHRWJ5OTXB3MM
    html = _url
    cnt = 0
    while( cnt < 3):
        try:
            f = urllib.request.urlopen(html)
            break;
        except urllib.error.HTTPError as e:
            print(e.reason)
            urllib.request.urlcleanup()
            print "get_bs_by_url error 1 : urlopen재시도중"
            try:
                f = urllib.request.urlopen(html)
                break;
            except:
                urllib.request.urlcleanup()
                print "리셋후재연결중"
            cnt += 1
    if cnt == 3: return None
    resultXML = f.read()
    bs = BeautifulSoup(resultXML, "lxml")
#print bs.prettify()
    return bs
class get_keword_by_txt:
    def __init__(self,filename):
        self.keyword = [] # 등급별 키워드 2차원배열
        self.gradecnt = 0 #등급이 몇분류 까지 되어있는지
        with open(filename, "r") as f:
            line = f.read().decode("utf-8-sig").encode("utf-8")
            content = line.split('@')
            grade_list = []
            for i in range(0, len(content)):
                if not content[i] == '':
                    grade_list.append(content[i].strip())#공백제거
            self.gradecnt = len(grade_list) #몇등급 분류되어있는지 가져온다

            for keyword in grade_list:
                key = keyword.split(":")[1]
                #print key
                self.keyword.append(list(key.split(','))) # 2차원 배열로 정리
            #print self.keyword , len(self.keyword), (self.gradecnt)
def get_category_by_txt(filename):
    with open(filename, "r") as f:
        line = f.read().decode("utf-8-sig").encode("utf-8")
        content = line.split('/')
        for idx in range(len(content)):
            content[idx] = content[idx].strip()
        return content
def make_excel(collectclass,restaurantinfoclass, num, workbook):
    sheetname = '(' + str(num) + ').'+restaurantinfoclass.r_name
    try:
        worksheet = workbook.add_worksheet(sheetname)
    except:
        a = ['[', ']', ':', '*', '?', '/']
        b = ' \ '
        a.append(b.strip())
        print "워크시트이름 오류 :",sheetname
        sheetname = sheetname [:10] + "..."
        print sheetname
        try:
            worksheet = workbook.add_worksheet(sheetname)
        except:
            print "워크시트 이름최종오류2"
            sheetname = sheetname[:3]+"..."
            for i in a:
                sheetname = sheetname.replace(i, '')
            worksheet = workbook.add_worksheet(sheetname)
    worksheet.set_column('A:A', 6)  # 레이팅
    worksheet.set_column('B:B', 25)  # 주소
    worksheet.set_column('C:C', 20)  # 업체이름
    col_list = ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O','P','Q','R']
    for j in range(0, 5):  # 레이팅적는곧
        worksheet.set_column(col_list[j] + ":" + col_list[j], 6)
    sangidx = 5
    worksheet.set_column(col_list[sangidx] + ":" + col_list[sangidx], 15)  # 상품특징
    snagjong = sangidx+1
    worksheet.set_column(col_list[snagjong] + ":" + col_list[snagjong], 15)  # 음식종류
    sangtime = snagjong+1
    worksheet.set_column(col_list[sangtime] + ":" + col_list[sangtime], 15)  # 음식종류
    blankidx = sangtime + 1
    worksheet.set_column(col_list[blankidx] + ":" + col_list[blankidx], 2)  # 빈칸
    reidx = blankidx + 1
    worksheet.set_column(col_list[reidx] + ":" + col_list[reidx], 100)  # 리뷰
    humanidx = reidx+1
    worksheet.set_column(col_list[humanidx] + ":" + col_list[humanidx], 20)  # 이름
    humanidx2 =humanidx+1
    worksheet.set_column(col_list[humanidx2] + ":" + col_list[humanidx2], 20)  # 날짜
    humanidx3 =humanidx2+ 1
    worksheet.set_column(col_list[humanidx3] + ":" + col_list[humanidx3], 20)  # flink
    humanidx4 =humanidx3+ 1
    worksheet.set_column(col_list[humanidx4] + ":" + col_list[humanidx4], 5)  # tip
    humanidx5 =humanidx4+ 1
    worksheet.set_column(col_list[humanidx5] + ":" + col_list[humanidx5], 50)  # img
    # 첫줄
    format = workbook.add_format()
    format.set_font_size(8)
    format.set_bold()
    format.set_align('center')
    format.set_bg_color('yellow')
    format.set_border(True)
    # 한글은 앞에 u자붙여라
    worksheet.write('A1', "Rating", format)
    worksheet.write('B1', u"업체명(위) / 주소(아래)", format)
    worksheet.write('C1', u"음식명", format)
    for k in range(0, 5):  # 레이팅적는곧
        worksheet.write(col_list[k] + "1", "[" + str(k + 1) + "]", format)
    worksheet.write(col_list[sangidx] + "1", u"음식특징", format)
    worksheet.write(col_list[snagjong] + "1", u"음식종류", format)
    worksheet.write(col_list[sangtime] + "1", u"시간대", format)
    worksheet.write(col_list[blankidx] + "1", "", format)
    worksheet.write(col_list[reidx] + "1", "filltered review", format)
    worksheet.write(col_list[humanidx] + "1", "user id", format)
    worksheet.write(col_list[humanidx2] + "1", "date", format)
    worksheet.write(col_list[humanidx3] + "1", "facebook link", format)
    worksheet.write(col_list[humanidx4] + "1", "Tip", format)
    worksheet.write(col_list[humanidx5] + "1", "img url", format)
    #입력시작
    format = workbook.add_format()
    format.set_font_size(8)
    format.set_align('center')
    spformat = workbook.add_format()
    spformat.set_font_size(8)
    spformat.set_align('center')
    spformat.set_bg_color('red')
    #기본적인 정보 입력
    row_start = 1  # 시작할 행넘버
    worksheet.write(row_start, 0, restaurantinfoclass.r_rating, format)
    worksheet.write(row_start, 1, restaurantinfoclass.r_name, format)
    worksheet.write(row_start + 1, 1, restaurantinfoclass.r_address, format)
    #음식입력
    for idx in range(0, len(collectclass.c_menulist)):  # 수집된 음식 개수만큼돈다
        worksheet.write(row_start, 2, collectclass.c_menulist[idx], format)
        for q in range(0, 5):  # 레이팅적는곧
            worksheet.write(row_start, 3 + q, collectclass.c_menu_scorelist_2d[idx][q], format)
        worksheet.write(row_start, 2, collectclass.c_menulist[idx], format)
        worksheet.write(row_start, 3 + 5, collectclass.c_menu_foodchar[idx], format)  # 음식특징
        worksheet.write(row_start, 3 + 6, collectclass.c_menu_categorylist_2d[idx], format)#음식카테고리
        worksheet.write(row_start, 3 + 7, restaurantinfoclass.r_time, format)  # 음식카테고리
        row_start += 1
    # Write some numbers, with row/column notation.
    row_start = 1  # 시작할 행넘버
    blankidx = blankidx + 3
    reidx = reidx + 3  # 레이팅, 주소, 음식명이 3개니까
    for idx in range(0, len(collectclass.c_reviewlist)):  # 리뷰 를 출력할것
        try:
            worksheet.write(row_start, humanidx+3, collectclass.c_humanlist[idx].name, format)
            worksheet.write(row_start, humanidx2+3, collectclass.c_humanlist[idx].date, format)
            worksheet.write(row_start, humanidx3+3, collectclass.c_humanlist[idx].flink, format)
            worksheet.write(row_start, humanidx4+3, collectclass.c_humanlist[idx].tip, format)
            collectclass.c_foodidxlist.index(idx)  # 찾았는데 있다 음식키워드가 있던글
            worksheet.write(row_start, blankidx, idx + 1, spformat)
            worksheet.write(row_start, reidx, collectclass.c_reviewlist[idx], format)
        except:  # 없다
            worksheet.write(row_start, blankidx, idx + 1, format)
            try:
                worksheet.write(row_start, reidx, (collectclass.c_reviewlist[idx]), format)
            except:
                print("인코딩변환 시도")
                try:
                    worksheet.write(row_start, reidx, (collectclass.c_reviewlist[idx].decode('utf-8')), format)
                except:
                    print("인코딩오류")
                    worksheet.write(row_start, reidx, ("encoding error"), format)
        row_start += 1
    row_start = 1  # 시작할 행넘버
    #print collectclass.c_imglist
    for idx in range(0, len(collectclass.c_imglist)):  # 리뷰 를 출력할것
        worksheet.write(row_start, humanidx5+3, collectclass.c_imglist[idx], format)
        row_start +=1

c_keword = get_keword_by_txt("grade.txt") #키워드 등급정보가 있는 파일이름을 적으면됨 클래스 객체 반환
G_categorylist = get_category_by_txt("category.txt")
G_footcharlist = get_category_by_txt("food.txt")
def get_urllist():
    url = "https://ko.foursquare.com"
    urllist = []
    with open("test2.txt", "r") as f:
        resultXML = f.read().decode("utf-8-sig").encode("utf-8")
        bs = BeautifulSoup(resultXML, 'html.parser')
        venue = bs.find_all("div", class_="venueName")
        for i in venue:
            urllist.append( url+i.find('a')['href'] )
        return urllist
def main():
    urllist = get_urllist()
    print urllist, len(urllist)
    #startidx = raw_input("시작:")
    #endidx = raw_input("끝:")
    startidx = 81
    endidx   = 90
    name  = "boston"
    idx = 0
    with xlsxwriter.Workbook(name+ str(startidx) + "-" + str(endidx) + ".xlsx") as workbook:
        print name,startidx, '~' ,endidx,'분석시작'
        for url in urllist[int(startidx)-1:int(endidx)]:
            menuurl = url + '/menu'
            url = url + '?'
            print idx+1, " 개 진행중..."
            print url
            bs = get_bs_by_url(url)
            if bs is None:
                idx += 1
                continue
            menu_bs = get_bs_by_url(menuurl)
            print "분석중..."
            c_restaurant = restaurant(bs,menu_bs) # bs 데이터 넘겨주고
            c_restaurant.get_info_by_bs() # bs 로 레스토랑의 info를 자체클래스에 입력
            c_collection = collection(url,c_restaurant.r_reviewtotalcnt,bs) # basic url과 review total전달
            c_collection.get_fillter_review()
            c_collection.extract_food(c_restaurant.r_menulist)
            c_collection.extract_userinfo_byurl()
            make_excel(c_collection,c_restaurant, idx+int(startidx), workbook)
            idx += 1

main()








