from typing import Optional, Dict
from etherscan import fetch_contract_name_code_compiler

"""
Deployment Chain: 表示合约的创建的链式关系
Node - Required: address & network & bytecode 
     - Optional: compilation & created_type & succ
"""


class ContractNode:
    def __init__(self, network: str, address: str, bytecode: str):
        self.network: str = network
        self.address: str = address
        self.bytecode: str = bytecode
        self.decompiled_code: Optional[str] = None
        self.created_type: str = 'create'  # 默认是以create方式被创建的
        self.succ: Optional["ContractNode"] = None
        self.prec: Optional["ContractNode"] = None

    def link_succ(self, create_type: str, succ_node: "ContractNode"):
        self.succ = succ_node
        succ_node.created_type = create_type
        succ_node.prec = self
