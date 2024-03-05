from slither.core.declarations import Function
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function, StateVariable
from slither.core.cfg.node import NodeType
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.core.expressions.identifier import Identifier
from typing import List, Tuple, Optional
from slither.core.cfg.node import Node


class CreatedSecurity(AbstractDetector):
    ARGUMENT = 'created-security'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM
    HELP = "detect factory-related created contracts security issues"
    WIKI = "https://github.com/crytic/slither/wiki/factory-detect"
    WIKI_TITLE = "Created Contracts Security Checker"
    WIKI_DESCRIPTION = """
    detect factory-related created contracts security issues
    """
    WIKI_RECOMMENDATION = """
    None
    """

    def detect_msg_sender_in_constructor(self, contract: Contract, taint_variables: List[StateVariable]) -> bool:
        """
        在created合约中，msg.sender出现在constructor需要格外注意,因为msg.sender始终指向factory合约
        """
        if contract.constructor is not None:
            reachable_nodes = contract.constructor.all_nodes()
            taint_variables_assign = False
            msg_sender_read = False
            for rn in reachable_nodes:
                if any(v.name == "msg.sender" for v in rn.solidity_variables_read):
                    msg_sender_read = True
                exp = rn.expression
                if rn.type == NodeType.EXPRESSION and isinstance(exp, AssignmentOperation):
                    left_val = exp.expression_left
                    if isinstance(left_val, Identifier):
                        value = left_val.value
                        if isinstance(value, StateVariable):
                            taint_variables_assign = any(value is tv for tv in taint_variables)
                if taint_variables_assign and msg_sender_read:
                    return True
        return False

    def _detect(self) -> List[Output]:
        """
        针对created合约的安全性检查工具
        msg.sender in constructor
        首先找主合约，得到主合约中所有state_valuables
        如果主合约中包含可疑名称的状态变量[owner/admin/controller]，则将其记录下来
        接着遍历所有合约的constructor，如果一个合约的constructor中包含了以可疑状态变量的赋值操作，且包含msg.sender的read操作
        则记录
        """
        ERR_TEXT = "use msg.sender in created contract"  # 上层调用使用该字段进行判断，不能随意修改
        # 获取主合约的名称
        target_contract_name = list(self.compilation_unit.crytic_compile.compilation_units.keys())[0]
        # 获取主合约
        target_contract = list(filter(lambda x: x.name == target_contract_name, self.contracts))[0]
        taint_variable_names = ('owner', 'admin', 'controller')
        taint_variables = []
        for variable in target_contract.state_variables_ordered:
            if any(name in variable.name.lower() for name in taint_variable_names):
                taint_variables.append(variable)

        if len(taint_variables) == 0:
            return []
        # 包含taint_variables
        results = []
        for c in self.contracts:
            if self.detect_msg_sender_in_constructor(c, taint_variables):
                info: DETECTOR_INFO = [c.constructor, ERR_TEXT, '\n']
                results.append(self.generate_result(info))
        return results
