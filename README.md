![image](https://github.com/user-attachments/assets/77fd2f15-3208-4c95-ad0b-d48c0f726479)

> 如果需要体验线上机器人，可以进入群体验哦！！

# qq-ai-bot-new

我们提供一个高效且易于配置的QQ机器人解决方案，支持无缝接入[码本翻译官API](https://www.lingyuzhao.top/b/Article/3968498572342507)和[码本大语言模型API](https://www.lingyuzhao.top/b/Article/377388518747589)。通过简单的配置文件修改，即可快速部署运行。

## 主要特性：

* 灵活接入：轻松连接至码本翻译API和大语言模型API，无需复杂编码。
* 简易配置：所有外部服务接入设置均通过单一配置文件进行管理，简化了部署流程。
* 即刻运行：完成配置后，机器人即可立即投入使用，为用户提供即时的服务响应

## 1.前期准备

### 1.1 下载项目

请访问 github链接 下载软件项目！

### 1.2 安装依赖

```shell
pip install qq-botpy jieba aiohttp
```

## 2.配置文件

```yaml
# 机器人appId，需要从 qq开放平台获取
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
# 码本模型服务sk
model_server_sk: '********'
# 码本模型服务id
model_server_id: 49
# 码本模型的 type 参数 请参考：https://www.lingyuzhao.top/b/Article/377388518747589#model%20%E5%8F%82%E6%95%B0
model_server_type: 'cat_neko'
# 码本模型的 model 参数 请参考：https://www.lingyuzhao.top/b/Article/377388518747589#type%20%E5%8F%82%E6%95%B0
model_server_model: 'model01'
# 码本翻译官服务sk
translate_server_sk: '********'
# 码本翻译官服务id
translate_server_id: 46
```

## 启动项目

```shell
python qqgroup-ai-bot.py <配置文件路径>
```
