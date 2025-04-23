import asyncio
import sys

import botpy

from neko import NekoClient, logger, lyMblApi, test_config

if __name__ == "__main__":
    import signal

    intents = botpy.Intents(public_messages=True, public_guild_messages=True, direct_message=True)
    client = NekoClient(intents1=intents)
    client.load_config_all_user()
    # 初始化所有的异步任务
    asyncio.run(client.init_interval_scheduler())

    def cleanup(signum, frame):
        """
        当进程收到终止信号时调用此函数。
        可在此处添加调用 diamond 的代码。
        """
        logger.info(f"Caught signal {signum}, initiating cleanup...")
        if client is not None:
            client.save_config()
        lyMblApi.close()
        # 清理完成后退出程序
        sys.exit(0)


    # 监听 Ctrl+C（SIGINT） 和 kill（SIGTERM）信号
    signal.signal(signal.SIGINT, cleanup)  # 处理 Ctrl+C
    signal.signal(signal.SIGTERM, cleanup)  # 处理 kill

    # 开始启动
    client.run(appid=test_config["appid"], secret=test_config["secret"])
