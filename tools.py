tools = [{"type": "function", "function": {"name": "定时任务", "description": "设定一个定时任务，用于将一个函数延迟执行",
                                           "parameters": {"properties": {"time": {"type": "long",
                                                                                  "description": "定时操作的时间设置（单位秒），算不出来就给空，这个不可以算错~"},
                                                                         "延迟执行的函数的名字": {"type": "string",
                                                                                                  "description": "要触发的函数名，如 发送邮件给当前用户"},
                                                                         "延迟执行的函数的参数": {"type": "list",
                                                                                                  "description": "触发函数时的参数,按位置传参,每个元素直接字符串就可以哦"}}}}},
         {"type": "function",
          "function": {"name": "测试目标网络状态", "description": "使用 TCP 测试指定的域名与端口的连通性",
                       "parameters": {"properties": {"ip": {"type": "string", "description": "这个是目标的 ip 或 域名"},
                                                     "port": {"type": "string",
                                                              "description": "这个是目标的 端口 不可以为空，默认是 80"}}}}, },
         {"type": "function",
          "function": {"name": "帮助/查看功能列表", "description": "查询系统支持的功能 和 帮助信息", "parameters": {}}},
         {"type": "function", "function": {"name": "查询码本用户列表", "description": "查询目前已记录的 码本用户 列表",
                                           "parameters": {"properties": {"查询的页码或关键字": {"type": "int或string",
                                                                                                "description": "这个代表当前要查询的码本用户列表的页码或者关键字，如果是数值就代表是页面，如果是其它文本就代表是搜索关键字！"}}}}},
         {"type": "function", "function": {"name": "登录", "description": "使用LY码本录用户名和密码登录码本录系统",
                                           "parameters": {"properties": {"username": {"type": "string",
                                                                                      "description": "这个是登录码本录系统时候要用的用户名"},
                                                                         "password": {"type": "string",
                                                                                      "description": "这个是登录码本录系统时候要用的密码"}}}}, },
         {"type": "function", "function": {"name": "发送邮件给当前用户",
                                           "description": "向当前对话用户发送邮件，系统会自动识别用户身份，无需额外提供收件人信息",
                                           "parameters": {
                                               "properties": {"content": {"type": "string", "description": "邮件内容"}},
                                               "required": ["content"]}}}, {"type": "function",
                                                                            "function": {"name": "发送邮件给指定用户",
                                                                                         "description": "向指定的 LY 码本录用户发送邮件，需提供收件人 ID",
                                                                                         "parameters": {"properties": {
                                                                                             "recipient_id": {
                                                                                                 "type": "int",
                                                                                                 "description": "目标用户 ID"},
                                                                                             "subject": {
                                                                                                 "type": "string",
                                                                                                 "description": "邮件标题，不能为空"},
                                                                                             "content": {
                                                                                                 "type": "string",
                                                                                                 "description": "邮件内容"}},
                                                                                             "required": [
                                                                                                 "recipient_id",
                                                                                                 "subject",
                                                                                                 "content"]}}},
         {"type": "function", "function": {"name": "发送文章", "description": "将一个文章发送到码本录网站中",
                                           "parameters": {"properties": {
                                               "title": {"type": "string", "description": "这个是文章的标题"},
                                               "desc": {"type": "string", "description": "这个是文章的描述"},
                                               "topic": {"type": "string", "description": "这个是文章所属的专题名称"},
                                               "data": {"type": "string",
                                                        "description": "这个是文章的 markdown 内容"}, }}}},
         {"type": "function",
          "function": {"name": "查LY码本录身份", "description": "查询当前登录 LY码本录 的 用户名", "parameters": {}}},
         {"type": "function",
          "function": {"name": "当前码本盘镜的空间", "description": "查询当前登录用户的码本盘镜 空间 使用情况",
                       "parameters": {}}}, {"type": "function",
                                            "function": {"name": "退出登录", "description": "让当前用户退出登录状态",
                                                         "parameters": {}}}]

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
