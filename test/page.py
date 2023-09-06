import letmego

# 配置标签记录文件的路径，默认为：/tmp/_running_man.log
letmego.conf.setting.RUNNING_MAN_FILE = "./_running_man.log"
# 配置操作系统的密码
letmego.conf.setting.PASSWORD = "1"


@letmego.mark
class Page:

    def click_some_element_self(self):
        """点击某个元素（实例方法）"""
        print("click self")

    @classmethod
    def click_some_element_cls(cls):
        """点击某个元素（类方法）"""
        print("click cls")

    @staticmethod
    def click_some_element_static():
        """点击某个元素（静态方法）"""
        print("click static")
