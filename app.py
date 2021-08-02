# region 使用包
from __future__ import unicode_literals
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models.mentionee import Mentionee
from linebot.models.mention import Mention
from base import config as base_sitting
import requests
import json
import pyodbc
import configparser
import random

# endregion

app = Flask(__name__)

# region LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')
line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
# endregion

# region 查看名單權限
list_access = {"U24d5bec32ae71a93aed8deab4bcf78ad", "U0700a417f44ea2f6a95bbad0bd1af7ff"}
# endregion

# region 寄送通知權限
list_access_notify = {"U24d5bec32ae71a93aed8deab4bcf78ad"}
# endregion

# region 職業MAP
dic_tian = {"太白": 1, "神威": 2, "丐幫": 3, "移花": 4, "天香": 5, "唐門": 6, "神刀": 7, "真武": 8}
dic_tian_re = {1: "太白", 2: "神威", 3: "丐幫", 4: "移花", 5: "天香", 6: "唐門", 7: "神刀", 8: "真武"}
# endregion

sqlConn = pyodbc.connect(base_sitting.connection, autocommit=True)
cursor = sqlConn.cursor()


# region 驗證 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # print(body, signature)
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'


# endregion


# region 機器人
@handler.add(MessageEvent, message=TextMessage)
def pretty_echo(event):
    return_text = ""

    # region 機器人ID
    if event.message.text == "機器人ID":
        return_text = "@915gtfxs"
    # endregion

    # region 密語
    if event.message.text == '漫漫賺大錢':
        return_text = "提醒一下，每日聚飲跟幫戰會用蘿蔔通知您！\n"
        return_text += "若不想接收提醒，可以點畫面右上方的選單圖示，然後關閉【提醒】喔。\n"
        return_text += "入群連結：http://line.me/ti/g/b0hIaU3X9I\n"
        return_text += "DC群連結：https://discord.gg/GehrAda649\n"
        return_text += "進入後記得留言。您的遊戲ID、您的職業"
    # endregion

    # region 名單
    if event.message.text == '名單':
        if event.source.user_id not in list_access:
            return_text = "你沒有查看名單的權限喔"
        else:
            cursor.execute("""
            SELECT [UserName]
                  ,[GameName]
                  ,[Job]
            FROM [Accounting].[dbo].[TianData]
            ORDER BY [Job] DESC""")
            data_list = cursor.fetchall()
            return_text = "目前登記名單如下：\n"
            count = 0
            for data in data_list:
                return_text += f'第{str(count + 1).zfill(3)}筆：{data.GameName}/{data.UserName}/{dic_tian_re[data.Job]}\n'
                count = count + 1
            return_text += f"共計：{count}筆"
    # endregion

    # region 登記方式
    if event.message.text == '登記方式':
        return_text = "登記：你的遊戲名稱，你的職業(需要全部複製)"
    # endregion

    # region 登記
    if '登記：' in event.message.text:
        profile = line_bot_api.get_profile(event.source.user_id)
        # print(profile.display_name)
        # print(profile.user_id)
        cursor.execute("""SELECT COUNT(*) AS C FROM TianData WHERE UserId = ?""", profile.user_id)
        check = cursor.fetchone()
        if check.C != 0:
            return_text = f"{profile.display_name}您已經記錄過了！"
        else:
            gamename = event.message.text.split("：")[1].split("，")[0]
            job = dic_tian[event.message.text.split("：")[1].split("，")[1]]
            # print(gamename)
            cursor.execute("""INSERT INTO [dbo].[TianData]
                           ([UserName]
                           ,[UserId]
                           ,[GameName]
                           ,[Job])
                        VALUES (?, ?, ?, ?)""", profile.display_name, profile.user_id, gamename, job)
            return_text = profile.display_name + "：已記錄"
    # endregion

    # region 通知
    if event.message.text == "通知":
        if event.source.user_id not in list_access_notify:
            return_text = "您沒有通知權限喔"
        else:
            cursor.execute("""
            SELECT [UserId]
            FROM [Accounting].[dbo].[TianData]
            ORDER BY [Job] DESC
            """)
            notify_list = cursor.fetchall()
            for notify in notify_list:
                line_bot_api.push_message(notify.UserId, TextMessage(text='晚上喝酒，打咚咚'))
            return_text = "已通知"
    # endregion

    # region 回覆
    if return_text == '':
        line_bot_api.reply_message(event.reply_token, TextMessage(text="挖母災哩咧工蝦"))
    else:
        line_bot_api.reply_message(event.reply_token, TextMessage(text=return_text))
    # endregion


# endregion

if __name__ == "__main__":
    app.run()
