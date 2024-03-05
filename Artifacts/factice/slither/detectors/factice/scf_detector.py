import os
from typing import List

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
)
from slither.utils.output import Output
from slither.detectors.factice.utils import get_home_folder_path, copy_paste_contract_file


class SCFDetector(AbstractDetector):
    ARGUMENT = 'scf-detector'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM
    HELP = "detect smart contract factory"
    WIKI = "https://github.com/crytic/slither/wiki/factory-detect#non-standard-proxy"
    WIKI_TITLE = "Factory Detector"
    WIKI_DESCRIPTION = """
    Detecting whether a smart contract is a factory contract
    """
    WIKI_RECOMMENDATION = """
    None
    """

    def _detect(self) -> List[Output]:
        results = []
        # 指定并创建目标文件夹
        destination_folder = get_home_folder_path("factories")

        for c in self.contracts:
            # 对于每一个合约，判断是否是工厂合约
            # 如果是工厂合约，获取其路径，并将其复制到特定路径中
            if c.is_factory:
                print(c.name, c.factory_functions)
                # TODO 考虑一个.sol文件中存在多个factory contract的情况，可能需要修改文件名
                copy_paste_contract_file(c.file_scope.filename.absolute, destination_folder)

        return results


