# Google Drive

## Feature

- [x] 转存文件或文件夹
- [x] 文件夹信息统计
- 同步
  - 互备份同步(最大同步): 所有备份文件夹互为备份
  - 指定目标同步: 所有备份文件夹向指定目标转换
  - 最小同步: 取所有备份文件夹的公共部分

## OPTIONS

~~~bash
-m    任务类型
-s    目标文件或文件夹, 一般指他人所属
-d    目的地文件夹, 一般指个人所属
-n    线程数量, 即同时并行多少个action
-u    是否使用个人账号, 使用个人账号时, 并行数量强制为1
~~~

## Usage

本程序是一个命令行程序, 依赖于python. 除了需要安装python之外, 一些库也是必要的, 请使用以下命令安装相关的python库依赖.

~~~ bash
pip install requirements.txt
~~~

或者

~~~ bash
pip3 install requirements.txt
~~~

下面给出一些相关的使用例子:

### 转存文件夹

~~~bash
python main.py -
~~~

## TODO

- 增加信息记录
- 增加数据库缓存信息
- 增加GUI界面
- 变量优化

## Operation

- 复制文件: (src, dst)
- 移动文件: (src, dst)
- 删除文件: (src)
- 复制创建文件夹: (src, dst)
- 获取文件信息: (src)

## ChangeLog
