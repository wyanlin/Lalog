# -*- coding: utf-8 -*-
"""日志筛选逻辑模块"""
import re


class LogFilter:
    """根据关键字、大小写、正则对单行日志进行匹配"""

    @staticmethod
    def matches(
        line: str, keyword: str, case_sensitive: bool, use_regex: bool
    ) -> bool:
        """
        判断日志行是否满足筛选条件。

        Args:
            line: 日志行内容
            keyword: 筛选关键字，为空则匹配所有
            case_sensitive: 是否匹配大小写
            use_regex: 是否使用正则表达式

        Returns:
            满足条件返回 True，否则 False
        """
        if not keyword or not keyword.strip():
            return True
        keyword = keyword.strip()
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                return bool(re.search(keyword, line, flags))
            except re.error:
                return False
        if case_sensitive:
            return keyword in line
        return keyword.lower() in line.lower()
