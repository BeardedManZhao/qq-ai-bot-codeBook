# -*- coding: utf-8 -*-
# 请直接运行此文件
import json
import logging
import os
import sys
import traceback
from typing import Any

import botpy
import jieba
from botpy import Intents
from botpy.ext.cog_yaml import read

from utils import HttpClient, CommandHandler, StrUtils, BotUtils
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


def create_url(model_type=test_config['model_server_type'], model=test_config['model_server_model']):
    return (f"https://api.get.lingyuzhao.top:8081/api/chat/?"
            f"id={server_id}"
            f"&sk={server_sk}"
            f"&type={model_type}"
            f"&model={model}")


def create_prompt_url(model_type='none', model=test_config['model_server_model_image']):
    return (f"https://api.get.lingyuzhao.top:8081/api/chat/generate?"
            f"id={server_id}"
            f"&sk={server_sk}"
            f"&type={model_type}"
            f"&model={model}")


def create_group_model_url(model_type=test_config['model_server_type_group'], model=test_config['model_server_model']):
    return create_url(model_type, model)


def create_group_model_prompt_url(model_type='none',
                                  model=test_config['model_server_model_image']):
    return create_prompt_url(model_type, model)


url = create_url()
group_model_url = create_group_model_url()

prompt_url = create_prompt_url(model_type='image_parse')
prompt_group_model_url = create_group_model_prompt_url(model_type='image_parse')

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


def command_get_current_time_formatted(string, list_args, message_list_id, user_openid, is_group):
    return f"当前时间：{StrUtils.get_current_time_formatted()}"


def command_args_string(string, list_args, message_list_id, user_openid, is_group):
    return f"输入参数：{string}\n参数列表：{list_args}"


async def command_translate_string(string, list_args, message_list_id, user_openid, is_group):
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


# 身份查询命令
def command_who_am_i(string, list_args, message_list_id, user_openid, is_group):
    """
    查自己的用户名
    :param user_openid: 可以代表用户个体的 id
    :param string:
    :param list_args:
    :param message_list_id: 需要被转换的 id
    :param is_group: 当前是否处于群，只有群的状态才会缩减自己的用户名
    :return:
    """
    return f"在我的眼中，您的唯一标识【{StrUtils.who_am_i(user_openid, is_group)}】"


# 构建指令处理器
command_handler = CommandHandler({
    "now": command_get_current_time_formatted,
    "testArgs": command_args_string,
    "翻译": command_translate_string,
    "我是谁": command_who_am_i
}, {"翻译"})


class MyClient(botpy.Client):
    async def on_ready(self):
        logger.info(f"robot 「{self.robot.name}」 on_ready!")
        await http_client.init_session()

    def __init__(self, intents1: Intents):
        super().__init__(intents1)
        self.history_chats = {}
        self.handler_message_fun = self.handler_message

        # 追加 clean 命令
        def command_clean(string, list_args, message_list_id, user_openid, is_group):
            return clean(self.history_chats, message_list_id)

        command_handler.push_command("清理", command_clean, False)

        # 设置 model_type 的命令
        def command_set_model_type(string, list_args, message_list_id, user_openid, is_group):
            """
            设置 model_type
            :param user_openid: 可以代表用户个体的 id
            :param string:
            :param list_args:
            :param message_list_id: 需要被转换的 id
            :param is_group: 当前是否处于群，只有群的状态才会缩减自己的用户名
            :return:
            """
            command_clean(string, list_args, message_list_id, user_openid, is_group)
            if len(list_args) <= 1:
                self.history_chats[message_list_id].set_space_model_url(
                    create_url(list_args[0]), create_group_model_url(list_args[0] + '_group')
                )
                return f"已将您所属空间的类型设置为【{list_args[0]}】\n\n此操作可能会更改一些行为，但区别不大，若需要还原请使用命令【/清理】"
            else:
                self.history_chats[message_list_id].set_space_model_url(
                    create_url(list_args[0], list_args[1]),
                    create_group_model_url(list_args[0] + '_group', list_args[1])
                )
                return (f"已将您所属空间的类型设置为【{list_args[0]}】\n\n已将您所属空间的模式设置为【{list_args[1]}】"
                        f"\n\n此操作可能会更改一些大量行为，若需要还原请使用命令【/清理】")

        command_handler.push_command("设置类型", command_set_model_type, False)

        def command_set_stream_by_line(string, list_args, message_list_id, user_openid, is_group):
            if self.handler_message_fun == self.handler_message:
                self.handler_message_fun = self.handler_message_stream
                return f"启用 stream 模式~"
            else:
                self.handler_message_fun = self.handler_message
                return f"关闭 stream 模式~"

        command_handler.push_command("切换流模式", command_set_stream_by_line, False)

        # 日志处理
        logger.info(
            f"欢迎您使用 码本API 的 qq机器人服务！\n详细信息请查询：https://www.lingyuzhao.top/b/Article/-2321317989405261")
        self.lock = asyncio.Lock()  # 添加异步锁防止历史记录冲突

    async def handler_message(self, content, member_openid, user_openid, message_bot, is_group=False, is_channel=False):
        """
        处理消息
        :param content: 消息
        :param member_openid: 可以用来记录消息的 id
        :param user_openid: 可以用来代表用户个体的 id
        :param message_bot: 消息对象
        :param is_group: 是否是群组聊天
        :param is_channel: 是否是频道聊天
        :return:
        """

        # 解析到 id
        real_id = CommandHandler.parse_message_id(member_openid, message_bot, is_group, is_channel)

        # 计算用户的标识
        user_mark = StrUtils.who_am_i(user_openid, is_group)

        # 解析到 附件数据 其是一个 json key是类型 value 是此类型对应的所有 url
        type_file_url = BotUtils.group_attachments_by_type(message_bot)
        # 解析除所有图 url 的base 列表
        images_base = await http_client.urls_to_base64(type_file_url['image'], logger)
        length_is0 = len(images_base) == 0
        content = StrUtils.trim_at_message(content)
        if content == '' and length_is0:
            await message_bot.reply(content=f"😊 在的在的！")
            return
        elif content == '' and not length_is0:
            content = '给你看我发的图片'

        date_str = StrUtils.get_current_time_formatted()
        try:
            if content[0] == '/':
                # 代表是指令
                logger.info(f"【info】时间：{date_str}; 玩家:{member_openid}; 命令:{content};")
                await message_bot.reply(
                    content=f"😊处理成功\n=========\n{await command_handler.handler(content, real_id, user_openid, is_group)}")
            elif need_hidden_module:
                # 代表隐藏模型功能
                logger.warning(f"用户输入了无法处理的指令：{content}")
                await message_bot.reply(content=f"\U0001F63F 无法处理的指令：{content}")
            else:
                # 看看是否有图数据
                if length_is0:
                    # 保存用户消息
                    hc, is_first = self.safe_history_update(real_id=real_id, is_group=is_group, message={
                        "role": "user",
                        "content": f"用户[{user_mark}]的消息（用户名：{user_mark}）：【系统消息：当前系统时间：{date_str}】；\n\n----\n\n{content}",
                        "options": {
                            "temperature": 0.6,
                            "top_p": 0.85,
                            "repeat_penalty": 1.3
                        }
                    })
                else:
                    # 图片解析
                    resp = await http_client.fetch_model_images(
                        model_prompt_url=prompt_url,
                        headers=[],
                        images=images_base
                    )
                    # 保存消息
                    hc, is_first = self.safe_history_update(real_id=real_id, is_group=is_group, message={
                        "role": "user",
                        "content": f"* 系统消息(注意，这不是用户发送的)：当前系统时间：{date_str}\n\n----\n\n"
                                   f"# 用户发送的消息（用户名：{user_mark}）：\n\n----\n\n{content}"
                    })
                    # 保存图像消息
                    self.safe_history_update(real_id=real_id, is_group=is_group, message={
                        "role": "user",
                        "content": f"# 系统消息(注意，这不是用户发送的)\n"
                                   f"> 当前系统时间：{date_str}"
                                   f"\n\n----\n\n"
                                   f"## 关于图片的解析结果：\n{resp['response']}\n\n"
                                   f"# 用户消息(这个是用户发送的消息哦)\n{content}"
                    })

                # 异步获取模型 API响应
                if is_group:
                    resp = await http_client.fetch_model(
                        model_url=hc.get_space_model_url(group_model_url),
                        headers=[],
                        history_chat=hc,
                    )
                else:
                    resp = await http_client.fetch_model(
                        model_url=hc.get_space_model_url(url),
                        headers=[],
                        history_chat=hc,
                    )

                if 'error' in resp:
                    logger.warning(f"模型处理失败：{resp}")
                    return

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

                # 处理回复 并 异步发送回复
                if is_first and is_group:
                    reply_content += f'\n\n----\n\n系统消息：群空间初始化完毕。'
                elif is_first:
                    reply_content += '\n\n----\n\n系统消息：关于更多信息，https://www.lingyuzhao.top/b/Article/-2321317989405261'

                await message_bot.reply(content=reply_content)
                logger.info(
                    f"【ok】时间：{date_str}; realId:{real_id}; 玩家:{user_mark}; 消息:{content}; 回复:{reply_content}")

        except Exception as e:
            logger.error(f"处理消息时出错：{str(e)}：{traceback.format_exc()}")
            if need_hidden_module:
                logger.error(f"导致上面异常的命令：【{content}】")
                await message_bot.reply(content=f"""\U0001F63F 处理您的命令时出现错误啦
您可调用的命令
===========
{command_handler.get_commands()}""")
            else:
                await message_bot.reply(content="\U0001F63F 服务器开小差了，请稍后再试～\n============\n"
                                                "更多信息请查询：https://www.lingyuzhao.top/b/Article/-2321317989405261")

    async def handler_message_stream(self, content, member_openid, user_openid, message_bot, is_group=False,
                                     is_channel=False):
        """
        处理消息
        :param content: 消息
        :param member_openid: 可以用来记录消息的 id
        :param user_openid: 可以用来代表用户个体的 id
        :param message_bot: 消息对象
        :param is_group: 是否是群组聊天
        :param is_channel: 是否是频道聊天
        :return:
        """

        # 解析到 id
        real_id = CommandHandler.parse_message_id(member_openid, message_bot, is_group, is_channel)

        # 计算用户的标识
        user_mark = StrUtils.who_am_i(user_openid, is_group)

        # 解析到 附件数据 其是一个 json key是类型 value 是此类型对应的所有 url
        type_file_url = BotUtils.group_attachments_by_type(message_bot)
        # 解析除所有图 url 的base 列表
        images_base = await http_client.urls_to_base64(type_file_url['image'], logger)
        length_is0 = len(images_base) == 0
        content = StrUtils.trim_at_message(content)
        if content == '' and length_is0:
            await message_bot.reply(content=f"😊 在的在的！")
            return
        elif content == '' and not length_is0:
            content = '给你看我发的图片'

        date_str = StrUtils.get_current_time_formatted()
        try:
            if content[0] == '/':
                # 代表是指令
                logger.info(f"【info】时间：{date_str}; 玩家:{member_openid}; 命令:{content};")
                await message_bot.reply(
                    content=f"😊处理成功\n=========\n{await command_handler.handler(content, real_id, user_openid, is_group)}")
            elif need_hidden_module:
                # 代表隐藏模型功能
                logger.warning(f"用户输入了无法处理的指令：{content}")
                await message_bot.reply(content=f"\U0001F63F 无法处理的指令：{content}")
            else:
                # 看看是否有图数据
                if length_is0:
                    # 保存用户消息
                    hc, is_first = self.safe_history_update(real_id=real_id, is_group=is_group, message={
                        "role": "user",
                        "content": f"用户[{user_mark}]的消息（用户名：{user_mark}）：【系统消息：当前系统时间：{date_str}】；\n\n----\n\n{content}",
                        "options": {
                            "temperature": 0.6,
                            "top_p": 0.85,
                            "repeat_penalty": 1.3
                        }
                    })
                else:
                    # 图片解析
                    resp = await http_client.fetch_model_images(
                        model_prompt_url=prompt_url,
                        headers=[],
                        images=images_base
                    )
                    # 保存消息
                    hc, is_first = self.safe_history_update(real_id=real_id, is_group=is_group, message={
                        "role": "user",
                        "content": f"* 系统消息(注意，这不是用户发送的)：当前系统时间：{date_str}\n\n----\n\n"
                                   f"# 用户发送的消息（用户名：{user_mark}）：\n\n----\n\n{content}"
                    })
                    # 保存图像消息
                    self.safe_history_update(real_id=real_id, is_group=is_group, message={
                        "role": "user",
                        "content": f"# 系统消息(注意，这不是用户发送的)\n"
                                   f"> 当前系统时间：{date_str}"
                                   f"\n\n----\n\n"
                                   f"## 关于图片的解析结果：\n{resp['response']}\n\n"
                                   f"# 用户消息(这个是用户发送的消息哦)\n{content}"
                    })

                # 准备一个函数 用来处理流数据
                async def handler_data(data_string, think_string):
                    """
                    处理流的数据汇总的结果
                    :param data_string: 回复数据 其中每个词占一个元素
                    :param think_string: 思考数据 其中每个词占一个元素
                    """
                    reply_content = ''.join(data_string)
                    # 通过api发送回复消息
                    # if is_channel:
                    #     await self.api.post_message(
                    #         channel_id=real_id,
                    #         msg_id=message_bot.id,
                    #         content=reply_content,
                    #     )
                    # elif is_group:
                    #     await self.api.post_group_message(
                    #         group_openid=real_id,
                    #         msg_id=message_bot.id,
                    #         content=reply_content
                    #     )
                    # else:
                    #     await self.api.post_c2c_message(
                    #         openid=real_id,
                    #         msg_id=message_bot.id,
                    #         content=reply_content
                    #     )

                    # 开始存储数据，数据保存到历史记录
                    self.safe_history_update(real_id=real_id, is_group=is_group, message={
                        "role": "assistant",
                        "content": reply_content
                    })
                    logger.info(
                        f"【ok】时间：{date_str}; realId:{real_id}; 玩家:{user_mark}; 消息:{content}; 回复:{reply_content}")

                # 异步获取模型 API响应
                if is_group:
                    await http_client.fetch_model(
                        model_url=hc.get_space_model_url(group_model_url),
                        headers=[],
                        history_chat=hc,
                        stream=True,
                        stream_fun=handler_data
                    )
                else:
                    await http_client.fetch_model(
                        model_url=hc.get_space_model_url(url),
                        headers=[],
                        history_chat=hc,
                        stream=True,
                        stream_fun=handler_data
                    )
        except Exception as e:
            logger.error(f"处理消息时出错：{str(e)}：{traceback.format_exc()}")
            if need_hidden_module:
                logger.error(f"导致上面异常的命令：【{content}】")
                await message_bot.reply(content=f"""\U0001F63F 处理您的命令时出现错误啦
您可调用的命令
===========
{command_handler.get_commands()}""")
            else:
                await message_bot.reply(content="\U0001F63F 服务器开小差了，请稍后再试～\n============\n"
                                                "更多信息请查询：https://www.lingyuzhao.top/b/Article/-2321317989405261")

    def safe_history_update(self, real_id, is_group, message) -> tuple[Any, bool]:
        """
        存储一个用户/群的消息 并返回其对应的 TimeBoundedList 对象
        :param real_id:
        :param is_group: 是否是群
        :param message:
        :return: 可以直接操作的 TimeBoundedList
        """
        is_first = False
        if is_group:
            # 代表是群消息
            if real_id not in self.history_chats:
                self.history_chats[real_id] = TimeBoundedList(
                    ttl=test_config['userMessageMaxTtl'], max_size=test_config['groupMessageMaxLen']
                )
                is_first = True
            res = self.history_chats[real_id]
        else:
            # 代表是个人消息
            if real_id not in self.history_chats:
                self.history_chats[real_id] = TimeBoundedList(
                    ttl=test_config['userMessageMaxTtl'], max_size=test_config['userMessageMaxLen']
                )
                is_first = True
            res = self.history_chats[real_id]
        res.append(message)
        return res, is_first

    async def on_group_at_message_create(self, message):
        """
        群聊@机器人
        :param message:
        :return:
        """
        await self.handler_message_fun(message.content,
                                       message.author.member_openid,
                                       message.author.member_openid,
                                       message, True)

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
        await self.handler_message_fun(message.content, message.author.username, message.author.username, message)

    async def on_at_message_create(self, message):
        """
        频道所有 @ 消息接受
        :param message:
        :return:
        """
        await self.handler_message_fun(message.content, message.author.username, message.author.username, message)

    async def on_message_create(self, message):
        """
        频道所有消息接受
        :param message:
        :return:
        """
        bot_name = test_config['botName']
        if test_config['botName'] in jieba.cut(message.content):
            await self.handler_message_fun(message.content, message.author.username, message.author.username, message)
        else:
            logger.info(f"未呼叫 {bot_name}")

    async def on_c2c_message_create(self, message):
        """
        私聊
        :param message:
        :return:
        """
        await self.handler_message_fun(message.content,
                                       message.author.user_openid, message.author.user_openid, message)


if __name__ == "__main__":
    import asyncio

    intents = botpy.Intents(public_messages=True, public_guild_messages=True, direct_message=True)
    client = MyClient(intents1=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
