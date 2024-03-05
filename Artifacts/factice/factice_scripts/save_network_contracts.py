import json
from api_config import api_keys, urls
import os
import requests
from utils import _fetch_create_txhash, _fetch_create_txs_by_txhash,\
    _data_preprocessing


if __name__ == '__main__':
    networks = ['goerli', 'mainnet', 'sepolia']
    for network in networks:
        _data_preprocessing(network)
