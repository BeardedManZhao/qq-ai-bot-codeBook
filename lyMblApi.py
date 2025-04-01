import jpype.imports

from tools import fun_params


class LyMblApiJvm:

    def __init__(self, jvm_dll, loader_jars=None):
        """
        支持访问 码本API 的 jvm 类组件
        :param jvm_dll: jvm 的 dll 文件  一般是 bin\server\jvm.dll(windows) 或者 lib/server/libjvm.so(linux)
        :param loader_jars: 加载的 jar 的列表
        """

        if loader_jars is None:
            loader_jars = ['./lib/lyMbl-shell.jar']

        # 启动 JVM（只需要启动一次）
        if not jpype.isJVMStarted():
            jpype.startJVM(jvm_dll,
                           "-Dfile.encoding=UTF-8",  # 强制使用 UTF-8 编码
                           classpath=loader_jars)
        self.ready = True

    def run(self, user_open_id, option_name, args):
        if self.ready:
            # 导入 Java 类
            from top.lingyuzhao.lyMbl.shell import Main  # 替换为你的实际包名和类名
            return Main.run(user_open_id, option_name, args)

    def is_ready(self):
        return self.ready

    def close(self):
        """
        关闭 jvm
        """
        if self.ready:
            # 导入 Java 类
            from top.lingyuzhao.lyMbl.shell import Main  # 替换为你的实际包名和类名
            Main.close()
            # 程序结束时关闭 JVM（可选）
            jpype.shutdownJVM()

    def json_cell(self, user_open_id, json):
        """
        解析 tools 返回并调用对应的操作
        :param user_open_id:
        :param json:
        :return:
        """
        res_str = []
        res = json['message']
        if 'tool_calls' not in res:
            return ''
        else:
            for func in res['tool_calls']:
                f = func['function']
                # 获取到名字
                name = f['name']
                arguments = f['arguments']
                # 开始找到这个函数 并解析格式
                args = []
                if name not in fun_params:
                    return '\n系统消息：不支持的操作:' + name
                for p_name in fun_params[name]:
                    if p_name not in arguments:
                        continue
                    arg = str(arguments[p_name])
                    if len(arg) != 0:
                        args.append(arg)

                # 开始调用
                res_str.append('\n* 系统消息：根据用户要求执行 ')
                res_str.append(name)
                res_str.append(' 的结果：')
                res_str.append(str(self.run(user_open_id, name, args)))
                res_str.append('\n')
        return ''.join(res_str)

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Exiting context")
        self.close()
