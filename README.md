![image](https://github.com/user-attachments/assets/7ffe55b7-ebe8-4027-af83-b6ed0ae306f7)

> 如果需要体验线上机器人，可以进入群体验哦！！

# qq-ai-bot-codeBook

我们提供一个高效且易于配置的QQ机器人解决方案，支持无缝接入[码本翻译官API](https://www.lingyuzhao.top/b/Article/3968498572342507)和[码本大语言模型API](https://www.lingyuzhao.top/b/Article/377388518747589)。通过简单的配置文件修改，即可快速部署运行。

## 主要特性：

* 灵活接入：轻松连接至码本翻译API和大语言模型API，无需复杂编码。
* 简易配置：所有外部服务接入设置均通过单一配置文件进行管理，简化了部署流程。
* 即刻运行：完成配置后，机器人即可立即投入使用，为用户提供即时的服务响应

## 1.前期准备

### 1.1 下载项目

请访问 GitHub 下载项目文件！

### 1.2 安装依赖

```shell
pip install qq-botpy jieba aiohttp jpype1
```

## 2.配置文件

```yaml
# 机器人appId
appid: "*********"
# 机器人安全密钥
secret: "*********"
# 机器人名字
botName: "neko"
# 用户消息的最大记录数量
userMessageMaxLen: 10
# 群/频道消息的最大记录数量
groupMessageMaxLen: 5
# 每个记录的消息的最大有效时间（ s ）
userMessageMaxTtl: 7200
# 是否隐藏模型服务，如果隐藏则无法使用模型
needHiddenModule: False
# 模型服务sk
model_server_sk: '********'
# 模型服务id
model_server_id: 49
# 模型的 type 参数 请参考：https://www.lingyuzhao.top/b/Article/377388518747589#model%20%E5%8F%82%E6%95%B0
model_server_type: 'cat_neko'
# 群组模型下的 type 参数
model_server_type_group: 'cat_neko_group'
# 模型的 model 参数 请参考：https://www.lingyuzhao.top/b/Article/377388518747589#type%20%E5%8F%82%E6%95%B0
model_server_model: 'model01'
# 可处理图像的模型 model 参数 请参考：https://www.lingyuzhao.top/b/Article/377388518747589#type%20%E5%8F%82%E6%95%B0
model_server_model_image: 'model03'
# 翻译服务sk
translate_server_sk: '********'
# 翻译服务id
translate_server_id: 46
# jvm 的 jar 插件列表
jvm_jars:
  - "/opt/app/qq-neko/qq-ai-bot-codeBook/lib/lyMbl-shell.jar"
# jvm 的dll库文件路径 如果启用此路径，则机器人会获得更丰富的功能 如发送邮件
# jvm_dll: "/opt/app/jdk-17.0.12/lib/server/libjvm.so"
```

## 启动项目

```shell
python qqgroup-ai-bot.py <配置文件路径>
```

## 内置指令 - qq指令

| 指令        | 语法格式                         | 详细信息                                                                                                         |
|-----------|------------------------------|--------------------------------------------------------------------------------------------------------------|
| /now      | 无需参数                         | 查询当前时间                                                                                                       |
| /testArgs | /testArgs <参数1> <参数2>        | 测试参数是否正常                                                                                                     |
| /翻译       | /翻译 <源语言> <目标语言> <需要被翻译的字符串> | 翻译一个文本                                                                                                       |
| /我是谁      | 无需参数                         | 查询您在neko眼中的用户名                                                                                               |
| /历史消息     | 无需参数                         | 查询您所在空间的历史消息                                                                                                 |
| /清理       | 无需参数                         | 清理所有数据并还原最初状态                                                                                                |
| /设置类型     | /设置类型 <模型type参数> <模型model参数> | 切换使用的模型，详细的选项可以在 [码本AI详情](https://www.lingyuzhao.top/b/Article/377388518747589#model%20%E5%8F%82%E6%95%B0)查询 |
| /切换流模式    | 无需参数                         | 如果机器人需要回复快速连贯，请启用流模式，如果需要规范模板（如代表多级标题的回复）则可以关闭流模式，流模式可以更快更像人一样的回复                                            |
| /切换指令开关   | 无需参数                         | 切换指令开关，如果需要机器人对接一些高级功能，如发送邮件，则需要打开此模式！此模式的关闭对模型的回复速度会稍微加快                                                    |
| /配置查询     | 无需参数                         | 查询当前所处空间的配置信息                                                                                                |

## 内置指令 - 模型指令

模型指令是神经网络中的内置功能，它会根据用户的需求来调用~ 会自动识别意图

模型指令是一直在变化的哦~ 请和机器人直接对话 `小家伙，查询一下系统支持的功能和帮助信息` 这类的句子，机器人会回复给您，她自身支持的功能！

下面是一个示例

![69e58f74454c0b12768f031857cd3436c540a08dae6df302a8eeeb43d6a55093](https://diskmirror.lingyuzhao.top/DiskMirrorBackEnd/FsCrud/downLoad/4/Binary?fileName=Article/Image/-3439099015597393/69e58f74454c0b12768f031857cd3436c540a08dae6df302a8eeeb43d6a55093.webp)


## 实机演示视频

<iframe src="//player.bilibili.com/player.html?isOutside=true&aid=114209757075912&bvid=BV1bMXaYGEjA&cid=29022160640&p=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"></iframe>
