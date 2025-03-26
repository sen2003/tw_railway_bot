from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import speech_recognition as sr
from pydub import AudioSegment
import requests
import time
import random

# 網站設定和連線
options = Options()
options.add_argument('incognito')
# options.add_argument('--headless')
options.add_argument('--disable-blink-features=AutomationControlled')
# options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
driver.get('https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip119/queryTime')


def downloadMp3(mp3_url):  # 下載recaptcha的mp3 file
    res = requests.get(mp3_url)
    with open('recaptchaAudio.mp3', 'wb') as mp3_file:
        mp3_file.write(res.content)


def speechRecognition():  # 語音轉文字
    src = (r'C:\python_spider\recaptchaAudio.mp3')
    sound = AudioSegment.from_mp3(src)
    sound.export(r'C:\python_spider\recaptchaAudio.wav', format='wav')
    audio_file = sr.AudioFile(r'C:\python_spider\recaptchaAudio.wav')
    r = sr.Recognizer()
    with audio_file as source:
        audio_text = r.record(source)
    return r.recognize_google(audio_text)


def solveRecaptcha(x):  # 解recaptcha
    # 點擊recaptcha
    recaptcha = driver.find_element(
        By.XPATH, '//*[@id="recaptcha"]/div/div/div/iframe')
    recaptcha.click()
    time.sleep(random.randrange(1, 3))
    recaptcha_frame = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f'/html/body/div[{x}]/div[4]/iframe')))

    # 把driver切換到recaptcha iframe 上
    driver.switch_to.frame(recaptcha_frame)

    try:
        # 切換到語音驗證並取得mp3 file的href然後下載
        recaptcha_audio = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="recaptcha-audio-button"]')))
        recaptcha_audio.click()
        time.sleep(2)
        mp3_element = driver.find_element(
            By.CLASS_NAME, 'rc-audiochallenge-tdownload-link')
        mp3_url = mp3_element.get_attribute('href')
        downloadMp3(mp3_url)
    except:
        print('音檔下載失敗')

    try:
        # mp3轉文字後送出並驗證
        audio_text = speechRecognition()
        audio_response = driver.find_element(By.ID, 'audio-response')
        audio_response.send_keys(audio_text)
        time.sleep(1)
        driver.find_element(By.ID, 'recaptcha-verify-button').click()
        # 把driver切回主頁面
        driver.switch_to.default_content()
    except:
        print('recaptcha驗證失敗')

# Info=['yyyymmdd', '出發站', '抵達站', '開始時間(每半小時一單位)', '身分證字號']


# Info = ['20240310', '知本', '新左營', '16:00', '你的身分證']



def send_info(id):
    startStation = driver.find_element(By.ID, 'startStation')
    endStation = driver.find_element(By.ID, 'endStation')
    date = driver.find_element(By.ID, id)
    date.clear()
    startStation.clear()
    endStation.clear()
    date.send_keys(Info[0])
    time.sleep(1)
    startStation.send_keys(Info[1])
    time.sleep(1)
    endStation.send_keys(Info[2])


def search():
    # 獲取要操作的元素和輸入查詢資料
    startTime = Select(WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.NAME, 'startTime'))))
    endTime = Select(WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.NAME, 'endTime'))))

    send_info('calendar1')
    time.sleep(random.randrange(1, 4))
    startTime.select_by_value(Info[3])
    time.sleep(random.randrange(1, 3))

    solveRecaptcha(9)

    recaptcha = driver.find_element(
        By.XPATH, '//*[@id="recaptcha"]/div/div/div/iframe')
    recaptcha.click()

    time.sleep(2)
    driver.find_element(By.ID, 'searchButton').click()
    time.sleep(1)
    showInfoList()
    bookTicket()
    driver.quit()


def showInfoList():
    try:
        # 可移除
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tab1"]/div/table')))
        table = driver.find_element(By.XPATH, '//*[@id="tab1"]/div/table')
        header_tr = table.find_element(
            By.CSS_SELECTOR, '#tab1 > div > table > tbody > tr:nth-child(1)')
        ths = header_tr.find_elements(By.TAG_NAME, 'th')
        indices_to_remove = [4, 5, 10]  # 要去除的索引
        infoList = []
        new_ths = [ths[i]
                   for i in range(len(ths)) if i not in indices_to_remove]
        for th in new_ths:
            print(th.text, end=' | ')
            infoList.append(th.text)
        print('\n===============================================================================')
        # show時刻表
        trs = table.find_elements(By.CLASS_NAME, 'trip-column')
        for td_lists in trs:
            tds = td_lists.find_elements(By.TAG_NAME, 'td')
            new_tds = [tds[i]
                       for i in range(len(tds)) if i not in indices_to_remove]
            for i, td in enumerate(new_tds):
                try:
                    # 判斷class name判斷剩餘座位
                    td_div = td.find_element(By.TAG_NAME, 'div')
                    ticketLeft = td_div.get_attribute('class')
                    if ('times' in ticketLeft):
                        seat = '0位'  # td.text無法修改所以用一個新變數
                    elif ('exclamation-triangle' in ticketLeft):
                        seat = '30~1位'
                    else:
                        seat = '>30位'
                    print(infoList[i], ':', seat, end='\n')
                except:
                    print(infoList[i], ':', td.text, end='\n')
            print('\n')

        # 進入訂票頁面
        driver.find_element(
            By.XPATH, '/html/body/div[4]/div/ul/li[1]/a').click()
        driver.find_element(
            By.XPATH, '/html/body/div[4]/div/ul/li[1]/div/ul/li/ul[1]/li/div[2]/a[1]').click()
    except:
        print('查無資料')


def bookTicket():
    try:
        # 開始個人訂票，輸入身分證、起訖站、日期
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'pid')))

        pid = driver.find_element(By.ID, 'pid')
        pid.clear()
        pid.send_keys(Info[4])

        send_info('rideDate1')

        train_number = input('請輸入要訂的車次 : ')
        print('\n')
        tarin_Num = driver.find_element(By.ID, 'trainNoList1')
        tarin_Num.send_keys(train_number)
        time.sleep(1)

        solveRecaptcha(8)
        time.sleep(1)

        driver.find_element(
            By.XPATH, '//*[@id="queryForm"]/div[4]/input[2]').click()
        time.sleep(1)

        # 進入訂票成功頁面，並且顯示付款期限、旅程資訊、訂票代碼
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'alert-warning')))
        alert_warning = driver.find_element(By.CLASS_NAME, 'alert-warning')
        results = alert_warning.find_elements(By.TAG_NAME, 'p')
        for result in results:
            print(result.text.replace('請選擇票種/付款方式，並於 ', ''))
        detail_list = driver.find_element(By.CLASS_NAME, 'time-course')
        spans = detail_list.find_elements(By.TAG_NAME, 'span')
        for span in spans:
            print(span.text, end=' ')
        print('\n')
        ticket_num = driver.find_element(By.CLASS_NAME, 'cartlist-id')
        print(ticket_num.text)
        time.sleep(1)

        # 確認票種(全票)(有時候會失效)
        finish_btn = driver.find_element(
            By.XPATH, '//*[@id="order"]/div[4]/button')
        print(finish_btn.get_attribute('title'))
        finish_btn.click()
    except:
        print('訂票結束')


if __name__ == '__main__':
    search()
