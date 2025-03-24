tools = [
    {
        "type": "function",
        "function": {
            "name": "测试目标网络状态",
            "description": "使用 TCP 测试指定的域名与端口的连通性", "parameters": {
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "这个是目标的 ip 或 域名"
                    },
                    "port": {
                        "type": "string",
                        "description": "这个是目标的 端口 不可以为空，默认是 80"
                    }
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "登录",
            "description": "使用LY码本录用户名和密码登录码本录系统", "parameters": {
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "这个是目标邮件的邮箱地址，代表要发送给哪个邮箱"
                    },
                    "password": {
                        "type": "string",
                        "description": "这个是邮件的标题，不可以为空哦"
                    }
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "发送邮件",
            "description": "发送邮件给其它的LY码本录用户",
            "parameters": {
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "这个是目标用户ID"
                    },
                    "title": {
                        "type": "string",
                        "description": "这个是邮件的标题，不可以为空哦"
                    },
                    "data": {
                        "type": "string",
                        "description": "这个邮件的内容"
                    },
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "发送文章",
            "description": "将一个文章发送到码本录网站中",
            "parameters": {
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "这个是文章的标题"
                    },
                    "desc": {
                        "type": "string",
                        "description": "这个是文章的描述"
                    },
                    "topic": {
                        "type": "string",
                        "description": "这个是文章所属的专题名称"
                    },
                    "data": {
                        "type": "string",
                        "description": "这个是文章的 markdown 内容"
                    },
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            # 填写技能信息
            "name": "查LY码本录身份",
            # 填写技能描述
            "description": "查询当前登录 LY码本录 的 用户名", "parameters": {}
        }
    },
    {
        "type": "function",
        "function": {
            # 填写技能信息
            "name": "当前码本盘镜的空间",
            # 填写技能描述
            "description": "查询当前登录用户的码本盘镜 空间 使用情况", "parameters": {}
        }
    },
    {
        "type": "function",
        "function": {
            # 填写技能信息
            "name": "帮助/查看功能列表",
            # 填写技能描述
            "description": "查询系统支持的功能 和 帮助信息", "parameters": {}
        }
    },
    {
        "type": "function",
        "function": {
            # 填写技能信息
            "name": "退出登录",
            # 填写技能描述
            "description": "让当前用户退出登录状态", "parameters": {}
        }
    }
]

fun_params = {}

for f in tools:
    f1 = f['function']
    fun_params_list = []
    p1 = f1['parameters']
    if "properties" in p1:
        for key, value in p1['properties'].items():
            fun_params_list.append(key)
    fun_params[f1['name']] = fun_params_list


def create_tools(history_chat):
    return {
        "messages": history_chat,
        "stream": False,
        "tools": tools
    }
