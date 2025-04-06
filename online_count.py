from utils import TimeBoundedList


class OnlineCount(TimeBoundedList):
    """
    在线统计器
    """

    def __init__(self, timeout):
        super().__init__(timeout, max_size=1024, is_group=False)

    def count(self):
        count_r = {}
        for get_item in self.get_items():
            if get_item not in count_r:
                count_r[get_item] = 1
            else:
                count_r[get_item] += 1
        return count_r

    def count_get_string(self):
        count_r = self.count()
        res = [f"当前在线人数：【{len(count_r)}】\n----\n"]
        for e in count_r:
            res.append(e)
            res.append(' 活跃度')
            res.append(f"【{count_r[e]}】")
            res.append("\n\n")
        return ''.join(res)

