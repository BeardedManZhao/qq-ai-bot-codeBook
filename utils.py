import base64
import hashlib
import json
import re
import time
from collections import deque, defaultdict
from datetime import datetime

import aiohttp

from tools import create_tools


class TimeBoundedList:
    """
    一个具有指定元素数量 以及 每个元素过期时间的数据容器
    """

    def __init__(self, ttl, max_size):
        """
        初始化TimeBoundedList实例。

        :param ttl: int, 元素的有效时间（秒）
        :param max_size: int, 容器的最大元素数量
        """
        self.ttl = ttl
        self.container = deque(maxlen=max_size)  # 使用双端队列存储(插入时间, 数据)的元组
        self.config = {}  # 用于存储此空间的一些临时配置
        # 设置默认值
        self.set_space_use_ly_mbl_api(self.use_ly_mbl_api())

    def set_config(self, config_name: str, config_value):
        """
        设置一个配置参数到这里 可能会在各种地方使用
        :param config_name: 配置名字
        :param config_value: 配置的数值
        :return:
        """
        self.config[config_name] = config_value

    def get_config(self, config_name: str, def_value):
        """
        获取到一个配置项目 获取不到就使用默认值
        :param config_name: 需要使用的配置的名字
        :param def_value: 获取不到时候的默认数值
        :return: 结果
        """
        if config_name in self.config:
            return self.config[config_name]
        else:
            return def_value

    def get_configs_string(self):
        """
        将所有的配置信息查询出来
        :return: 结果
        """
        res = []
        count = 0
        for c in self.config:
            if 'url' not in c:
                res.append('【')
                res.append(c)
                res.append(f'】{self.config[c]}')
                res.append('\n\n')
                count += 1
        res.append(f"共找到{count}个配置项目！")
        return ''.join(res)

    def set_space_chat_fun(self, fun):
        self.set_config("聊天模式", fun)

    def get_space_chat_fun(self, def_value):
        return self.get_config("聊天模式", def_value)

    def set_space_model_type(self, model_string, type_string):
        if model_string is None:
            model_string = '默认'
        if type_string is None:
            type_string = '默认'
        self.set_config("模型型号", model_string)
        self.set_config("数据风格", type_string)

    def set_space_model_url(self, model_url: str, model_group_url: str):
        self.set_config("model_url", model_url)
        self.set_config("model_group_url", model_group_url)

    def get_space_model_url(self, def_value):
        return self.get_config("model_url", def_value)

    def get_space_model_group_url(self, def_value):
        return self.get_config("model_group_url", def_value)

    def set_space_use_ly_mbl_api(self, value):
        return self.set_config("模型指令", value)

    def use_ly_mbl_api(self):
        return self.get_config("模型指令", False)

    def append(self, item):
        """
        添加新元素到列表中，并移除过期或超出最大数量限制的元素。

        :param item: 要添加的元素
        """
        # 这是添加时间以及元素本身的元组
        self.container.append((time.time(), item))

    def set_last_value_append(self, new_string):
        """
        将最新添加的数值进行修改 修改方法就是直接在值上追加新的字符串
        :param new_string 新的字符串
        """
        # 弹出最新添加的元素
        latest_element = self.container.pop()
        latest_element[1]['content'] += new_string['content']
        # 追加最新的元素
        self.container.append(latest_element)

    def get_items(self):
        """
        获取当前有效的所有元素。

        :return: list, 当前有效的所有元素组成的列表
        """
        res = []
        now = time.time()
        for t, value in self.container:
            if now - t <= self.ttl:
                # 代表没过期
                res.append(value)
        return res


class HttpClient:
    """
    HTTP 请求库
    """

    def __init__(self):
        self.session = None

    async def init_session(self):
        if self.session is None:
            # verify_ssl 用于防止请求 https 出问题
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=64, verify_ssl=False))
        return self.session

    async def fetch_text(self, url: str) -> str:
        try:
            async with self.session.get(url) as response:
                # 检查响应的状态码是否为 200 (OK)
                if response.status != 200:
                    return f"此链接请求失败，状态码：{response.status}"

                # 获取响应的内容类型
                content_type = response.headers.get('Content-Type', '').lower()

                # 检查内容类型是否为文本类型
                if not any(content_type.startswith(mime) for mime in ['text/', 'application/json']):
                    return "此链接返回的数据是不支持的类型，只能使用文本数据的链接"

                # 读取响应内容
                text = await response.text()
                return text
        except aiohttp.ClientError as e:
            return f"请求发生错误: {e}"

    async def fetch_tools_model(self, user_open_id, model_url: str, headers, history_chat: TimeBoundedList | list,
                                input_content, ly_mbl_jvm):
        if type(history_chat) is TimeBoundedList:
            messages = history_chat.get_items()
        else:
            messages = history_chat
        messages.append({
            "role": "user",
            "content": input_content
        })
        async with self.session.post(model_url, headers=headers, json=create_tools(messages)) as response:
            return ly_mbl_jvm.json_cell(user_open_id, json.loads(await response.text()))

    async def fetch_model(self, model_url: str, headers, history_chat: TimeBoundedList, stream: bool = False,
                          stream_fun=None, think_mark='think'):
        """
        向模型发起对话请求
        :param think_mark: 思考标记 在标记中的数据将不会被发送
        :param stream_fun: 如果是使用的流，则数据会直接传递到此函数中
        :param stream: 是否要使用流式数据
        :param model_url: 模型API 的 url
        :param headers: 头数据
        :param history_chat: 聊天历史消息列表
        :return: 模型的 json 或者 None（对于流式数据）
        """
        data = {
            "messages": history_chat.get_items(),
            "stream": stream,
        }
        think_start, think_end = f"<{think_mark}>", f"</{think_mark}>"

        async with self.session.post(model_url, headers=headers, json=data) as response:
            think_string = []
            res_list = []
            count = 1
            if stream:
                # 如果是流式处理，逐行读取并解析响应
                in_think = False
                async for line in response.content:
                    if line:
                        try:
                            decoded_line = line.decode('utf-8')
                            if decoded_line:  # 确保非空
                                res = json.loads(line.decode('utf-8'))['message']  # 解码并打印每一条消息
                                if type(res) is str:
                                    await stream_fun(res, [], count)
                                else:
                                    res_string = res['content']
                                    if think_end in res_string:
                                        in_think = False
                                    elif think_start in res_string:
                                        in_think = True

                                    # 不是在 think 且 token 有数据
                                    elif not in_think and len(res_string) != 0:
                                        res_list.append(res_string)
                                        if count <= 4 and '\n' in res_string:
                                            # 代表是换段 同时消息数量小于4 可以继续发送
                                            reply_content = ''.join(res_list).strip()
                                            if len(reply_content) != 0:
                                                await stream_fun(reply_content, think_string, count)
                                                res_list = []
                                                count += 1
                        except json.JSONDecodeError:
                            continue  # 忽略无法解析为JSON的数据
                # 迭代结束 看看是否还有没发送的
                if len(res_list) != 0:
                    # 有没发送的 直接发送
                    reply_content = ''.join(res_list).strip()
                    if len(reply_content) != 0:
                        await stream_fun(reply_content, think_string, count)
                    elif count == 1:
                        await stream_fun("模型似乎正在维护中呢，没有有效的回复~", think_string, count)
                return None  # 流式处理不返回最终结果
            else:
                json_text = await response.text()
                try:
                    # 如果不是流式处理，直接返回json解析结果
                    return json.loads(json_text)
                except json.decoder.JSONDecodeError:
                    raise ValueError("模型的回复json解析操作出现问题了！【" + json_text + '】')

    async def fetch_model_images(self, model_prompt_url: str, headers, images: list):
        """
        :param headers: 头数据
        :param images: 需要被模型看的图片
        :param model_prompt_url: 一次性请求使用的 url 用于多模态
        :return:
        """
        data = {
            # 提取出最新发送的消息
            "prompt": '请用最详细的语言来描述图！',
            "stream": False,
            # 提取出所有图片
            "images": images
        }
        async with self.session.post(model_prompt_url, headers=headers, json=data) as response:
            return json.loads(await response.text())

    async def urls_to_base64(self, url_list, logger, timeout=10):
        """
        将网络图片转换为Base64编码

        参数:
            url_list (list): 图片的HTTP/HTTPS地址列表
            timeout (int): 请求超时时间(秒)

        返回:
            list: Base64编码字符串列表 (格式如: "data:image/png;base64,iVBORw0...")
                  若某个请求失败，对应位置返回None
        """
        res = []
        for url in url_list:
            try:
                async with self.session.get(url.replace("https", "http"), timeout=timeout) as response:
                    response.raise_for_status()  # 自动处理4xx/5xx错误
                    image_data = await response.read()  # 异步读取图片数据
                    # 如果需要添加data URI前缀，可以获取Content-Type：
                    # content_type = response.headers.get('Content-Type', 'image/png')
                    b64_str = base64.b64encode(image_data).decode('utf-8')
                    # encoded_str = f"data:{content_type};base64,{b64_str}"
                    res.append(b64_str)
            except Exception as e:
                if logger is not None:
                    logger.warning(f"图片转换失败【{str(e)}】：{url_list}")
        return res

    async def close(self):
        await self.session.close()


class CommandHandler:

    @staticmethod
    def parse_message_id(member_openid, message_bot, is_group=False, is_channel=False):
        # 获取到真正的消息id
        if is_group:
            return message_bot.group_openid
        elif is_channel:
            return message_bot.channel_id
        else:
            return member_openid

    def __init__(self, cf, a_command_set):
        """
        初始化并提供处理函数
        :param cf: 当前的函数处理器对应的json key是命令，value 是处理器，处理器接受一个string，就是剔除了指令的值，以及一个 list 是 string 按空格拆分的值
        :param a_command_set 需要使用异步的命令
        """
        self.command_fun = cf
        self.a_command_set = a_command_set

        # 编译正则表达式
        self.pattern = re.compile(r'[\s\x00-\x1F\x7F]+')

    def push_command(self, command_key, command_fun, is_async):
        """
        追加一个命令到处理器中
        :param command_key: 命令字符串
        :param command_fun: 命令对应的处理逻辑
        :param is_async: 是否需要挂起操作
        :return:
        """
        self.command_fun[command_key] = command_fun
        if is_async:
            self.a_command_set.add(command_key)

    def get_commands(self):
        # 遍历并打印所有键
        res = []
        for key in self.command_fun.keys():
            res.append(key)
            res.append('\n----------\n')
        return ''.join(res)

    async def handler(self, content: str, message_id: str, user_openid: str, is_group: bool) -> str:
        """
        调用命令
        :param user_openid: 可以用来代表用户个体的 id
        :param is_group: 是否处于群聊
        :param message_id: 消息id
        :param content: 参数上下文
        :return: 结果
        """
        args = self.pattern.split(content)
        args[0] = args[0].strip('\uE000 /')
        if args[0] == '':
            # 代表命令有问题 偏移一下参数位
            args = args[1:]
            args[0] = args[0].strip('\uE000 /')
        if args[0] not in self.command_fun:
            return (
                f"没有找到可以调用的机器人指令：{args[0]}\n\n关于支持的指令和机器人详情，请查阅：https://www.lingyuzhao.top/b/Article"
                f"/-3439099015597393#%E5%86%85%E7%BD%AE%E6%8C%87%E4%BB%A4%20-%20qq%E6%8C%87%E4%BB%A4")
        if self.is_async(args[0]):
            return await self.command_fun[args[0]](content[len(args[0]):], args[1:], message_id, user_openid, is_group)
        return self.command_fun[args[0]](content[len(args[0]):], args[1:], message_id, user_openid, is_group)

    def is_async(self, command: str):
        """
        判断一个命令是否需要异步处理
        :param command:
        :return:
        """
        return command in self.a_command_set


class StrUtils:
    @staticmethod
    def trim_at_message(string) -> str:
        """
        去除输入消息起始的 <@!18317418856015228057> 标识
        :param string: 需要被处理的消息
        :return: 处理之后的消息
        """
        if len(string) == 0:
            return string
        if string[0] == '<':
            index = 0
            for e in string:
                index += 1
                if e == '>':
                    break
            return string[index:].strip()
        else:
            return string.strip()

    @staticmethod
    def get_last_segment(input_string) -> str:
        """
        接受一个字符串，如果字符串中包含 <think/> 则按照 <think/> 拆分并获取到最后一个字符串。

        :param input_string: 输入的字符串
        :return: 按照 <think/> 拆分后得到的最后一个字符串
        """
        # 查找 <think/> 是否在字符串中
        if '</think>' in input_string:
            # 使用 </think> 作为分隔符拆分字符串
            segments = input_string.split('</think>')
            # 返回最后一个拆分结果
            return segments[-1].strip()
        else:
            # 如果没有找到 <think/>，则返回原始字符串
            return input_string

    @staticmethod
    def get_current_time_formatted() -> str:
        """
        获取当前时间并格式化为 '年月日时分秒' 的形式。
        格式: YYYYMMDDHHMMSS
        返回: 格式化后的字符串
        """
        # 获取当前时间
        now = datetime.now()

        # 格式化时间为 年月日时分秒 的格式
        formatted_time = now.strftime("%Y年%m月%d日 %H时%M分%S秒")

        return formatted_time

    @staticmethod
    def desensitization(string: str) -> str:
        """
        数据脱敏
        :param string: 要被脱贫的字符串
        :return: 脱敏之后的字符串 每隔一个字符会被替换为一个星号
        """
        r = []
        length = 0
        for c in string:
            if (length - (length >> 1 << 1)) != 0:
                r.append('*')
            else:
                r.append(c)
            length += 1
        return ''.join(r)

    @staticmethod
    def id_to_short_identifier(user_id_need_handler: str, length: int = 4) -> str:
        """
        将长数字 ID 转换为简短标识符

        参数:
            user_id (int): 用户的长数字 ID
            length (int): 标识符的长度（默认 4 字符）

        返回:
            str: 简短标识符
        """
        # 将数字 ID 转换为字符串并编码为字节
        user_id_str = user_id_need_handler.encode('utf-8')

        # 使用 SHA-256 哈希函数生成固定长度的摘要
        hash_obj = hashlib.sha256(user_id_str)
        hash_bytes = hash_obj.digest()

        # 使用 Base64 编码将哈希值转换为字符串
        encoded = base64.urlsafe_b64encode(hash_bytes).decode('utf-8')

        # 截取指定长度的标识符
        return encoded[:length]

    @staticmethod
    def who_am_i(user_openid, is_group):
        """
        将一个 id 转换为简短好记的用户名
        :param user_openid: 可以代表用户个体的 id
        :param is_group: 当前是否处于群，只有群的状态才会缩减自己的用户名
        :return:
        """
        if is_group:
            # 如果是群组 就要处理一下 避免不认识
            return StrUtils.id_to_short_identifier(user_openid)
        else:
            return user_openid


class BotUtils:

    @staticmethod
    def group_attachments_by_type(message) -> defaultdict:
        """
        从消息中提取附件属性，并将不同类型的附件分组。

        例如：所有 image/* 类型的附件都分到 "image" 组中。

        参数:
            message (dict): 包含 'attachments' 属性的消息字典，
                            'attachments' 的值是一个字符串，表示列表格式。

        返回:
            dict: 分组后的附件，键为附件类型（如 "image", "video", "audio" 等），
                  值为对应类型的附件列表。
        """
        grouped = defaultdict(list)
        for attach in message.attachments:
            content_type = attach.content_type
            # 按附件的 content_type 分组
            if content_type.startswith('image/'):
                group_key = 'image'
            elif content_type.startswith('video/'):
                group_key = 'video'
            elif content_type.startswith('audio/'):
                group_key = 'audio'
            else:
                # 其他类型则取 content_type 的主类别，如 application、text 等
                group_key = content_type.split('/')[0] if '/' in content_type else content_type

            grouped[group_key].append(attach.url)

        return grouped
