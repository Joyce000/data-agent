# from dataclasses import dataclass, MISSING
# from pathlib import Path
#
# from omegaconf import OmegaConf
# from typing import Dict
#
#
# @dataclass
# class Address:
#     city: str = MISSING
#     street: str = MISSING
#
# #2，定义一个与配置文件结构相同的类
# @dataclass
# class MyConfig:
#     name: str = MISSING
#     age: int = MISSING
#     gender: str = MISSING
#     address: Address
#
# #__file__ :当前文件的绝对目录
# """
# path方法可以获取文件的路径，.parent该路径下的父目录，/ 后面加目录名，即子目录。parents[2]即向上两级父目录
# """
# #1.加载路径-配置文件的内容
# config_file = Path(__file__).parents[2] / 'conf' / 'app_config.yaml'
# content = OmegaConf.load(config_file)  #字典类型：dict
#
# #3.加载类，合并后转对象
# schema = OmegaConf.structured(MyConfig)
#
# app_conf: MyConfig = OmegaConf.to_object(OmegaConf.merge(schema, content))   #两者合并后转对象
#
# print(app_conf.address.city)
