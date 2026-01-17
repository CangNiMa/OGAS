# Victoria3 OGAS专用生成工具

## 项目简介

这是一个由UP主**苍王子**开发的Victoria 3 mod OGAS工具，将带有生产方式和物资数据的表格转化为游戏内的可读文件。

该工具旨在自动化兼容其他MOD的生产数据。

## 使用方法

使用Victoria3 building PM工具将所有生产数据导出为csv，
将所有的非生产相关建筑数据剔除。
upgrade和balance模式写在type中，对应pm的两种处理模式。upgrade模式下按照先后顺序判定升级顺序。非这两种情况的pm不会生成pm操控。
处理表格过程可参考目录下苍王子的手稿。本工具将以你做好的pm_goods.csv为准。

如果你添加了物资，请将其添加到goods.txt

执行main.py，将生成后的script_文件夹覆盖OGAS内的文件。

AUTO_construct_building_manager中不包含数值平衡算法，请根据实际情况调整。
