![图片1](https://github.com/user-attachments/assets/88f72def-2eef-49f4-9a24-121ff050aaf3)

> 如果需要体验线上机器人，可以进入群体验哦！！
> 
> 源文章：https://www.lingyuzhao.top/b/Article/-3439099015597393

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

## 2. 配置文件

```yaml
# 机器人appId
appid: "*********"
# 机器人安全密钥
secret: "*********"
# 机器人名字
botName: "neko"
# 机器人要绑定的码本用户名
codebook_lyMbl_user_name: "****"
# 机器人要绑定的码本账户对应的密码
codebook_lyMbl_user_password: "********"
# 慰问间隔时间(s)
comfort_interval: 86400
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
# 用户数据保存路径
user_data_path: "/opt/app/qq-neko/qq-ai-bot-codeBook/config/users.json"
# jvm 的 jar 插件列表
jvm_jars:
  - "/opt/app/qq-neko/qq-ai-bot-codeBook/lib/lyMbl-shell.jar"
# jvm 的dll库文件路径 如果启用此路径，则机器人会获得更丰富的功能 如发送邮件
# jvm_dll: "/opt/app/jdk-17.0.12/lib/server/libjvm.so"
```

## 3. 启动项目

```shell
python qqgroup-ai-bot.py <配置文件路径>
```

## 4. 内置指令 - qq指令

| 指令        | 指令类型      | 语法格式                                | 详细信息                                                                                                          |
|-----------|:----------|-------------------------------------|---------------------------------------------------------------------------------------------------------------|
| /now      | 用户指令      | 无需参数                                | 查询当前时间                                                                                                        |
| /testArgs | 用户指令      | /testArgs <参数1> <参数2>               | 测试参数是否正常                                                                                                      |
| /翻译       | 用户指令      | /翻译 <源语言> <目标语言> <需要被翻译的字符串>        | 翻译一个文本                                                                                                        |
| /我是谁      | 用户指令      | 无需参数                                | 查询您在neko眼中的用户名（因为qq不给机器人关于您的qq账号信息，所以机器人会为您生成一个id或用户名）                                                        |
| /历史消息     | 用户指令      | 无需参数                                | 查询您所在空间的历史消息（暂时停用）                                                                                            |
| /清理       | 用户指令      | 无需参数                                | 清理当前用户空间的上下文，用于开启新的话题                                                                                         |
| /设置类型     | **管理员指令** | /设置类型 <模型type参数> <模型model参数>        | 切换使用的模型，详细的选项可以在 [码本AI详情](https://www.lingyuzhao.top/b/Article/377388518747589#model%20%E5%8F%82%E6%95%B0) 查询 |
| /切换流模式    | 用户指令      | 无需参数                                | 如果机器人需要回复快速连贯，请启用流模式，如果需要规范模板（如代表多级标题的回复）则可以关闭流模式，流模式可以更快更像人一样的回复                                             |
| /切换指令开关   | **管理员指令** | 无需参数                                | 切换指令开关，如果需要机器人对接一些高级功能，如发送邮件，则需要打开此模式！此模式的关闭对模型的回复速度会稍微加快                                                     |
| /配置查询     | 用户指令      | 无需参数                                | 查询当前所处空间的配置信息                                                                                                 |
| /注册       | 用户指令      | 无需参数                                | 通过Neko注册码本账号（暂时是引导到网站注册账号，后续会接入自动注册的！！）                                                                       |
| /管理员      | **用户指令**  | /管理员 <添加/删除/启用/禁用> <添加和删除需要填写的用户id> | 对一个用户进行管理员赋权或移除权限，同时可以设置启用或禁用管理员模式                                                                            |

### 4.1 什么是空间

neko 会给每一个用户或者群单独分配一个空间，用于存储共享的数据，包括但不限于配置信息，消息记录

私聊的情况下，用户单独成为一个空间

频道/群聊的区块下，群的所有用户组成一个空间，当人员发生变动的时候，neko的空间也会同步数据

### 4.2 关于空间中的配置

当我们执行了 `/配置查询` 操作的时候，neko会回复当前空间的配置信息以及对应的值，我们在这里对值进行解释

| 配置项目         | 数据类型               | 如何修改                 | 项目的意义                                                                                          |
|--------------|--------------------|----------------------|------------------------------------------------------------------------------------------------|
| 管理员表         | json或字符串           | /管理员                 | 如果启用了管理员校验功能，则这里会显示管理员的json列表，其中key是管理员的id，value是管理员的优先级，优先级值越小，优先级越高                          |
| 群组模式         | 布尔                 | 无法修改，此值在空间初始化时已经固定   | 如果当前空间属于群聊/频道 则会初始化为 True                                                                      |
| 模型指令         | 布尔                 | /切换指令开关              | 如果为 True 代表当前启用了模型指令                                                                           |
| 模型型号         | 字符串                | /设置类型                | 在 [码本AI详情](https://www.lingyuzhao.top/b/Article/377388518747589#model%20%E5%8F%82%E6%95%B0) 查询 |
| 数据风格         | 字符串                | /设置类型                | 在 [码本AI详情](https://www.lingyuzhao.top/b/Article/377388518747589#model%20%E5%8F%82%E6%95%B0) 查询 |
| 聊天模式         | 字符串                | /切换流模式               | 如果值 包含 `stream` 代表当前启用了流模式                                                                     |
| 最后登录         | 字符串                | 启用模型指令后，通过neko登录码本账号 | 如果值是您的码本用户名，则代表您已经登录了码本账号！                                                                     |
| history_chat | 枚举【`未找到` or `已启用`】 | 无法修改，此值由系统自动处理       | 此数值代表的就是您的消息记录是否被持久化记忆，如果是 `已启用` 则代表消息记录已经记忆完毕，作为用户无需关注此参数                                     |

## 5. 内置指令 - 模型指令

模型指令是神经网络中的内置功能，它会根据用户的需求来调用~ 会自动识别意图

模型指令是一直在变化的哦~ 请和机器人直接对话 `小家伙，查询一下系统支持的功能和帮助信息` 这类的句子，机器人会回复给您，她自身支持的功能！

下面是一个示例

![69e58f74454c0b12768f031857cd3436c540a08dae6df302a8eeeb43d6a55093](https://diskmirror.lingyuzhao.top/DiskMirrorBackEnd/FsCrud/downLoad/4/Binary?fileName=Article/Image/-3439099015597393/69e58f74454c0b12768f031857cd3436c540a08dae6df302a8eeeb43d6a55093.webp)

## 6. 隐藏小功能

### 6.1 慰问

neko 会在您不在的时候，偷偷利用码本录的系统给您发送消息哦~

> 触发条件
> 1. 您需要在**私聊页面**，通过 neko 登录您的码本录账号！
> 2. 您需要在**私聊页面**和 neko 交流对话，让neko记住您
> 3. 您需要等待一段时间（就是配置 `comfort_interval` 的值）以下的时间内，neko会偷偷给您小惊喜
> 4. 您需要确保 type 参数是 `cat_neko`，当然，如果您没有使用过 `/设置类型` 则不需要担心此问题

> 若您是开发者，还需要以下操作
> 1. 您需要确保neko系统不重启，因为重启后重新等待时间
> 2. 您需要为 neko 配置一个码本的用户名和密码，就是配置项目 `codebook_lyMbl_user_name` 和 `codebook_lyMbl_user_password`

### 6.2 意图识别

neko 可以根据您的话语使用电脑来执行一些操作，包括但不限于 上网搜索数据，查询当前时间，持久化保存数据

### 6.3 none 自定义引导

当您将 neko 设置为 `none` 的type 的时候，您可以使用自己的话语来引导她，实现自定义角色的效果~

### 6.4 关于码本账号

码本账号是独立于 qq 的一套系统，由于qq不允许机器人主动发送消息之类的功能，导致可玩性大大降低，因此您可以选择通过 neko 登录码本录，实现更多有序的功能拓展

具体操作如下

#### 6.4.1 启用模型指令

您需要调用 `/切换指令开关` 来将指令切换到启用状态！

#### 6.4.2 直接和neko对话 登录码本录

下面是一个示例

![3eb96ffe6f550329b2e8c621e42bbdb545669ccc8590a1657686c859d479ca1](https://diskmirror.lingyuzhao.top/DiskMirrorBackEnd/FsCrud/downLoad/4/Binary?fileName=Article/Image/-3439099015597393/3eeb96ffe6f550329b2e8c621e42bbdb545669ccc8590a1657686c859d479ca1.webp)

## 7. 实机演示视频

<iframe src="//player.bilibili.com/player.html?isOutside=true&aid=114209757075912&bvid=BV1bMXaYGEjA&cid=29022160640&p=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"></iframe>
