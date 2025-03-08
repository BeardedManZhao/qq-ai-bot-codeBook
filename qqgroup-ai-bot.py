# -*- coding: utf-8 -*-
# 请直接运行此文件
import json
import logging
import os
import sys
import traceback

import botpy
import jieba
from botpy import Intents
from botpy.ext.cog_yaml import read

from utils import HttpClient, CommandHandler, StrUtils
from utils import TimeBoundedList

# 通过sys模块的argv属性获取命令行参数
args = sys.argv
if len(args) == 1:
    args.append(input("请输入要使用的配置文件的路径，然后回车: ").replace('\\', '/'))

# 第一个参数为脚本文件的名称，从第二个参数开始为输入参数
input_params = args[1:]

# 配置文件加载
test_config = read(os.path.join(os.path.dirname(__file__), input_params[0]))
# 提取配置文件名字
path = input_params[0].split('/')
# 创建一个文件处理器，将日志写入指定文件
logger = logging.getLogger("chatLogger")
logger.setLevel(logging.DEBUG)  # 设置最低的日志级别
# 文件处理
file_handler = logging.FileHandler(f'chat_{path[len(path) - 1]}.log')
# 定义日志消息的格式
formatter = logging.Formatter('%(message)s')
# 给文件处理器设置格式
file_handler.setFormatter(formatter)
# 将文件处理器添加到logger对象中
logger.addHandler(file_handler)
# 设置文件处理器的日志级别
file_handler.setLevel(logging.DEBUG)

# 设置您码本API 的id和sk
server_id = test_config['model_server_id']
server_sk = test_config['model_server_sk']
url = (f"https://api.get.lingyuzhao.top:8081/api/chat/?"
       f"id={server_id}"
       f"&sk={server_sk}"
       f"&type={test_config['model_server_type']}"
       f"&model={test_config['model_server_model']}")

# 构建http客户端
http_client = HttpClient()

# 构建翻译官API链接
translate_url = (f"https://api.get.lingyuzhao.top:8081/api/translate?"
                 f"sk={test_config['translate_server_sk']}&id={test_config['translate_server_id']}")

# 查看是否允许模型调用
need_hidden_module = test_config['needHiddenModule']


async def translate_string(src_lang, tar_lang, translate_str):
    return await http_client.fetch_text(
        f"{translate_url}&str={translate_str}&srcLang={src_lang}&targetLang={tar_lang}")


def clean(history_chats, message_id):
    """
    清理消息记录
    :param history_chats: 这个是消息列表
    :param message_id: 消息记录对应的 id
    :return: 处理成功的消息
    """
    history_chats[message_id] = TimeBoundedList(
        ttl=test_config['userMessageMaxTtl'], max_size=test_config['groupMessageMaxLen']
    )
    return f"清理空间：【{StrUtils.desensitization(message_id)}】的数据成功！"


def command_get_current_time_formatted(string, list_args, message_list_id):
    return f"当前时间：{StrUtils.get_current_time_formatted()}"


def command_args_string(string, list_args, message_list_id):
    return f"输入参数：{string}\n参数列表：{list_args}"


async def command_translate_string(string, list_args, message_list_id):
    if len(list_args) < 3:
        return ("语法错误啦，您应该这样输入哦！\n/翻译 源语言 目标语言 这个就是要翻译的文本\n"
                "====语言支持====\n"
                """语言	简写	全小写	完全语法
日语: ja jp Japanese
中文: zh cn Mandarin
英文: en us English
法语: fr french French
西班牙语: es	spain Spanish
德语: de germany German
韩语: ko korea Korean
俄语: ru russia Russia
意大利语: it italy Italian
=========
示例：/翻译 zh en 今天真冷呀
""")
    return json.loads(await translate_string(list_args[0], list_args[1], ''.join(list_args[2:])))['message']


# 构建指令处理器
command_handler = CommandHandler({
    "now": command_get_current_time_formatted,
    "testArgs": command_args_string,
    "翻译": command_translate_string
}, {"翻译"})


class MyClient(botpy.Client):
    async def on_ready(self):
        logger.info(f"robot 「{self.robot.name}」 on_ready!")
        await http_client.init_session()

    def __init__(self, intents1: Intents):
        super().__init__(intents1)
        self.history_chats = {}

        # 追加 clean 命令
        def command_clean(string, list_args, message_list_id):
            return clean(self.history_chats, message_list_id)

        command_handler.push_command("清理", command_clean, False)

        # 日志处理
        logger.info(
            f"欢迎您使用 码本API 的 qq机器人服务！\n详细信息请查询：https://www.lingyuzhao.top/b/Article/377388518747589")
        self.lock = asyncio.Lock()  # 添加异步锁防止历史记录冲突

    async def handler_message(self, content, member_openid, message_bot, is_group=False, is_channel=False):
        """
        处理消息
        :param content: 消息
        :param member_openid: 用户id
        :param message_bot: 消息对象
        :param is_group: 是否是群组聊天
        :param is_channel: 是否是频道聊天
        :return:
        """

        # 解析到 id
        real_id = CommandHandler.parse_message_id(member_openid, message_bot, is_group, is_channel)

        content = StrUtils.trim_at_message(content)
        if content == '':
            await message_bot.reply(content=f"😊 在的在的！")
            return
        date_str = StrUtils.get_current_time_formatted()
        try:
            if content[0] == '/':
                # 代表是指令
                logger.info(f"【info】时间：{date_str}; 玩家:{member_openid}; 命令:{content};")
                await message_bot.reply(
                    content=f"😊处理成功\n=========\n{await command_handler.handler(content, real_id)}")
            elif need_hidden_module:
                # 代表隐藏模型功能
                logger.warning(f"用户输入了无法处理的指令：{content}")
                await message_bot.reply(content=f"\U0001F63F 无法处理的指令：{content}")
            else:
                # 保存用户消息
                hc = self.safe_history_update(real_id=real_id, is_group=is_group, message={
                    "role": "user",
                    "content": f"系统消息：当前系统时间：{date_str}；\n\n用户[{member_openid}]的消息：{content}"
                })

                # 异步获取模型 API响应
                resp = await http_client.fetch_model(model_url=url, headers=[], history_chat=hc)
                temp = resp["message"]
                if type(temp) is str:
                    reply_content = StrUtils.get_last_segment(temp)
                    logger.error(f"模型的请求可能出现了错误：{temp}")
                else:
                    reply_content = StrUtils.get_last_segment(temp['content'])

                # 保存回复消息
                self.safe_history_update(real_id=real_id, is_group=is_group, message={
                    "role": "assistant",
                    "content": reply_content
                })

                # 异步发送回复
                await message_bot.reply(content=reply_content)
                logger.info(f"【ok】时间：{date_str}; 玩家:{member_openid}; 消息:{content}; 回复:{reply_content}")

        except Exception as e:
            logger.error(f"处理消息时出错：{str(e)}：{traceback.format_exc()}")
            if need_hidden_module:
                logger.error(f"导致上面异常的命令：【{content}】")
                await message_bot.reply(content=f"""\U0001F63F 处理您的命令时出现错误啦
您可调用的命令
===========
{command_handler.get_commands()}""")
            else:
                await message_bot.reply(content="\U0001F63F 服务器开小差了，请稍后再试～")

    def safe_history_update(self, real_id, is_group, message) -> TimeBoundedList:
        """
        存储一个用户/群的消息 并返回其对应的 TimeBoundedList 对象
        :param real_id:
        :param is_group: 是否是群
        :param message:
        :return: 可以直接操作的 TimeBoundedList
        """
        if is_group:
            # 代表是群消息
            if real_id not in self.history_chats:
                self.history_chats[real_id] = TimeBoundedList(
                    ttl=test_config['userMessageMaxTtl'], max_size=test_config['groupMessageMaxLen']
                )
            res = self.history_chats[real_id]
        else:
            # 代表是个人消息
            if real_id not in self.history_chats:
                self.history_chats[real_id] = TimeBoundedList(
                    ttl=test_config['userMessageMaxTtl'], max_size=test_config['userMessageMaxLen']
                )
            res = self.history_chats[real_id]
        res.append(message)
        return res

    async def on_group_at_message_create(self, message):
        """
        群聊@机器人
        :param message:
        :return:
        """
        await self.handler_message(message.content, message.author.member_openid, message, False)

    async def on_group_message_create(self, message):
        """
        群聊消息全量 不一定可以用
        :param message:
        :return:
        """
        bot_name = test_config['botName']
        if test_config['botName'] in jieba.cut(message.content):
            await self.on_group_at_message_create(message)
        else:
            logger.info(f"未呼叫 {bot_name}")

    async def on_direct_message_create(self, message):
        """
        频道内私信
        :param message: 消息对象·
        :return:
        """
        await self.handler_message(message.content, message.author.username, message)

    async def on_at_message_create(self, message):
        """
        频道所有 @ 消息接受
        :param message:
        :return:
        """
        await self.handler_message(message.content, message.author.username, message)

    async def on_message_create(self, message):
        """
        频道所有消息接受
        :param message:
        :return:
        """
        bot_name = test_config['botName']
        if test_config['botName'] in jieba.cut(message.content):
            await self.handler_message(message.content, message.author.username, message)
        else:
            logger.info(f"未呼叫 {bot_name}")

    async def on_c2c_message_create(self, message):
        """
        私聊
        :param message:
        :return:
        """
        await self.handler_message(message.content,
                                   message.author.user_openid, message)


if __name__ == "__main__":
    import asyncio

    intents = botpy.Intents(public_messages=True, public_guild_messages=True, direct_message=True)
    client = MyClient(intents1=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
