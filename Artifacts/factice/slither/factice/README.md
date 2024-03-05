slither detector只能处理单Slither实例的情况

如果要做跨合约分析(XCFG),需要多Slither实例

注意：由于CryticCompile本身并不支持以太坊多合约地址解析，需要修改依赖代码：
将crytic_compile.py的compile_all函数末尾添加：
```python
# 添加的elif判断
elif ',' in target:
        ts = target.split(',')
        for t in ts:
            if not is_supported(t):
                raise ValueError(f"{str(target)} is not a file or directory.")
            compilations.append(CryticCompile(t, **kwargs))
else:
    raise ValueError(f"{str(target)} is not a file or directory.")
return compilations
```
