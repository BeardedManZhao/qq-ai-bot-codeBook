import json
import time
from collections import deque
from datetime import datetime

import aiohttp


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

    def append(self, item):
        """
        添加新元素到列表中，并移除过期或超出最大数量限制的元素。

        :param item: 要添加的元素
        """
        # 这是添加时间以及元素本身的元组
        self.container.append((time.time(), item))

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
            self.session = aiohttp.ClientSession()
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

    async def fetch_model(self, model_url: str, headers, history_chat: TimeBoundedList) -> json:
        """
        向模型发起对话请求
        :param model_url: 模型API 的 url
        :param headers: 头数据
        :param history_chat: 聊天历史消息列表
        :return: 模型的 json
        """
        data = {
            "model": "CodeBook-deepSeek",
            "messages": history_chat.get_items(),
            "stream": False
        }
        async with self.session.post(model_url, headers=headers, json=data) as response:
            return json.loads(await response.text())

    async def close(self):
        await self.session.close()


class CommandHandler:
    def __init__(self, cf, a_command_set):
        """
        初始化并提供处理函数
        :param cf: 当前的函数处理器对应的json key是命令，value 是处理器，处理器接受一个string，就是剔除了指令的值，以及一个 list 是 string 按空格拆分的值
        :param a_command_set 需要使用异步的命令
        """
        self.command_fun = cf
        self.a_command_set = a_command_set

    def get_commands(self):
        # 遍历并打印所有键
        res = []
        for key in self.command_fun.keys():
            res.append(key)
            res.append('\n----------\n')
        return ''.join(res)

    async def handler(self, content: str) -> str:
        """
        调用命令
        :param content: 参数上下文
        :return: 结果
        """
        args = content.split(' ')
        if self.is_async(args[0]):
            return await self.command_fun[args[0]](content[len(args[0]):], args[1:])
        return self.command_fun[args[0]](content[len(args[0]):], args[1:])

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
        if string[0] == '<':
            index = 0
            for e in string:
                index += 1
                if e == '>':
                    break
            return string[index:].strip()
        else:
            return string

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
