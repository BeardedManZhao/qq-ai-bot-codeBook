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
from botpy.errors import ServerError
from botpy.ext.cog_yaml import read

from lyMblApi import LyMblApiJvm
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

# 设置用户数据存储位置
if 'user_data_path' in test_config:
    user_data_path = test_config['user_data_path']
else:
    user_data_path = None


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

tools_url = create_url(model_type='none', model='model02')

# 初始化 jvm
lyMblApi = None
if 'jvm_dll' in test_config and 'jvm_jars' in test_config:
    lyMblApi = LyMblApiJvm(test_config['jvm_dll'], test_config['jvm_jars'])

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


def clean(history_chats, message_id, is_group):
    """
    清理消息记录
    :param is_group: 是否属于群组模式
    :param history_chats: 这个是消息列表
    :param message_id: 消息记录对应的 id
    :return: 处理成功的消息
    """
    history_chats[message_id] = TimeBoundedList(
        ttl=test_config['userMessageMaxTtl'], max_size=test_config['groupMessageMaxLen'],
        is_group=is_group
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
    "我是谁": command_who_am_i,
}, {"翻译"})


class MyClient(botpy.Client):
    async def on_ready(self):
        logger.info(f"robot 「{self.robot.name}」 on_ready!")
        await http_client.init_session()

    async def handler_message_fun(self, content, member_openid, user_openid, message_bot, is_group=False,
                                  is_channel=False):
        # 解析到 id 这个是可以直接用于获取消息列表的
        real_id = CommandHandler.parse_message_id(member_openid, message_bot, is_group, is_channel)
        # 获取到消息列表
        fc, is_first = self.safe_history_get_or_create(real_id, is_group)
        # 获取到处理函数并调用 默认是 stream 模式
        await fc.get_space_chat_fun(self.handler_message_stream)(
            real_id=real_id, hc=fc, is_first=is_first, content=content,
            member_openid=member_openid, user_openid=user_openid,
            message_bot=message_bot, is_group=is_group
        )

    def __init__(self, intents1: Intents):
        super().__init__(intents1)
        self.history_chats = {}

        # 追加消息历史查询命令
        def command_history(string, list_args, message_list_id, user_openid, is_group):
            res = []
            for line in self.safe_history_get_or_create(message_list_id, is_group)[0].get_items():
                if line['role'] == 'user':
                    res.append("*用户*\n")
                else:
                    res.append("*neko*\n")
                res.append(line['content'])
                res.append('\n\n###########\n\n')
            return ''.join(res)

        command_handler.push_command("历史消息", command_history, False)

        # 追加 clean 命令
        def command_clean(string, list_args, message_list_id, user_openid, is_group):
            return clean(self.history_chats, message_list_id, is_group)

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
            hc = self.safe_history_get_or_create(message_list_id, is_group)[0]
            if len(list_args) == 0:
                list_args = [
                    hc.get_space_type(def_type_string=test_config['model_server_type']),
                    hc.get_space_model(def_model_string=test_config['model_server_model'])
                ]
            if len(list_args) == 1:
                # 由于没有设置模型 只是改类型 因此我们获取一下原本的模型
                old_model = hc.get_space_model(def_model_string=test_config['model_server_model'])
                hc.set_space_model_url(
                    create_url(list_args[0], old_model),
                    create_group_model_url(list_args[0] + '_group', old_model)
                )
                hc.set_space_model_type(old_model, list_args[0])
                return f"已将您所属空间的类型设置为【{list_args[0]}】\n\n此操作可能会更改一些行为，但区别不大，若需要还原请使用命令【/清理】"
            else:
                hc.set_space_model_url(
                    create_url(list_args[0], list_args[1]),
                    create_group_model_url(list_args[0] + '_group', list_args[1])
                )
                hc.set_space_model_type(list_args[1], list_args[0])
                return (f"已将您所属空间的类型设置为【{list_args[0]}】\n\n已将您所属空间的模式设置为【{list_args[1]}】"
                        f"\n\n此操作可能会更改一些大量行为，若需要还原请使用命令【/清理】")

        command_handler.push_command("设置类型", command_set_model_type, False)

        def command_set_stream_by_line(string, list_args, message_list_id, user_openid, is_group):
            hc = self.safe_history_get_or_create(message_list_id, is_group)[0]
            # 首先判断当前是否是非流
            if hc.get_space_chat_fun(self.handler_message_stream) == self.handler_message:
                # 非流模式就启用流
                hc.set_space_chat_fun(self.handler_message_stream)
                return f"启用 stream 模式~"
            else:
                hc.set_space_chat_fun(self.handler_message)
                return f"关闭 stream 模式~"

        command_handler.push_command("切换流模式", command_set_stream_by_line, False)

        def command_set_use_ly_mbl_api(string, list_args, message_list_id, user_openid, is_group):
            hc = self.safe_history_get_or_create(message_list_id, is_group)[0]
            r = not hc.use_ly_mbl_api()
            hc.set_space_use_ly_mbl_api(r)
            if r:
                return "现在已经 启用了 模型指令，此模式下，机器人会具有更多功能"
            else:
                return "现在已经 关闭了 模型指令，此模式下，机器人会具有更快更好的回答方式"

        command_handler.push_command("切换指令开关", command_set_use_ly_mbl_api, False)

        def command_show_config(string, list_args, message_list_id, user_openid, is_group):
            """
            查自己的用户名
            :param user_openid: 可以代表用户个体的 id
            :param string:
            :param list_args:
            :param message_list_id: 需要被转换的 id
            :param is_group: 当前是否处于群，只有群的状态才会缩减自己的用户名
            :return:
            """
            hc = self.safe_history_get_or_create(message_list_id, is_group)[0]
            return hc.get_configs_string()

        command_handler.push_command("配置查询", command_show_config, False)

        # 日志处理
        logger.info(
            f"欢迎您使用 码本API 的 qq机器人服务！\n"
            f"qq机器人交流群：938229786\n"
            f"neko开源交流群：931546838\n"
            f"详细信息请查询：https://www.lingyuzhao.top/b/Article/-2321317989405261"
        )
        self.lock = asyncio.Lock()  # 添加异步锁防止历史记录冲突

    @staticmethod
    async def handler_message(real_id, hc, is_first, content, member_openid, user_openid, message_bot,
                              is_group=False):
        """
        处理消息
        :param real_id: 可以代表用户消息历史对象的 id
        :param hc: 用户的消息历史对象
        :param is_first: 是否是第一条消息
        :param content: 消息
        :param member_openid: 可以用来记录消息的 id
        :param user_openid: 可以用来代表用户个体的 id
        :param message_bot: 消息对象
        :param is_group: 是否是群组聊天
        :return:
        """
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
                    # 查询是否需要调用 tool
                    tools_res = ''
                    if lyMblApi is not None:
                        # 需要调用
                        if hc.use_ly_mbl_api():
                            tools_res = await http_client.fetch_tools_model(
                                user_openid, tools_url, [], hc, content, lyMblApi
                            )
                    if len(tools_res) != 0:
                        # 函数调用结果
                        logger.info("触发了函数调用：" + tools_res)
                        if '失败' not in tools_res:
                            MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                                "role": "user",
                                "content": f"# 系统消息(注意，这不是用户发送的，请不要对此内容做过多描述，尤其是数字类的参数，这可以避免错误描述)\n"
                                           f"> 当前系统时间：{date_str}\n"
                                           f"> 请尽可能详细的将此结果回复给用户\n"
                                           f"\n\n----\n\n"
                                           f"## 关于用户触发函数调用的调用结果\n"
                                           f"{tools_res}\n\n"
                                           f"# 用户消息(这个是用户发送的消息哦，请结合此信息来将上面的结果回复给用户)\n{content}"
                            })
                        else:
                            # 这是执行命令 但是执行错误了，所以抛出异常信息
                            MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                                "role": "assistant",
                                "content": tools_res
                            })
                            await message_bot.reply(content=tools_res)
                            return
                    else:
                        # 保存用户消息
                        MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                            "role": "user",
                            "content": f"用户[{user_mark}]的消息（用户名：{user_mark}）："
                                       f"【系统消息：当前系统时间：{date_str}】；\n"
                                       f"\n----\n\n{content}",
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
                    MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                        "role": "user",
                        "content": f"* 系统消息(注意，这不是用户发送的)：当前系统时间：{date_str}\n\n----\n\n"
                                   f"# 用户发送的消息（用户名：{user_mark}）：\n\n----\n\n{content}"
                    })
                    # 保存图像消息
                    MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                        "role": "user",
                        "content": f"# 系统消息(注意，这不是用户发送的)\n"
                                   f"> 当前系统时间：{date_str}\n"
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
                MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                    "role": "assistant",
                    "content": reply_content
                })

                # 处理回复 并 异步发送回复
                if is_first and is_group:
                    reply_content += f'\n\n----\n\n系统消息：群空间初始化完毕。'
                elif is_first:
                    reply_content += ('\n\n----\n\n系统消息：\n'
                                      f"欢迎您使用 码本API 的 qq机器人服务！\n"
                                      f"qq机器人交流群：938229786\n"
                                      f"neko开源交流群：931546838\n"
                                      '关于更多信息，https://www.lingyuzhao.top/b/Article/-2321317989405261'
                                      )

                await message_bot.reply(content=reply_content)
                logger.info(
                    f"【ok】时间：{date_str}; realId:{real_id}; 玩家:{user_mark}; 消息:{content}; 回复:{reply_content}")

        except ServerError as se:
            error_string = str(se).replace('.', '_')
            logger.error(f"腾讯拦截了消息，没有成功回答：{content}，因为：{error_string}")
            await message_bot.reply(
                content=f"模型已成功生成回答，但被qq拦截了，下面是qq返回的错误信息！\n====\n{error_string}")
            await message_bot.reply(
                content=f"不用担心，您可以尝试换一种问法哦~\n\n====\n\n更多详情：https://www.lingyuzhao.top/b/Article/-2321317989405261",
                msg_seq='2'
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

    @staticmethod
    async def handler_message_stream(real_id, hc, is_first, content, member_openid, user_openid, message_bot,
                                     is_group=False):
        """
        处理消息
        :param hc: 历史消息对象2
        :param is_first: 是否是第一条消息
        :param real_id: 用于获取消息对象的id
        :param content: 消息
        :param member_openid: 可以用来记录消息的 id
        :param user_openid: 可以用来代表用户个体的 id
        :param message_bot: 消息对象
        :param is_group: 是否是群组聊天
        :return:
        """

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
                    # 查询是否需要调用 tool
                    tools_res = ''
                    if lyMblApi is not None:
                        # 需要调用
                        if hc.use_ly_mbl_api():
                            tools_res = await http_client.fetch_tools_model(
                                user_openid, tools_url, [], hc, content, lyMblApi
                            )
                    if len(tools_res) != 0:
                        # 函数调用结果
                        logger.info("触发了函数调用：" + tools_res)
                        if '失败' not in tools_res:
                            MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                                "role": "user",
                                "content": f"# 系统消息(注意，这不是用户发送的，请不要对此内容做过多描述，尤其是数字类的参数，这可以避免错误描述)\n"
                                           f"> 当前系统时间：{date_str}\n"
                                           f"> 请尽可能详细的将此结果回复给用户\n"
                                           f"\n\n----\n\n"
                                           f"## 关于用户触发函数调用的调用结果\n"
                                           f"{tools_res}\n\n"
                                           f"# 用户消息(这个是用户发送的消息哦，请结合此信息来将上面的结果回复给用户)\n{content}"
                            })
                        else:
                            # 这是执行命令 但是执行错误了，所以抛出异常信息
                            MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                                "role": "assistant",
                                "content": tools_res
                            })
                            await message_bot.reply(content=tools_res)
                            return
                    else:
                        # 保存用户消息
                        MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                            "role": "user",
                            "content": f"用户[{user_mark}]的消息（用户名：{user_mark}）："
                                       f"【系统消息：当前系统时间：{date_str}】；\n"
                                       f"\n----\n\n{content}",
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
                    MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                        "role": "user",
                        "content": f"* 系统消息(注意，这不是用户发送的)：当前系统时间：{date_str}\n\n----\n\n"
                                   f"# 用户发送的消息（用户名：{user_mark}）：\n\n----\n\n{content}"
                    })
                    # 保存图像消息
                    MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                        "role": "user",
                        "content": f"# 系统消息(注意，这不是用户发送的)\n"
                                   f"> 当前系统时间：{date_str}"
                                   f"\n\n----\n\n"
                                   f"## 关于图片的解析结果：\n{resp['response']}\n\n"
                                   f"# 用户消息(这个是用户发送的消息哦)\n{content}"
                    })

                # 准备一个函数 用来处理流数据
                async def handler_data(reply_content, think_string, count):
                    """
                    处理流的数据汇总的结果
                    :param count: 当前回复消息的编号
                    :param reply_content: 回复数据 的字符串
                    :param think_string: 思考数据 list 其中每个词占一个元素
                    """
                    # # 通过api发送回复消息
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
                    #         content=reply_content,
                    #         msg_seq=count
                    #     )
                    # else:
                    #     await self.api.post_c2c_message(
                    #         openid=real_id,
                    #         msg_id=message_bot.id,
                    #         content=reply_content,
                    #         msg_seq=str(count)
                    #     )

                    # 开始存储数据，数据保存到历史记录
                    MyClient.safe_history_update_use_obj(hc=hc, is_first=is_first, message={
                        "role": "assistant",
                        "content": reply_content
                    }, append=count == 1)
                    await message_bot.reply(content=reply_content, msg_seq=str(count))
                    if count == 1:
                        logger.info(
                            f"【ok】时间：{date_str}; realId:{real_id}; 玩家:{user_mark}; 消息:{content}; 回复:{reply_content}")
                    else:
                        logger.info(
                            f"玩家:{user_mark}; 回复:{reply_content}")

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

    def safe_history_get_or_create(self, real_id, is_group) -> (TimeBoundedList, bool):
        """
        存储一个用户/群的消息 并返回其对应的 TimeBoundedList 对象
        :param real_id:
        :param is_group: 是否是群
        :return: 可以直接操作的 TimeBoundedList
        """
        is_first = False
        if is_group:
            # 代表是群消息
            if real_id not in self.history_chats:
                self.history_chats[real_id] = TimeBoundedList(
                    ttl=test_config['userMessageMaxTtl'], max_size=test_config['groupMessageMaxLen'],
                    is_group=is_group
                )
                is_first = True
            res = self.history_chats[real_id]
        else:
            # 代表是个人消息
            if real_id not in self.history_chats:
                self.history_chats[real_id] = TimeBoundedList(
                    ttl=test_config['userMessageMaxTtl'], max_size=test_config['userMessageMaxLen'],
                    is_group=is_group
                )
                is_first = True
            res = self.history_chats[real_id]
        return res, is_first

    def safe_history_update(self, real_id, is_group, message, append=True) -> tuple[Any, bool]:
        """
        存储一个用户/群的消息 并返回其对应的 TimeBoundedList 对象
        :param append: 是否要在消息列表里追加 如果选择False 就是要在最新的消息字符串上追加 而不是列表
        :param real_id:
        :param is_group: 是否是群
        :param message:
        :return: 可以直接操作的 TimeBoundedList
        """
        res, is_first = self.safe_history_get_or_create(real_id, is_group)
        MyClient.safe_history_update_use_obj(res, is_first, message, append)
        return res, is_first

    @staticmethod
    def safe_history_update_use_obj(hc: TimeBoundedList, is_first, message, append=True):
        """
        存储一个用户/群的消息 并返回其对应的 TimeBoundedList 对象
        :param is_first: 是否是第一次处理用户的消息
        :param hc: 用户的历史消息对象
        :param append: 是否要在消息列表里追加 如果选择False 就是要在最新的消息字符串上追加 而不是列表
        :param message:
        """
        if append:
            hc.append(message)
        else:
            hc.set_last_value_append(message)

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
        await self.handler_message_fun(message.content, message.author.username, message.author.username, message,
                                       False, True)

    async def on_message_create(self, message):
        """
        频道所有消息接受
        :param message:
        :return:
        """
        bot_name = test_config['botName']
        if test_config['botName'] in jieba.cut(message.content):
            await self.handler_message_fun(message.content, message.author.username, message.author.username, message,
                                           False, True)
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

    def load_config_one_user(self, chat_id, config):
        res, is_first = self.safe_history_get_or_create(chat_id, config['群组模式'])
        res.set_configs(config)
        logger.info(f"加载【{chat_id}】的配置，成功！")

    def load_config_all_user(self):
        """
        加载用户数据。
        如果 user_data_path 文件存在，则加载其中的数据并更新 history_chats。
        """
        if user_data_path is None:
            logger.warning("未设置 user_data_path，因此无法持久化用户的数据~")
            return

        if not os.path.exists(user_data_path):
            logger.info(f"配置文件 {user_data_path} 不存在，跳过加载。")
            return

        try:
            with open(user_data_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            # 更新 history_chats
            count = 0
            for chat_id, config in loaded_data.items():
                self.load_config_one_user(chat_id, config)
                count += 1
            logger.info(f"配置已成功从 {user_data_path} 加载。共有{count}个用户配置！")
        except Exception as e:
            logger.error(f"加载配置时出错: {e}")

    def save_config(self):
        """
        保存用户数据 一般是用来在程序终止的时候操作的
        """
        if user_data_path is None:
            logger.warning("未设置 user_data_path，因此无法持久化用户的数据~")
            return
        res = {}
        for chat_id, chat_obj in self.history_chats.items():
            res[chat_id] = chat_obj.get_configs()  # 获取每个聊天对象的配置

        # 将数据保存到文件
        try:
            with open(user_data_path, 'w', encoding='utf-8') as f:
                json.dump(res, f, ensure_ascii=False, indent=4)
            logger.info(f"配置已成功保存到 {user_data_path}")
        except Exception as e:
            print(f"保存配置时出错: {e}")


if __name__ == "__main__":
    import asyncio
    import signal

    intents = botpy.Intents(public_messages=True, public_guild_messages=True, direct_message=True)
    client = MyClient(intents1=intents)
    client.load_config_all_user()

    def cleanup(signum, frame):
        """
        当进程收到终止信号时调用此函数。
        可在此处添加调用 diamond 的代码。
        """
        logger.info(f"Caught signal {signum}, initiating cleanup...")
        lyMblApi.close()
        if client is not None:
            client.save_config()
        # 清理完成后退出程序
        sys.exit(0)


    # 监听 Ctrl+C（SIGINT） 和 kill（SIGTERM）信号
    signal.signal(signal.SIGINT, cleanup)  # 处理 Ctrl+C
    signal.signal(signal.SIGTERM, cleanup)  # 处理 kill

    # 开始启动
    client.run(appid=test_config["appid"], secret=test_config["secret"])

