from slither.core.declarations import Function
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function, StateVariable
from slither.core.variables import Variable
from slither.core.cfg.node import NodeType
from slither.core.expressions.identifier import Identifier
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.expression import Expression
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.member_access import MemberAccess
from typing import List, Tuple, Optional
from slither.core.cfg.node import Node

# 使用using关键字（memberAccrss形式）、whitelist、call形式调用
test_addr1 = "0x61b98acbfc23326cfe296f380b5aa3e5adcc5238"
test_addr2 = "0xf6b287ab618d7a6ec07f28421376bdfac7f5a37d"
test_aadr3 = "0xb57df14adecf6ffffb6c5e28338f6f914d25432d"

CHECK_IMP_ADDR_0_TEXT = "check_implement_address_equal_0"
CHECK_IMP_IS_CONTRACT_TEXT = "check_implement_is_contract"
CHECK_CALL_PROXY_TEXT = "check_call_proxy_contract"
CHECK_ADDRESS_IN_WHITELIST_TEXT = "check_address_in_whitelist"
INTERNAL_ADDRESS_TEXT = "is_internal_address"
EXTERNAL_ADDRESS_TEXT = "is_external_address"
IS_CLONE_BASED_FACTORY_TEXT = "is_clone_based_factory"
NO_CHECK_TEXT = "factory_no_check"


class CloneBasedFactorySecurity(AbstractDetector):
    ARGUMENT = 'clone-based-factory-security'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM
    HELP = "detect clone-based factory-related created contracts security issues"
    WIKI = "https://github.com/crytic/slither/wiki/factory-detect"
    WIKI_TITLE = "Clone-based Factory Contracts Security Checker"
    WIKI_DESCRIPTION = """
    detect clone-based factory-related created contracts security issues
    """
    WIKI_RECOMMENDATION = """
    None
    """

    def find_clone_fn_names(self) -> List[str]:
        clone_related_fn_names = []
        # 和克隆相关的合约名："Clones" & "ProxyFactory" & IProxyFactory"
        clones_contract = self.compilation_unit.get_contract_from_name("Clones")
        proxy_factory_contract = self.compilation_unit.get_contract_from_name("ProxyFactory")
        iproxy_factory_contract = self.compilation_unit.get_contract_from_name("IProxyFactory")
        if clones_contract:
            clone_related_fn_names.extend(["clone", "cloneDeterministic"])
        if proxy_factory_contract or iproxy_factory_contract:
            clone_related_fn_names.append("deployMinimal")
            if "clone" not in clone_related_fn_names:
                clone_related_fn_names.append("clone")
        return clone_related_fn_names

    def find_clone_callers_and_exp(self, clone_fn_names: List[str]) -> List[
        Tuple[FunctionContract, Expression]]:
        callers_and_callexp = []
        for c in self.contracts:
            for fn in c.functions:
                for exp in fn.expressions:
                    e = exp
                    if isinstance(e, AssignmentOperation):
                        e = e.expression_right
                    if isinstance(e, TypeConversion):
                        e = e.expression
                    if isinstance(e, CallExpression):
                        called = e.called
                        if isinstance(called, MemberAccess) and called.member_name in clone_fn_names:
                            callers_and_callexp.append((fn, exp))
                        if isinstance(called, Identifier) and called.value.name in clone_fn_names:
                            callers_and_callexp.append((fn, exp))
        return callers_and_callexp

    def check_implement_validation_in_fn(self, caller_cloneExp: Tuple[FunctionContract, Expression]) -> List[
        str]:
        """
        检查函数对implement的验证方法
        1.判断是来自内部还是外部地址
        2.判断address是否为0
        3.判断address是否为contract
        4.判断是否存在于白名单中
        5.调用该合约的方法
        """
        res_text_list = []
        caller, clone_exp = caller_cloneExp
        # proxy_name：函数返回的代理合约地址
        # imp_name: 实现合约地址
        imp_name, proxy_name = self.get_imp_proxy_name_from_clone_exp(clone_exp)
        if not (imp_name and proxy_name):
            return [INTERNAL_ADDRESS_TEXT]
        else:
            res_text_list.append(EXTERNAL_ADDRESS_TEXT)
        if self.check_address_in_whitelist(caller, imp_name):
            res_text_list.append(CHECK_ADDRESS_IN_WHITELIST_TEXT)
        for exp in caller.expressions:
            if self.check_address_zero(exp, imp_name):
                res_text_list.append(CHECK_IMP_ADDR_0_TEXT)
            if self.check_address_is_contract(exp, imp_name):
                res_text_list.append(CHECK_IMP_IS_CONTRACT_TEXT)
            if self.check_call_proxy(exp, proxy_name):
                res_text_list.append(CHECK_CALL_PROXY_TEXT)
        # 说明没有找到当前clone调用的check操作
        if len(res_text_list) == 1:
            res_text_list.append(NO_CHECK_TEXT)
        return res_text_list

    def get_imp_proxy_name_from_clone_exp(self, clone_exp: Expression) -> Tuple[str, str]:
        proxy_name, imp_name = "", ""
        if isinstance(clone_exp, AssignmentOperation):
            right = clone_exp.expression_right
            left = clone_exp.expression_left
            if isinstance(left, Identifier):
                proxy_name = left.value.name
            if isinstance(right, TypeConversion):
                right = right.expression
            if isinstance(right, CallExpression):
                if len(right.arguments) > 0:
                    # 情况1：第一个参数是address类型，则是imp_addr
                    maybe_imp_identifier = right.arguments[0]
                    if isinstance(maybe_imp_identifier, Identifier):
                        it = maybe_imp_identifier.value.type
                        if isinstance(it, ElementaryType):
                            if it.name == 'address':
                                imp_name = maybe_imp_identifier.value.name
                                return imp_name, proxy_name
                    # 情况2：使用了using关键字，将Clones库函数能力赋予address类型
                    called = right.called
                    if isinstance(called, MemberAccess):
                        calledexp = called.expression
                        if isinstance(calledexp, Identifier):
                            value = calledexp.value
                            if isinstance(value, Variable):
                                it = value.type
                                if isinstance(it, ElementaryType):
                                    if it.name == 'address':
                                        imp_name = calledexp.value.name
                                        return imp_name, proxy_name

        return imp_name, proxy_name

    def check_address_zero(self, exp: Expression, imp_name: str) -> bool:
        content = exp.source_mapping.content
        return imp_name in content and "address(0)" in content

    def check_address_is_contract(self, exp: Expression, imp_name: str) -> bool:
        content = exp.source_mapping.content
        assembly_check = "extcode" in content.lower()
        function_check = "iscontract" in content.lower()
        return imp_name in content and (assembly_check or function_check)

    def check_address_in_whitelist(self, caller: Function, imp_name: str) -> bool:
        content = caller.source_mapping.content
        return imp_name in content and "whitelist" in content.lower()

    def check_call_proxy(self, exp: Expression, proxy_name: str) -> bool:
        if isinstance(exp, AssignmentOperation):  # 有返回值的情况
            exp = exp.expression_right
        if isinstance(exp, CallExpression):  # 调用proxy对象方法
            called = exp.called
            if isinstance(called, MemberAccess):
                iexp = called.expression
                if isinstance(iexp, Identifier):
                    name = iexp.value.name
                    if name == proxy_name:
                        return True
        return False

    def _detect(self) -> List[Output]:
        """
        针对clone—based Factory合约的安全性检查工具
        1. 首先判断合约是否是基于Clone模式的？
        2. 如果是，则筛选出Clone方法以及调用该方法的所有call site
        3 判断Call Site之前：
            ① implement address是否是来自内部合约地址还是外部入参地址
            ② implement address是否有做有效性校验
        3.2 判断Clone方法内部（内联代码前后）是否有对implement的有效性检验
        """
        """
        可以用到的函数
        compilation_unit.get_contract_from_name
        """
        results = []
        clone_related_fn_names = self.find_clone_fn_names()
        if not clone_related_fn_names:
            return results  # 不是基于Clone模式的工厂
        # 获取所有调用了clone-related fn 的函数
        clone_related_callers = self.find_clone_callers_and_exp(clone_related_fn_names)
        if len(clone_related_callers) > 0:
            results.append(self.generate_result([IS_CLONE_BASED_FACTORY_TEXT, '\n']))
        # 对这些函数进行判断，是否存在验证方法
        for caller_exp in clone_related_callers:
            detect_text_list = self.check_implement_validation_in_fn(caller_exp)
            if detect_text_list:
                info: DETECTOR_INFO = [caller_exp[0], ' - '.join(detect_text_list), '\n']
                results.append(self.generate_result(info))

        return results
