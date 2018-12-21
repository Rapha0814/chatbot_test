# -*- coding: utf-8 -*-
import json
import re
import urllib.request
import datetime

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response

app = Flask(__name__)

sc = SlackClient(slack_token)


# 사용자가 입력한 텍스트 분석
def _get_text(text):
    mon = re.compile('\d{1,2}월')
    rday = re.compile('\d{1,2}일')
    ddi = re.compile('[ㄱ-ㅎ가-힣]{1,3}띠')
    star = re.compile('[ㄱ-ㅎ가-힣]{1,3}자리')

    # 운세를 보고 싶은 날짜 구하기
    year = str(datetime.date.today().year)
    if '오늘' in text:
        month = str(datetime.date.today().month)
        day = str(datetime.date.today().day)
    else:
        month = mon.findall(text)[0].replace("월", "")
        if len(month) == 1:
            month = "0"+month
        day = rday.findall(text)[0].replace("일", "")
        if len(day) == 1:
            day = "0"+day

    # 날짜 예외 처리
    if int(day) < 0 or int(day) > 31:
        return '*정확한 날짜를 입력하세요*'

    if int(month) < 0 or int(month) > 12:
        return '*정확한 날짜를 입력하세요*'

    search_date = year + month + day

    # 특정 별자리, 띠
    user_ddi = ddi.findall(text)
    user_star = star.findall(text) if '별' not in text else []

    # 운세정보를 얻을 때 넘겨줄 사용자 정보
    info = ''

    # 사용자가 입력한 정보에 따른 분기
    if '오늘' in text:
        if '별자리' in text or len(user_star) > 0:
            if len(user_star) > 0:
                info = user_star[0]
            else:
                info = str('별자리')
            url = "https://www.ytn.co.kr/_ln/0121_" + search_date + "000000000" + str(2)
            return _crawl_star_luck(info, url, month, day)
        elif '띠별' in text or len(user_ddi) > 0:
            if len(user_ddi) > 0:
                info = user_ddi[0]
            else:
                info = str('띠별')
            url = "https://www.ytn.co.kr/_ln/0121_" + search_date + "000000000" + str(1)
            return _crawl_ddi_luck(info, url, month, day)
        else:
            title = '*검색어에 다음 단어들 중 한개를 포함시켜 주세요*'
            txt = '\n@ 별자리 \n @ 띠별 \n @ ~자리 \n @ ~띠\n'
            return title + txt
    else:
        if '별자리' in text or len(user_star) > 0:
            if len(user_star) > 0:
                info = user_star[0]
            else:
                info = str('별자리')
            url = "https://www.ytn.co.kr/_ln/0121_" + search_date + "000000000" + str(2)
            return _crawl_star_luck(info, url, month, day)
        elif '띠별' in text or len(user_ddi) > 0:
            if len(user_ddi) > 0:
                info = user_ddi[0]
            else:
                info = str('띠별')
            url = "https://www.ytn.co.kr/_ln/0121_" + search_date + "000000000" + str(1)
            return _crawl_ddi_luck(info, url, month, day)
        else:
            title = '*검색어에 다음 단어들 중 한개를 포함시켜 주세요*'
            txt = '\n@ 별자리 \n @ 띠별 \n @ ~자리 \n @ ~띠\n'
            return title + txt


# 별자리 운세정보 크롤링
def _crawl_star_luck(info, url, month, day):
    star_content = dict()
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
    content = soup.find("div", class_="article_paragraph").find("span").get_text()

    key = ''
    temp_list = []
    for line in content.split('\n'):
        if '제공=드림웍' in line:
            continue
        # key값 생성
        if line.startswith('['):
            key = ''
            temp_list = []
            # 별자리를 key 값으로 설정
            for char in line:
                if char == '[':
                    pass
                elif char == '리':
                    key += char
                    break
                else:
                    key += char
        # <br> 필터링
        elif not (line):
            pass
        else:
            temp_list.append(line)
        star_content[key] = temp_list

    # 특정 별자리가 아닌 별자리 전체를 검색
    if info == '별자리':
        res = []
        for key, value in star_content.items():
            title = "*" + key + " " + month + "월 " + day + "일" + " 운세 :*"
            txt = '\n\n'
            for text in star_content[key]:
                txt += text.replace(".", "\n") + "\n"
            res.append(title + txt)
        return u'\n'.join(res)

    # 특정 별자리만 검색
    else:
        res = {}
        for key, value in star_content.items():
            # 사용자가 입력한 별자리가 있으면 결과값으로 저장
            if key == info:
                title = "*" + key + " " + month + "월 " + day + "일" + " 운세 :*"
                txt = '\n\n'
                for text in star_content[key]:
                    txt += text.replace(".", "\n") + "\n"
                res = {title + txt}
                break
            # 별자리에 없는 별자리를 입력 ex) 잠자리
            else:
                title = "*정확한 별자리 정보를 입력해 주세요*"
                txt = "\n물병\t물고기\t양\t황소\n쌍둥이\t게\t사자\t처녀\n천칭\t전갈\t사수\t염소"
                res = {title + txt}
        return u'\n'.join(res)


# 띠별 운세정보 크롤링
def _crawl_ddi_luck(info, url, month, day):
    ddi_content = dict()
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
    content = soup.find("div", class_="article_paragraph").find("span").get_text()

    key = ''
    temp_list = []
    for line in content.split('\n'):
        if '제공=드림웍' in line:
            continue
        # key값 생성
        if line.startswith('['):
            key = ''
            temp_list = []
            # 띠를 key 값으로 설정
            for char in line:
                if char == '[':
                    pass
                elif char == ']':
                    break
                else:
                    key += char
        # <br> 필터링
        elif not (line):
            pass
        else:
            temp_list.append(line)
        ddi_content[key] = temp_list

    # 특정 띠가 아닌 띠 전체 검색
    if info == '띠별':
        res = []
        for key, value in ddi_content.items():
            title = "*" + key + " " + month + "월 " + day + "일" + " 운세 :*"
            txt = '\n\n'
            for text in ddi_content[key]:
                txt += text.replace(".", "\n") + "\n"
            res.append(title + txt)
        return u'\n'.join(res)

    else:
        res = {}
        for key, value in ddi_content.items():
            # 사용자가 입력한 띠가 있으면 결과값으로 저장
            if key == info:
                title = "*" + key + " " + month + "월 " + day + "일" + " 운세 :*"
                txt = '\n\n'
                for text in ddi_content[key]:
                    txt += text.replace(".", "\n") + "\n"
                res = {title + txt}
                break
            # 정확하지 않은 띠를 입력 ex) 허리띠
            else:
                title = "*정확한 띠 정보를 입력해 주세요*"
                txt = "\n쥐\t소\t호랑이\t토끼\n용\t뱀\t말\t양\n개\t돼지\t원숭이\t닭"
                res = {title + txt}
        return u'\n'.join(res)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _get_text(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type": "application/json"})

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)