from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from typing import List, Tuple, Dict, Union
from slither.core.cfg.node import Node

# 测试地址
extcodesize_factory = "0xFaC100450Af66d838250EA25a389D8Cd09062629"
deploymentAddress_equal_factory = "0x0000000000FFe8B47B3e2130213B802212439497"

FACTORY_FN_NOT_FOUND_TEXT = "err: factory function not found"
ADDR_NAME_NOT_FOUND_TEXT = "err: address name not found"
BY_NEW_TEXT = "factory create contract by new Contract"
BY_CREATE_TEXT = "factory create contract by create opcode"
BY_CREATE2_TEXT = "factory create contract by create2 opcode"
CHECK_ADDR_EQUAL_TEXT = "check if actual address is equal to target address"
CHECK_ADDR_0_TEXT = "check if actual address is 0"
CHECK_EXTCODE_TEXT = "check extcodesize or extcodehash of actual address"


class FactorySecurity(AbstractDetector):
    ARGUMENT = 'factory-security'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM
    HELP = "detect factory-related factory contracts security issues"
    WIKI = "https://github.com/crytic/slither/wiki/factory-detect"
    WIKI_TITLE = "Factory Contracts Security Checker"
    WIKI_DESCRIPTION = """
    detect factory-related factory contracts security issues
    """
    WIKI_RECOMMENDATION = """
    None
    """

    def _contains_address_validation(self, node_and_statement: Tuple["Node", Union[str, Dict]]) -> List[str]:
        """
        检测在当前node的statement后是否含有对address的验证语句
        三种验证方式，见notion
        ① 检测deploymentAddress是否是0
        ② 检测create2 deploymentAddress 是否和预期计算的address一致
        ③ 检测deploymentAddress中的extcodesize是否是0
        """
        ret_text_list = []
        node, create_statement = node_and_statement
        fn_name = node.function.name
        contract_name = node.function.contract.name
        # 先在当前的node中检测③ 分为两种情况：AST形式和字符串形式的内联汇编代码
        asm_content = node.source_mapping.content
        if "extcodesize" in asm_content or "extcodehash" in asm_content:
            print(f"③{contract_name} -> {fn_name}检测deploymentAddress中extcode是否是0")
            ret_text_list.append(CHECK_EXTCODE_TEXT)
        if "create2(" in asm_content:
            ret_text_list.append(BY_CREATE2_TEXT)
        if "create(" in asm_content:
            ret_text_list.append(BY_CREATE_TEXT)
        # 在当前node的后继中检测①和②中的两种情况
        # 获取在create_statement中定义的部署地址变量名
        addr_name = ""
        if isinstance(create_statement, Dict):  # AST形式
            ast: Dict = node.inline_asm.get("AST")
            for statement in ast.get("statements"):
                if statement.get("nodeType") == "YulAssignment" and statement.get("value") == create_statement:
                    addr_name = statement.get("variableNames")[0].get("name")
                    break
        elif isinstance(create_statement, str) and ":=" in create_statement:  # 字符串形式
            addr_name = create_statement.split(":=")[0].strip()

        if addr_name:
            for succ in node.dominator_successors_recursive:
                succ_content_lines = succ.source_mapping.content.split("\n")
                for line in succ_content_lines:  # 每一行代码
                    # 第①种情况
                    line = line.replace(" ", "")
                    if "address(0)" in line and addr_name in line:
                        print(f"①{contract_name} -> {fn_name}检测deploymentAddress是否是0")
                        ret_text_list.append(CHECK_ADDR_0_TEXT)
                    # 第②种情况，仅通过create2关键字创建
                    if ("create2(" in asm_content) and \
                            (f"=={addr_name}" in line or f"{addr_name}==" in line) and \
                            ("address(0)" not in line):
                        print(f"②{contract_name} -> {fn_name}检测create2 deploymentAddress 是否和预期计算的address一致")
                        ret_text_list.append(CHECK_ADDR_EQUAL_TEXT)
                    if ".code.length" in line or ".codehash" in line:
                        print(f"③{contract_name} -> {fn_name}检测deploymentAddress中extcode是否是0")
                        ret_text_list.append(CHECK_EXTCODE_TEXT)
        else:
            print("未找到create/create2调用左值addr_name")
            ret_text_list.append(ADDR_NAME_NOT_FOUND_TEXT)
        return ret_text_list

    def detect_address_validation_after_create_contract(self, contract: Contract) -> List[str]:
        """
        工厂合约使用create/create2(底层函数)创建后,需要检查address是否为0，不为0表示创建成功
        1.筛选所有is_factory_func
        2.获取所有factory的create/create2 nodes
        3.检查当前node以及node后继中是否存在require/assert/revert的操作
        """
        factory_fns = list(filter(lambda x: x.is_factory_function, contract.functions))
        if len(factory_fns) == 0:
            print("is_factory_function函数对工厂函数的判断不完善")
            return [FACTORY_FN_NOT_FOUND_TEXT]
        ret_text_list = []
        for f in factory_fns:
            # factory_node数据结构：Tuple["Node",any(statement)]
            # factory_nodes：当前函数所有与create/create2底层函数相关的node-statement组
            # 不包含通过new关键字创建子合约的工厂，因为只有底层函数create/create2在创建失败是不会冒泡异常
            # 而new关键字在子合约创建失败后会冒泡异常
            create_op_nodes = f.create_factory_nodes + f.create2_factory_nodes
            if len(create_op_nodes) == 0:  # 如果没有create/create2 说明是通过new创建的
                ret_text_list.append(BY_NEW_TEXT)
                continue
            for node in create_op_nodes:
                ret_text_list = ret_text_list + self._contains_address_validation(node)
        return ret_text_list

    def _detect(self) -> List[Output]:
        """
        针对factory合约的安全性检查工具
        1.msg.sender in constructor
        """
        results = []
        # 过滤仅为工厂的contract
        for c in list(filter(lambda x: x.is_factory, self.contracts)):
            detect_text_list = self.detect_address_validation_after_create_contract(c)
            info: DETECTOR_INFO = [c, ' - '.join(detect_text_list), '\n']
            results.append(self.generate_result(info))
        return results
