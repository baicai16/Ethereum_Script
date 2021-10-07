import json
from web3 import Web3

# 引入存有
with open('./data/chain_data.json', 'r', encoding='utf-8') as cd:
    chain_data = json.load(cd)
with open('./data/oec_contract.json', 'r', encoding='utf-8') as oc:
    oec_contract = json.load(oc)


class MainNet:
    """以<类以太坊>的元信息,生成接入RPC的端口"""

    def __init__(self, chain_key):
        self.key = chain_key
        self.currency = chain_data[self.key]["currency"]
        self.nickname = chain_data[self.key]["nickname"]
        self.explorer = chain_data[self.key]["blockExplorerUrl"]
        self.rpc = chain_data[self.key]["rpcUrl"]
        web3 = Web3(Web3.HTTPProvider(self.rpc))
        if Web3.isConnected(web3):
            self.web3 = web3
            print('RPC连接成功')
        else:
            print('%s-->RPC连接失败' % self.key)
        self.chainId = self.web3.eth.chainId

    def __str__(self):
        return self.nickname

    def balance(self, address):
        """获得所在网络的货币余额"""
        return Web3.fromWei(self.web3.eth.getBalance(Web3.toChecksumAddress(address)), 'ether')


class Contract:
    """构建通用合约对象,使用参数:key_chain(链关键字),key_token(币关键字),以及存有对应链和币信息的字典文件:data"""

    def __init__(self, net: MainNet, token_key, data: dict):
        self.index = token_key
        self.symbol = data['token'][token_key]['symbol']
        self.type = data['token'][token_key]['type']
        self.address = Web3.toChecksumAddress(data['token'][token_key]['address'])
        self.abi = data['token'][token_key]['abi']
        self.contract = net.web3.eth.contract(address=self.address, abi=self.abi)

    def __str__(self):
        return self.symbol

    def balance(self, address):
        return Web3.fromWei(self.contract.functions.balanceOf(address).call(), 'ether')


class OecContract(Contract):
    def __init__(self, token_key):
        Contract.__init__(self, MainNet('oec'), token_key, oec_contract)
