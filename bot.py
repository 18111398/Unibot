import os
import json
import random
from datetime import datetime
from json import JSONDecodeError

import aiocqhttp
import aiofiles
import requests
import re
import time
import traceback
import yaml
from aiocqhttp import CQHttp, Event
from chachengfen import dd_query
from modules.api import gacha
from modules.chara import charaset, grcharaset, charadel, charainfo, grcharadel, aliastocharaid, get_card
from modules.config import whitelist, block, msggroup, aliasblock
from modules.cyo5000 import genImage
from modules.enmodules import engetqqbind, ensk, enbindid, ensetprivate, enaliastomusicid, endrawpjskinfo, endaibu, \
    enpjskjindu, enpjskb30, enpjskprofile
from modules.twmodules import twgetqqbind, twsk, twbindid, twsetprivate, twaliastomusicid, twdrawpjskinfo, twdaibu, \
    twpjskjindu, twpjskb30, twpjskprofile
from modules.gacha import getcharaname, getallcurrentgacha, getcurrentgacha, fakegacha
from modules.homo import generate_homo
from modules.musics import hotrank, levelrank, parse_bpm, aliastochart, idtoname, notecount, tasseiritsu, findbpm
from modules.pjskguess import getrandomjacket, cutjacket, getrandomchart, cutchartimg, getrandomcard, cutcard
from modules.pjskinfo import aliastomusicid, drawpjskinfo, pjskset, pjskdel, pjskalias
from modules.profileanalysis import daibu, rk, pjskjindu, pjskprofile, pjskb30
from modules.sendmail import sendemail
from modules.sk import sk, getqqbind, bindid, setprivate, skyc, verifyid, gettime
from modules.texttoimg import texttoimg, ycmimg
from modules.twitter import newesttwi

bot = CQHttp()
botdir = os.getcwd()

pjskguess = {}
charaguess = {}
ciyunlimit = {}
gachalimit = {'lasttime': '', 'count': 0}
admin = [1103479519]
mainbot = [1513705608]
requestwhitelist = []  # 邀请加群白名单 随时设置 不保存到文件
groupban = [467602419]
botdebug = False
botname = {
    1513705608: '一号机',
    3506606538: '三号机'
}

send1 = False
send3 = False


@bot.on_message('group')
async def handle_msg(event: Event):
    global blacklist
    global botdebug
    if event.message == '/delete unibot':
        info = await bot.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
        if info['role'] == 'owner' or info['role'] == 'admin':
            await bot.send(event, 'Bye~')
            await bot.set_group_leave(self_id=event.self_id, group_id=event.group_id)
        else:
            await bot.send(event, '你没有权限，该命令需要群主/管理员')
    if event.raw_message == '关闭娱乐':
        info = await bot.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
        if info['role'] == 'owner' or info['role'] == 'admin':
            if event.group_id in blacklist['ettm']:  # 如果在黑名单
                await bot.send(event, '已经关闭过了')
                return
            blacklist['ettm'].append(event.group_id)  # 加到黑名单
            with open('yamls/blacklist.yaml', "w") as f:
                yaml.dump(blacklist, f)
            await bot.send(event, '关闭成功')
        else:
            await bot.send(event, '此命令需要群主或管理员权限')
        return
    if event.raw_message == '开启娱乐':
        info = await bot.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
        if info['role'] == 'owner' or info['role'] == 'admin':
            if event.group_id not in blacklist['ettm']:  # 如果不在黑名单
                await bot.send(event, '已经开启过了')
                return
            blacklist['ettm'].remove(event.group_id)  # 从黑名单删除
            with open('yamls/blacklist.yaml', "w") as f:
                yaml.dump(blacklist, f)
            await bot.send(event, '开启成功')
        else:
            await bot.send(event, '此命令需要群主或管理员权限')
        return
    if event.raw_message == '关闭sk':
        info = await bot.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
        if info['role'] == 'owner' or info['role'] == 'admin':
            if event.group_id in blacklist['sk']:  # 如果在黑名单
                await bot.send(event, '已经关闭过了')
                return
            blacklist['sk'].append(event.group_id)  # 加到黑名单
            with open('yamls/blacklist.yaml', "w") as f:
                yaml.dump(blacklist, f)
            await bot.send(event, '关闭成功')
        else:
            await bot.send(event, '此命令需要群主或管理员权限')
        return
    if event.raw_message == '开启sk':
        info = await bot.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
        if info['role'] == 'owner' or info['role'] == 'admin':
            if event.group_id not in blacklist['sk']:  # 如果不在黑名单
                await bot.send(event, '已经开启过了')
                return
            blacklist['sk'].remove(event.group_id)  # 从黑名单删除
            with open('yamls/blacklist.yaml', "w") as f:
                yaml.dump(blacklist, f)
            await bot.send(event, '开启成功')
        else:
            await bot.send(event, '此命令需要群主或管理员权限')
        return
    if event.raw_message == '开启debug' and event.user_id in admin:
        botdebug = True
        await bot.send(event, '开启成功')
    if event.raw_message == '关闭debug' and event.user_id in admin:
        botdebug = False
        await bot.send(event, '关闭成功')


@bot.on_message('group')
def sync_handle_msg(event):
    global pjskguess
    global charaguess
    global ciyunlimit
    global gachalimit
    global blacklist
    global requestwhitelist
    if botdebug:
        timeArray = time.localtime(time.time())
        Time = time.strftime("[%Y-%m-%d %H:%M:%S]", timeArray)
        try:
            print(Time, botname[event.self_id] + '收到消息', event.group_id, event.user_id, event.message.replace('\n', ''))
        except KeyError:
            print(Time, '测试bot收到消息', event.group_id, event.user_id, event.message.replace('\n', ''))
    if event.group_id in groupban:
        # print('黑名单群已拦截')
        return
    if event.user_id in block:
        # print('黑名单成员已拦截')
        return
    if event.message[0:1] == '/':
        event.message = event.message[1:]
    try:
        if event.message == 'help':
            sendmsg(event, 'bot帮助文档：https://docs.unipjsk.com/')
            return
        if event.message[:8] == 'pjskinfo' or event.message[:4] == 'song':
            if event.message[:8] == 'pjskinfo':
                resp = aliastomusicid(event.message[event.message.find("pjskinfo") + len("pjskinfo"):].strip())
            else:
                resp = aliastomusicid(event.message[event.message.find("song") + len("song"):].strip())
            if resp['musicid'] == 0:
                sendmsg(event, '没有找到你要的歌曲哦')
                return
            else:
                leak = drawpjskinfo(resp['musicid'])
                if resp['match'] < 0.8:
                    text = '你要找的可能是：'
                else:
                    text = ""
                if leak:
                    text = text + f"匹配度:{round(resp['match'], 4)}\n⚠该内容为剧透内容"
                else:
                    if resp['translate'] == '':
                        text = text + f"{resp['name']}\n匹配度:{round(resp['match'], 4)}"
                    else:
                        text = text + f"{resp['name']} ({resp['translate']})\n匹配度:{round(resp['match'], 4)}"
                sendmsg(event,
                        text + fr"[CQ:image,file=file:///{botdir}\piccache\pjskinfo{resp['musicid']}.png,cache=0]")
            return
        if event.message[:7] == 'pjskset' and 'to' in event.message:
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
            event.message = event.message[7:]
            para = event.message.split('to')
            info = bot.sync.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
            if info['card'] == '':
                username = info['nickname']
            else:
                username = info['card']
            qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
            resp = pjskset(para[0], para[1], event.user_id, username, f"{qun['group_name']}({event.group_id})内")
            sendmsg(event, resp)
            return
        if event.message[:7] == 'pjskdel':
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
            event.message = event.message[7:]
            info = bot.sync.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
            if info['card'] == '':
                username = info['nickname']
            else:
                username = info['card']
            qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
            resp = pjskdel(event.message, event.user_id, username, f"{qun['group_name']}({event.group_id})内")
            sendmsg(event, resp)
            return
        if event.message[:9] == 'pjskalias':
            event.message = event.message[9:]
            resp = pjskalias(event.message)
            sendmsg(event, resp)
            return
        if event.message[:8] == "sekai真抽卡":
            if event.self_id not in mainbot:
                return
            if event.group_id in blacklist['ettm']:
                return
            if event.user_id not in whitelist and event.group_id not in whitelist:
                nowtime = f"{str(datetime.now().hour).zfill(2)}{str(datetime.now().minute).zfill(2)}"
                lasttime = gachalimit['lasttime']
                count = gachalimit['count']
                if nowtime == lasttime and count >= 2:
                    sendmsg(event, f'技能冷却中，剩余cd:{60 - datetime.now().second}秒（一分钟内所有群只能抽两次）')
                    return
                gachalimit['lasttime'] = nowtime
                gachalimit['count'] = count + 1
            sendmsg(event, '了解')
            gachaid = event.message[event.message.find("sekai真抽卡") + len("sekai真抽卡"):].strip()
            if gachaid == '':
                result = gacha()
            else:
                currentgacha = getallcurrentgacha()
                targetgacha = None
                for gachas in currentgacha:
                    if int(gachas['id']) == int(gachaid):
                        targetgacha = gachas
                        break
                if targetgacha is None:
                    sendmsg(event, '你指定的id现在无法完成无偿十连')
                    return
                else:
                    result = gacha(targetgacha)
            sendmsg(event, result)
            return
        if event.message == "sk预测":
            texttoimg(skyc(), 500, 'skyc')
            sendmsg(event, 'sk预测' + fr"[CQ:image,file=file:///{botdir}\piccache\skyc.png,cache=0]")
            return
        if event.message[:2] == "sk":
            if event.group_id in blacklist['sk']:
                return
            if event.message == "sk":
                bind = getqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                result = sk(bind[1], None, bind[2])
                sendmsg(event, result)
            else:
                userid = event.message.replace("sk", "")
                userid = re.sub(r'\D', "", userid)
                if userid == '':
                    sendmsg(event, '你这id有问题啊')
                    return
                if int(userid) > 10000000:
                    result = sk(userid)
                else:
                    result = sk(None, userid)
                sendmsg(event, result)
                return
        if event.message[:2] == "rk":
            if event.message == "rk":
                bind = getqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                result = rk(bind[1], None, bind[2])
                sendmsg(event, result)
            else:
                userid = event.message.replace("rk", "")
                userid = re.sub(r'\D', "", userid)
                if userid == '':
                    sendmsg(event, '你这id有问题啊')
                    return
                if int(userid) > 10000000:
                    result = rk(userid)
                else:
                    result = rk(None, userid)
                sendmsg(event, result)
            return
        if event.message[:2] == "绑定":
            userid = event.message.replace("绑定", "")
            userid = re.sub(r'\D', "", userid)
            sendmsg(event, bindid(event.user_id, userid))
            return
        if event.message == "不给看":
            if setprivate(event.user_id, 1):
                sendmsg(event, '不给看！')
            else:
                sendmsg(event, '你还没有绑定哦')
            return
        if event.message == "给看":
            if setprivate(event.user_id, 0):
                sendmsg(event, '给看！')
            else:
                sendmsg(event, '你还没有绑定哦')
            return
        if event.message[:2] == "逮捕":
            if event.group_id in blacklist['sk']:
                return
            if event.message == "逮捕":
                bind = getqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '查不到捏，可能是没绑定')
                    return
                result = daibu(bind[1], bind[2])
                sendmsg(event, result)
            else:
                userid = event.message.replace("逮捕", "")
                if '[CQ:at' in userid:
                    qq = re.sub(r'\D', "", userid)
                    bind = getqqbind(qq)
                    if bind is None:
                        sendmsg(event, '查不到捏，可能是没绑定')
                        return
                    elif bind[2] and qq != str(event.user_id):
                        sendmsg(event, '查不到捏，可能是不给看')
                        return
                    else:
                        result = daibu(bind[1], bind[2])
                        sendmsg(event, result)
                        return
                userid = re.sub(r'\D', "", userid)
                if userid == '':
                    sendmsg(event, '你这id有问题啊')
                    return
                if int(userid) > 10000000:
                    result = daibu(userid)
                else:
                    result = daibu(userid)
                sendmsg(event, result)
            return
        if event.message == "pjsk进度":
            bind = getqqbind(event.user_id)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskjindu(bind[1], bind[2])
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if event.message == "pjsk进度ex":
            bind = getqqbind(event.user_id)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskjindu(bind[1], bind[2], 'expert')
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if event.message == "pjsk b30":
            bind = getqqbind(event.user_id)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskb30(bind[1], bind[2])
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}b30.png,cache=0]")
            return
        try:
            if event.message == "热度排行":
                hotrank()
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\hotrank.png,cache=0]")
                return
            if "难度排行" in event.message:
                if event.message[:2] == 'fc':
                    fcap = 1
                elif event.message[:2] == 'ap':
                    fcap = 2
                else:
                    fcap = 0
                event.message = event.message[event.message.find("难度排行") + len("难度排行"):].strip()
                para = event.message.split(" ")
                if len(para) == 1:
                    success = levelrank(int(event.message), 'master', fcap)
                else:
                    success = levelrank(int(para[0]), para[1], fcap)
                if success:
                    if len(para) == 1:
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{para[0]}master{fcap}.png,cache=0]")
                    else:
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{para[0]}{para[1]}{fcap}.png,cache=0]")
                else:
                    sendmsg(event, '参数错误，指令：/难度排行 定数 难度，'
                                   '难度支持的输入: easy, normal, hard, expert, master，如/难度排行 28 expert')
                return
        except:
            sendmsg(event, '参数错误，指令：/难度排行 定数 难度，'
                           '难度支持的输入: easy, normal, hard, expert, master，如/难度排行 28 expert')
        if event.message == "pjskprofile" or event.message == "个人信息":
            bind = getqqbind(event.user_id)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskprofile(bind[1], bind[2])
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}profile.png,cache=0]")
            return
        if event.message[:7] == 'pjskbpm':
            parm = event.message[event.message.find("bpm") + len("bpm"):].strip()
            resp = aliastomusicid(parm)
            if resp['musicid'] == 0:
                sendmsg(event, '没有找到你要的歌曲哦')
                return
            else:
                bpm = parse_bpm(resp['musicid'])
                text = ''
                for bpms in bpm[1]:
                    text = text + ' - ' + str(bpms['bpm']).replace('.0', '')
                text = f"{resp['name']}\n匹配度:{round(resp['match'], 4)}\nBPM: " + text[3:]
                sendmsg(event, text)
            return
        if "谱面预览2" in event.message:
            picdir = aliastochart(event.message.replace("谱面预览2", ''), True)
            if picdir is not None:  # 匹配到歌曲
                if len(picdir) == 2:  # 有图片
                    sendmsg(event, picdir[0] + fr"[CQ:image,file=file:///{botdir}\{picdir[1]},cache=0]")
                else:
                    sendmsg(event, picdir + "\n暂无谱面图片 请等待更新"
                                            "\n（温馨提示：谱面预览2只能看master与expert）")
            else:  # 匹配不到歌曲
                sendmsg(event, "没有找到你说的歌曲哦")
            return
        if event.message[:4] == "谱面预览" or event.message[-4:] == "谱面预览" :
            picdir = aliastochart(event.message.replace("谱面预览", ''), False, True)
            if picdir is not None:  # 匹配到歌曲
                if len(picdir) == 2:  # 有图片
                    sendmsg(event, picdir[0] + fr"[CQ:image,file=file:///{botdir}\{picdir[1]},cache=0]")
                elif picdir == '':
                    return
                else:
                    sendmsg(event, picdir + "\n暂无谱面图片 请等待更新")
            else:  # 匹配不到歌曲
                sendmsg(event, "没有找到你说的歌曲哦")
            return
        if "查时间" in event.message:
            userid = event.message[event.message.find("查时间") + len("查时间"):].strip()
            if userid == '':
                bind = getqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                userid = bind[1]
            userid = re.sub(r'\D', "", userid)
            if userid == '':
                sendmsg(event, '你这id有问题啊')
                return
            if verifyid(userid):
                sendmsg(event, time.strftime('注册时间：%Y-%m-%d %H:%M:%S',
                                             time.localtime(gettime(userid))))
            else:
                sendmsg(event, '你这id有问题啊')
            return
        if event.message[:8] == 'charaset' and 'to' in event.message:
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
            event.message = event.message[8:]
            para = event.message.split('to')
            info = bot.sync.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
            if info['card'] == '':
                username = info['nickname']
            else:
                username = info['card']
            qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
            sendmsg(event, charaset(para[0], para[1], event.user_id, username, f"{qun['group_name']}({event.group_id})内"))
            return
        if event.message[:10] == 'grcharaset' and 'to' in event.message:
            event.message = event.message[10:]
            para = event.message.split('to')
            sendmsg(event, grcharaset(para[0], para[1], event.group_id))
            return
        if event.message[:8] == 'charadel':
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
            event.message = event.message[8:]
            info = bot.sync.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
            if info['card'] == '':
                username = info['nickname']
            else:
                username = info['card']
            qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
            sendmsg(event, charadel(event.message, event.user_id, username, f"{qun['group_name']}({event.group_id})内"))
            return
        if event.message[:10] == 'grcharadel':
            event.message = event.message[10:]
            sendmsg(event, grcharadel(event.message, event.group_id))
            return
        if event.message[:9] == 'charainfo':
            event.message = event.message[9:]
            sendmsg(event, charainfo(event.message, event.group_id))
            return
        if event.message == '看33':
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\pics/33{random.randint(0, 1)}.gif,cache=0]")
            return
        if event.message[:1] == '看' or event.message[:2] == '来点':
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            event.message = event.message.replace('看', '')
            event.message = event.message.replace('来点', '')
            resp = aliastocharaid(event.message, event.group_id)
            if resp[0] != 0:
                cardurl = get_card(resp[0])
                if 'cutout' not in cardurl:
                    cardurl = cardurl.replace('png', 'jpg')
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{cardurl},cache=0]")
            return
        if event.message == '推车':
            ycmimg()
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\ycm.png,cache=0]")
            return
        if event.message[:2] == "生成":
            if event.group_id in blacklist['ettm']:
                return
            event.message = event.message[event.message.find("生成") + len("生成"):].strip()
            para = event.message.split(" ")
            now = int(time.time() * 1000)
            if len(para) < 2:
                para = event.message.split("/")
                if len(para) < 2:
                    sendmsg(event, '请求不对哦，/生成 这是红字 这是白字')
                    return
            genImage(para[0], para[1]).save(f"piccache/{now}.png")
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{now}.png,cache=0]")
            return
        if event.message[:4] == 'homo':
            if event.self_id not in mainbot:
                return
            if event.group_id in blacklist['ettm']:
                return
            event.message = event.message[event.message.find("homo") + len("homo"):].strip()
            try:
                sendmsg(event, event.message + '=' + generate_homo(event.message))
            except ValueError:
                return
            return
        if event.message[:3] == "ccf":
            if event.self_id not in mainbot:
                return
            if event.group_id in blacklist['ettm']:
                return
            event.message = event.message[event.message.find("ccf") + len("ccf"):].strip()
            dd = dd_query.DDImageGenerate(event.message)
            image_path, vtb_following_count, total_following_count = dd.image_generate()
            sendmsg(event, f"{dd.username} 总共关注了 {total_following_count} 位up主, 其中 {vtb_following_count} 位是vtb。\n"
                           f"注意: 由于b站限制, bot最多只能拉取到最近250个关注。因此可能存在数据统计不全的问题。"
                    + fr"[CQ:image,file=file:///{image_path},cache=0]")
            return
        if event.message[:5] == "白名单添加" and event.user_id in admin:
            event.message = event.message[event.message.find("白名单添加") + len("白名单添加"):].strip()
            requestwhitelist.append(int(event.message))
            sendmsg(event, '添加成功: ' + event.message)
            return
        if event.message[:3] == "达成率":
            event.message = event.message[event.message.find("达成率") + len("达成率"):].strip()
            para = event.message.split(' ')
            if len(para) < 5:
                return
            sendmsg(event, tasseiritsu(para))
            return
        if event.message[:2] == '机翻' and event.message[-2:] == '推特':
            if event.self_id not in mainbot:
                return
            if '最新' in event.message:
                event.message = event.message.replace('最新', '')
            twiid = event.message[2:-2]
            try:
                twiid = newesttwi(twiid, True)
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache/{twiid}.png,cache=0]")
            except:
                sendmsg(event, '查不到捏，可能是你id有问题或者bot卡了')
            return
        if event.message[-4:] == '最新推特':
            if event.self_id not in mainbot:
                return
            try:
                twiid = newesttwi(event.message.replace('最新推特', '').replace(' ', ''))
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache/{twiid}.png,cache=0]")
            except:
                sendmsg(event, '查不到捏，可能是你id有问题或者bot卡了')
            return
        if event.message[:3] == '查物量':
            sendmsg(event, notecount(int(event.message[3:])))
            return
        if event.message[:4] == '查bpm':
            sendmsg(event, findbpm(int(event.message[4:])))
            return
        if 'pjsk抽卡' in event.message or 'sekai抽卡' in event.message:
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            gachaid = event.message[event.message.find("抽卡") + len("抽卡"):].strip()
            gachaid = re.sub(r'\D', "", gachaid)
            if gachaid == '':
                currentgacha = getcurrentgacha()
                sendmsg(event, fakegacha(int(currentgacha['id']), 10, False))
            else:
                sendmsg(event, fakegacha(int(gachaid), 10, False))
            return
        if 'pjsk反抽卡' in event.message or 'sekai反抽卡' in event.message:
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            gachaid = event.message[event.message.find("抽卡") + len("抽卡"):].strip()
            gachaid = re.sub(r'\D', "", gachaid)
            if gachaid == '':
                currentgacha = getcurrentgacha()
                sendmsg(event, fakegacha(int(currentgacha['id']), 10, True))
            else:
                sendmsg(event, fakegacha(int(gachaid), 10, True))
            return
        if (event.message[0:5] == 'sekai' or event.message[0:4] == 'pjsk') and '连' in event.message:
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            gachaid = event.message[event.message.find("连") + len("连"):].strip()
            num = event.message[:event.message.find('连')].replace('sekai', '').replace('pjsk', '')
            num = re.sub(r'\D', "", num)
            if int(num) > 400:
                sendmsg(event, '太多了，少抽一点吧！')
                return
            if gachaid == '':
                currentgacha = getcurrentgacha()
                sendmsg(event, fakegacha(int(currentgacha['id']), int(num), False))
            else:
                sendmsg(event, fakegacha(int(gachaid), int(num), False))
            return

        # 以下为台服内容
        if event.user_id in whitelist or event.group_id in whitelist:
            if event.message[:4] == "twsk":
                if event.message == "twsk":
                    bind = twgetqqbind(event.user_id)
                    if bind is None:
                        sendmsg(event, '你没有绑定id！')
                        return
                    result = twsk(bind[1], None, bind[2])
                    sendmsg(event, result)
                else:
                    userid = event.message.replace("sk", "")
                    userid = re.sub(r'\D', "", userid)
                    if userid == '':
                        sendmsg(event, '你这id有问题啊')
                        return
                    if int(userid) > 10000000:
                        result = twsk(userid)
                    else:
                        result = twsk(None, userid)
                    sendmsg(event, result)
                    return
            if event.message[:6] == "twbind" or event.message[:4] == "tw绑定":
                userid = event.message.replace("twbind", "").replace("tw绑定", "")
                userid = re.sub(r'\D', "", userid)
                sendmsg(event, twbindid(event.user_id, userid))
                return
            if event.message == "tw不给看":
                if twsetprivate(event.user_id, 1):
                    sendmsg(event, '不给看！')
                else:
                    sendmsg(event, '你还没有绑定哦')
                return
            if event.message == "tw给看":
                if twsetprivate(event.user_id, 0):
                    sendmsg(event, '给看！')
                else:
                    sendmsg(event, '你还没有绑定哦')
                return
            if event.message[:10] == 'twpjskinfo':
                resp = twaliastomusicid(event.message[event.message.find("pjskinfo") + len("pjskinfo"):].strip())
                if resp['musicid'] == 0:
                    sendmsg(event, '没有找到你要的歌曲哦')
                    return
                else:
                    leak = twdrawpjskinfo(resp['musicid'])
                    if resp['match'] < 0.8:
                        text = '你要找的可能是：'
                    else:
                        text = ""
                    if leak:
                        text = text + f"匹配度:{round(resp['match'], 4)}\n⚠该内容为剧透内容"
                    else:
                        if resp['translate'] == '':
                            text = text + f"{resp['name']}\n匹配度:{round(resp['match'], 4)}"
                        else:
                            text = text + f"{resp['name']} ({resp['translate']})\n匹配度:{round(resp['match'], 4)}"
                    sendmsg(event,
                            text + fr"[CQ:image,file=file:///{botdir}\piccache\enpjskinfo{resp['musicid']}.png,cache=0]")
                return
            if event.message[:4] == "tw逮捕":
                if event.message == "tw逮捕":
                    bind = twgetqqbind(event.user_id)
                    if bind is None:
                        sendmsg(event, '查不到捏，可能是没绑定')
                        return
                    result = twdaibu(bind[1], bind[2])
                    sendmsg(event, result)
                else:
                    userid = event.message.replace("逮捕", "")
                    if '[CQ:at' in userid:
                        qq = re.sub(r'\D', "", userid)
                        bind = twgetqqbind(qq)
                        if bind is None:
                            sendmsg(event, '查不到捏，可能是没绑定')
                            return
                        elif bind[2] and qq != str(event.user_id):
                            sendmsg(event, '查不到捏，可能是不给看')
                            return
                        else:
                            result = twdaibu(bind[1], bind[2])
                            sendmsg(event, result)
                            return
                    userid = re.sub(r'\D', "", userid)
                    if userid == '':
                        sendmsg(event, '你这id有问题啊')
                        return
                    result = twdaibu(userid)
                    sendmsg(event, result)
                return
            if event.message == "twpjsk进度":
                bind = twgetqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '查不到捏，可能是没绑定')
                    return
                twpjskjindu(bind[1], bind[2])
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
                return
            if event.message == "twpjsk进度ex":
                bind = twgetqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '查不到捏，可能是没绑定')
                    return
                twpjskjindu(bind[1], bind[2], 'expert')
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
                return
            if event.message == "twpjsk b30":
                bind = twgetqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '查不到捏，可能是没绑定')
                    return
                twpjskb30(bind[1], bind[2])
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}b30.png,cache=0]")
                return
            if event.message == "twpjskprofile":
                bind = twgetqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '查不到捏，可能是没绑定')
                    return
                twpjskprofile(bind[1], bind[2])
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}profile.png,cache=0]")
                return
        # 以下为国际服内容

        if event.message[:4] == "ensk":
            if event.message == "ensk":
                bind = engetqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                result = ensk(bind[1], None, bind[2])
                sendmsg(event, result)
            else:
                userid = event.message.replace("sk", "")
                userid = re.sub(r'\D', "", userid)
                if userid == '':
                    sendmsg(event, '你这id有问题啊')
                    return
                if int(userid) > 10000000:
                    result = ensk(userid)
                else:
                    result = ensk(None, userid)
                sendmsg(event, result)
                return
        if event.message[:6] == "enbind" or event.message[:4] == "en绑定":
            userid = event.message.replace("enbind", "").replace("en绑定", "")
            userid = re.sub(r'\D', "", userid)
            sendmsg(event, enbindid(event.user_id, userid))
            return
        if event.message == "en不给看":
            if ensetprivate(event.user_id, 1):
                sendmsg(event, '不给看！')
            else:
                sendmsg(event, '你还没有绑定哦')
            return
        if event.message == "en给看":
            if ensetprivate(event.user_id, 0):
                sendmsg(event, '给看！')
            else:
                sendmsg(event, '你还没有绑定哦')
            return
        if event.message[:10] == 'enpjskinfo':
            resp = enaliastomusicid(event.message[event.message.find("pjskinfo") + len("pjskinfo"):].strip())
            if resp['musicid'] == 0:
                sendmsg(event, '没有找到你要的歌曲哦')
                return
            else:
                leak = endrawpjskinfo(resp['musicid'])
                if resp['match'] < 0.8:
                    text = '你要找的可能是：'
                else:
                    text = ""
                if leak:
                    text = text + f"匹配度:{round(resp['match'], 4)}\n⚠该内容为剧透内容"
                else:
                    if resp['translate'] == '':
                        text = text + f"{resp['name']}\n匹配度:{round(resp['match'], 4)}"
                    else:
                        text = text + f"{resp['name']} ({resp['translate']})\n匹配度:{round(resp['match'], 4)}"
                sendmsg(event,
                        text + fr"[CQ:image,file=file:///{botdir}\piccache\enpjskinfo{resp['musicid']}.png,cache=0]")
            return
        if event.message[:4] == "en逮捕":
            if event.message == "en逮捕":
                bind = engetqqbind(event.user_id)
                if bind is None:
                    sendmsg(event, '查不到捏，可能是没绑定')
                    return
                result = endaibu(bind[1], bind[2])
                sendmsg(event, result)
            else:
                userid = event.message.replace("逮捕", "")
                if '[CQ:at' in userid:
                    qq = re.sub(r'\D', "", userid)
                    bind = engetqqbind(qq)
                    if bind is None:
                        sendmsg(event, '查不到捏，可能是没绑定')
                        return
                    elif bind[2] and qq != str(event.user_id):
                        sendmsg(event, '查不到捏，可能是不给看')
                        return
                    else:
                        result = endaibu(bind[1], bind[2])
                        sendmsg(event, result)
                        return
                userid = re.sub(r'\D', "", userid)
                if userid == '':
                    sendmsg(event, '你这id有问题啊')
                    return
                result = endaibu(userid)
                sendmsg(event, result)
            return
        if event.message == "enpjsk进度":
            bind = engetqqbind(event.user_id)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            enpjskjindu(bind[1], bind[2])
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if event.message == "enpjsk进度ex":
            bind = engetqqbind(event.user_id)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            enpjskjindu(bind[1], bind[2], 'expert')
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if event.message == "enpjsk b30":
            bind = engetqqbind(event.user_id)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            enpjskb30(bind[1], bind[2])
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}b30.png,cache=0]")
            return
        if event.message == "enpjskprofile":
            bind = engetqqbind(event.user_id)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            enpjskprofile(bind[1], bind[2])
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}profile.png,cache=0]")
            return

        # 猜曲
        if event.message[-2:] == '猜曲' and event.message[:4] == 'pjsk':
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜卡面！')
                    return
            except KeyError:
                pass

            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
                else:
                    musicid = getrandomjacket()
                    pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid,
                                                 'starttime': int(time.time())}
            except KeyError:
                musicid = getrandomjacket()
                pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid, 'starttime': int(time.time())}
            if event.message == 'pjsk猜曲':
                cutjacket(musicid, event.group_id, size=140, isbw=False)
            elif event.message == 'pjsk阴间猜曲':
                cutjacket(musicid, event.group_id, size=140, isbw=True)
            elif event.message == 'pjsk非人类猜曲':
                cutjacket(musicid, event.group_id, size=30, isbw=False)
            sendmsg(event, 'PJSK曲绘竞猜 （随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有50秒的时间回答\n可手动发送“结束猜曲”来结束猜曲'
                    + fr"[CQ:image,file=file:///{botdir}\piccache/{event.group_id}.png,cache=0]")
            return
        if event.message == 'pjsk猜谱面':
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜卡面！')
                    return
            except KeyError:
                pass

            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
                else:
                    musicid = getrandomchart()
                    pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid,
                                                 'starttime': int(time.time())}
            except KeyError:
                musicid = getrandomchart()
                pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid, 'starttime': int(time.time())}
            cutchartimg(musicid, event.group_id)
            sendmsg(event, 'PJSK谱面竞猜（随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有50秒的时间回答\n可手动发送“结束猜曲”来结束猜曲'
                    + fr"[CQ:image,file=file:///{botdir}\piccache/{event.group_id}.png,cache=0]")
            return
        if event.message == 'pjsk猜卡面':
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
            except KeyError:
                pass
            # getrandomcard() return characterId, assetbundleName, prefix, cardRarityType
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
                else:
                    cardinfo = getrandomcard()
                    charaguess[event.group_id] = {'isgoing': True, 'charaid': cardinfo[0],
                                                  'assetbundleName': cardinfo[1], 'prefix': cardinfo[2],
                                                  'starttime': int(time.time())}
            except KeyError:
                cardinfo = getrandomcard()
                charaguess[event.group_id] = {'isgoing': True, 'charaid': cardinfo[0],
                                              'assetbundleName': cardinfo[1],
                                              'prefix': cardinfo[2], 'starttime': int(time.time())}

            charaguess[event.group_id]['istrained'] = cutcard(cardinfo[1], cardinfo[3], event.group_id)
            sendmsg(event, 'PJSK猜卡面\n你有30秒的时间回答\n艾特我+你的答案（只猜角色）以参加猜曲（不要使用回复）\n发送「结束猜卡面」可退出猜卡面模式'
                    + fr"[CQ:image,file=file:///{botdir}\piccache/{event.group_id}.png,cache=0]")
            print(charaguess)
            return
        if event.message == '结束猜曲':
            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    picdir = f"data/assets/sekai/assetbundle/resources/startapp/music/jacket/" \
                             f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}/" \
                             f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}.png"
                    text = '正确答案：' + idtoname(pjskguess[event.group_id]['musicid'])
                    pjskguess[event.group_id]['isgoing'] = False
                    sendmsg(event, text + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
            except KeyError:
                pass
            return
        if event.message == '结束猜卡面':
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    if charaguess[event.group_id]['istrained']:
                        picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                 f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_after_training.jpg"
                    else:
                        picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                 f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_normal.jpg"
                    text = f"正确答案：{charaguess[event.group_id]['prefix']} - {getcharaname(charaguess[event.group_id]['charaid'])}"
                    charaguess[event.group_id]['isgoing'] = False

                    sendmsg(event, text + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
            except KeyError:
                pass
            return
        # 判断艾特自己
        if f'[CQ:at,qq={event.self_id}]' in event.message:
            # 判断有没有猜曲
            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    answer = event.message[event.message.find("]") + len("]"):].strip()
                    resp = aliastomusicid(answer)
                    if resp['musicid'] == 0:
                        sendmsg(event, '没有找到你说的歌曲哦')
                        return
                    else:
                        if resp['musicid'] == pjskguess[event.group_id]['musicid']:
                            text = f'[CQ:at,qq={event.user_id}] 您猜对了'
                            if int(time.time()) > pjskguess[event.group_id]['starttime'] + 45:
                                text = text + '，回答已超时'
                            picdir = f"data/assets/sekai/assetbundle/resources/startapp/music/jacket/" \
                                     f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}/" \
                                     f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}.png"
                            text = text + '\n正确答案：' + idtoname(pjskguess[event.group_id]['musicid'])
                            pjskguess[event.group_id]['isgoing'] = False
                            sendmsg(event, text + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                        else:
                            sendmsg(event, f"[CQ:at,qq={event.user_id}] 您猜错了，答案不是{idtoname(resp['musicid'])}哦")
                    return
            except KeyError:
                pass
            # 判断有没有猜卡面
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    # {'isgoing', 'charaid', 'assetbundleName', 'prefix', 'starttime'}
                    answer = event.message[event.message.find("]") + len("]"):].strip()
                    resp = aliastocharaid(answer)
                    if resp[0] == 0:
                        sendmsg(event, '没有找到你说的角色哦')
                        return
                    else:
                        if resp[0] == charaguess[event.group_id]['charaid']:
                            text = f'[CQ:at,qq={event.user_id}] 您猜对了'
                            if int(time.time()) > charaguess[event.group_id]['starttime'] + 45:
                                text = text + '，回答已超时'
                            if charaguess[event.group_id]['istrained']:
                                picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                         f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_after_training.jpg"
                            else:
                                picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                         f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_normal.jpg"
                            text = text + f"\n正确答案：{charaguess[event.group_id]['prefix']} - {resp[1]}"
                            charaguess[event.group_id]['isgoing'] = False
                            sendmsg(event, text + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                        else:
                            sendmsg(event, f"[CQ:at,qq={event.user_id}] 您猜错了，答案不是{resp[1]}哦")
                    return
            except KeyError:
                pass
            sendmsg(event, 'bot帮助文档：https://docs.unipjsk.com/')
            return
    except (requests.exceptions.ConnectionError, JSONDecodeError):
        sendmsg(event, '查不到数据捏，好像是bot网不好')
    except Exception as a:
        traceback.print_exc()
        sendmsg(event, '出问题了捏\n' + repr(a))


def sendmsg(event, msg):
    global send1
    global send3
    timeArray = time.localtime(time.time())
    Time = time.strftime("\n[%Y-%m-%d %H:%M:%S]", timeArray)
    try:
        print(Time, botname[event.self_id] + '收到命令', event.group_id, event.user_id, event.message.replace('\n', ''))
    except KeyError:
        print(Time, '测试bot收到命令', event.group_id, event.user_id, event.message.replace('\n', ''))
    print(botname[event.self_id] + '发送群消息', event.group_id, msg.replace('\n', ''))
    try:
        bot.sync.send_group_msg(self_id=event.self_id, group_id=event.group_id, message=msg)
        if event.self_id == 1513705608:
            send1 = False
        elif event.self_id == 3506606538:
            send3 = False
    except aiocqhttp.exceptions.ActionFailed:
        if event.self_id == 1513705608:
            print('一号机发送失败')
            if send1 is not True:
                print('即将发送告警邮件')
                sendemail(botname[event.self_id] + '群消息发送失败', str(event.group_id) + msg)
                send1 = True
            else:
                print('告警邮件发过了')
        elif event.self_id == 3506606538:
            print('三号机发送失败')
            if send3 is not True:
                print('即将发送告警邮件')
                sendemail(botname[event.self_id] + '群消息发送失败', str(event.group_id) + msg)
                send3 = True
            else:
                print('告警邮件发过了')


@bot.on_notice('group_increase')  # 群人数增加事件
async def handle_group_increase(event: Event):
    if event.user_id == event.self_id:  # 自己被邀请进群
        if event.group_id in requestwhitelist:
            await bot.send_group_msg(self_id=event.self_id, group_id=msggroup, message=f'我已加入群{event.group_id}')
        else:
            await bot.send_group_msg(self_id=event.self_id, group_id=event.group_id, message='未经审核的邀请，已自动退群')
            await bot.set_group_leave(self_id=event.self_id, group_id=event.group_id)
            await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                     message=f'有人邀请我加入群{event.group_id}，已自动退群')


@bot.on_request('group')  # 加群请求或被拉群
async def handle_group_request(event: Event):
    print(event.sub_type, event.message)
    if event.sub_type == 'invite':  # 被邀请加群
        if event.group_id in requestwhitelist:
            await bot.set_group_add_request(self_id=event.self_id, flag=event.flag, sub_type=event.sub_type,
                                            approve=True)
            await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                     message=f'{event.user_id}邀请我加入群{event.group_id}，已自动同意')
        else:
            await bot.set_group_add_request(self_id=event.self_id, flag=event.flag, sub_type=event.sub_type,
                                            approve=False)
            await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                     message=f'{event.user_id}邀请我加入群{event.group_id}，已自动拒绝')
    elif event.sub_type == 'add':  # 有人加群
        if event.group_id == 883721511 or event.group_id == 647347636:
            answer = event.comment[event.comment.find("答案：") + len("答案："):].strip()
            answer = re.sub(r'\D', "", answer)
            async with aiofiles.open('masterdata/musics.json', 'r', encoding='utf-8') as f:
                contents = await f.read()
            musics = json.loads(contents)
            now = time.time() * 1000
            count = 0
            for music in musics:
                if music['publishedAt'] < now:
                    count += 1
            print(count)
            if count - 5 < int(answer) < count + 5:
                await bot.set_group_add_request(self_id=event.self_id, flag=event.flag, sub_type=event.sub_type,
                                                approve=True)
                await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                         message=f'{event.user_id}申请加群\n{event.comment}\n误差<5，已自动通过')
            else:
                await bot.set_group_add_request(self_id=event.self_id, flag=event.flag, sub_type=event.sub_type,
                                                approve=False, reason='回答错误，请认真回答(使用阿拉伯数字)')
                await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                         message=f'{event.user_id}申请加群\n{event.comment}\n误差>5，已自动拒绝')
        elif event.group_id == 467602419:
            answer = event.comment[event.comment.find("答案：") + len("答案："):].strip()
            if 'Mrs4s/go-cqhttp' in answer:
                await bot.set_group_add_request(self_id=event.self_id, flag=event.flag, sub_type=event.sub_type,
                                                approve=True)
                await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                         message=f'{event.user_id}申请加群\n{event.comment}\n已自动通过')
            else:
                await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                         message=f'{event.user_id}申请加群\n{event.comment}\n，无法判定')


@bot.on_notice('group_ban')
async def handle_group_ban(event: Event):
    if event.user_id == event.self_id:
        await bot.set_group_leave(self_id=event.self_id, group_id=event.group_id)
        await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                 message=f'我在群{event.group_id}内被{event.operator_id}禁言{event.duration / 60}分钟，已自动退群')


with open('yamls/blacklist.yaml', "r") as f:
    blacklist = yaml.load(f, Loader=yaml.FullLoader)
bot.run(host='127.0.0.1', port=1234, debug=False)
