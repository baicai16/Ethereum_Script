from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from retrying import retry
from web3 import Web3
from decimal import *
import pandas as pd
import binascii
import json
import time

# 引入链数据
with open('./data/chain_data.json', 'r', encoding='utf-8') as cd:
    chain_data = json.load(cd)


# ######################################################################################################################
#
# 账户生成
#
# ######################################################################################################################
def generateAccountbyMnemonic(mnemonic, total):
    """通过助记词生成账户池"""
    address_list = []
    private_key_list = []
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip_obj_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    bip_obj_acc = bip_obj_mst.Purpose().Coin().Account(0)
    bip_obj_chain = bip_obj_acc.Change(Bip44Changes.CHAIN_EXT)
    for num in range(total):
        bip_obj_addr = bip_obj_chain.AddressIndex(num)
        addr = bip_obj_addr.PublicKey().ToAddress()
        key = bip_obj_addr.PrivateKey().Raw().ToHex()
        address_list.append(addr)
        private_key_list.append(key)
    accounts_dict = {
        'address': address_list,
        'private_key': private_key_list
    }
    accounts = pd.DataFrame(accounts_dict)
    accounts.to_csv('./data/accounts.csv')
    with open("data/mnemonic.txt", "w") as f:
        f.write(mnemonic)
        f.close()
    output = '一共生成%s个账号,其中前5个账号为:' % total
    example = accounts['address'][0:5]
    return output, example


def validAccount(addr, key):
    """检测是否为有效账户：私钥是否能生成对应地址"""
    private_key_bytes = binascii.unhexlify(key)
    valid_addr = Bip44.FromAddressPrivKey(private_key_bytes, Bip44Coins.ETHEREUM).PublicKey().ToAddress()
    if addr == valid_addr:
        return True
    else:
        return False


def generateAccountbyInput():
    """通过输入生成账户池"""
    address_list = []
    private_key_list = []
    df = pd.DataFrame(pd.read_excel('手动输入地址私钥.xlsx'))
    total = len(df.index)
    address = df['地址']
    private_key = df['私钥']
    for num in range(total):
        addr = Web3.toChecksumAddress(address[num])
        key = private_key[num]
        if not validAccount(addr, key):
            raise ValueError('账户 %s 私钥与地址不匹配!' % (num + 1))
        address_list.append(addr)
        private_key_list.append(key)
    accounts_dict = {
        'address': address_list,
        'private_key': private_key_list
    }
    accounts = pd.DataFrame(accounts_dict)
    accounts.to_csv('./data/accounts.csv')
    output = '一共生成%s个账号,其中前5个账号为:' % total
    example = accounts['address'][0:5]
    return output, example


class Account:
    """
    账户类，储存：账户序号--num,账户地址--address,账户私钥--private_key，脚本以账户为基本操作单元
    """

    def __init__(self, num, address, private_key):
        self.num = num
        self.address = address
        self.key = private_key

    def __str__(self):
        return 'Account_%s' % self.num


def readAccount():
    """将存在csv文件里的账户池实例化"""
    df = pd.DataFrame(pd.read_csv('./data/accounts.csv'))
    total = len(df.index)
    account_list = []
    for k in range(total):
        num = k + 1
        addr = df['address'][k]
        key = df['private_key'][k]
        account = Account(num, addr, key)
        account_list.append(account)
    account_tuple = tuple(account_list)
    return account_tuple


# ######################################################################################################################
#
# 链与合约类，以及实例化
#
# ######################################################################################################################
class Chain:
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

    def balance(self, acc: Account):
        """获得所在网络的货币余额"""
        return Web3.fromWei(self.web3.eth.getBalance(Web3.toChecksumAddress(acc.address)), 'ether')


class Contract:
    """构建通用合约对象,使用参数:key_chain(链关键字),key_token(币关键字),以及存有对应链和币信息的字典文件:data"""

    def __init__(self, chain: Chain, token_key, data: dict):
        self.index = token_key
        self.symbol = data['token'][token_key]['symbol']
        self.type = data['token'][token_key]['type']
        self.address = Web3.toChecksumAddress(data['token'][token_key]['address'])
        self.abi = data['token'][token_key]['abi']
        self.contract = chain.web3.eth.contract(address=self.address, abi=self.abi)

    def __str__(self):
        return self.symbol

    def balance(self, acc: Account):
        return Web3.fromWei(self.contract.functions.balanceOf(acc.address).call(), 'ether')


# ######################################################################################################################
#
# 链与合约类，以及实例化
#
# ######################################################################################################################
# 将数字转化为ethereum的精确18位小数模式
def d18(num):
    return Decimal(num).quantize(Decimal('.{:0>18}'.format(1)), rounding=ROUND_DOWN)


def d4(num):
    return Decimal(num).quantize(Decimal('.{:0>4}'.format(1)), rounding=ROUND_DOWN)


class TxParams:
    def __init__(self, chain: Chain):
        self.params = {}
        self.chain = chain

    def fromAddress(self, acc: Account):
        self.params['from'] = Web3.toChecksumAddress(acc.address)

    def getNonce(self, nonce):
        if nonce is None:
            self.params['nonce'] = self.chain.web3.eth.getTransactionCount(self.params['from'])
            return self.params['nonce']
        else:
            self.params['nonce'] = nonce

    def toAddress(self, acc: Account):
        self.params['to'] = Web3.toChecksumAddress(acc.address)

    def chainId(self):
        self.params['chainId'] = self.chain.chainId

    def gas(self, gas):
        self.params['gas'] = gas

    def gasPrice(self, gasprice):
        """传入的gasprice单位是gwei"""
        self.params['gasPrice'] = Web3.toWei(gasprice, 'gwei')

    def value(self, value):
        """传入的value单位是ether"""
        self.params['value'] = Web3.toWei(value, 'ether')

    def data(self, data):
        self.params['data'] = data

    def txHash(self, txhash):
        self.params['txhash'] = txhash

    def method(self, method):
        self.params['method'] = method

    def evenlySend(self, amount, main: Account, other: Account):
        """
        将主账户的主网货币,以amount为参数,均匀发送到其他账户,生成:
        'from'，'to'，'value' 三个参数，并返回参考值:
        """
        a = d18(amount)
        m_bal = self.chain.balance(main)
        o_bal = self.chain.balance(other)
        m_f = d4(m_bal)
        o_f = d4(o_bal)
        a_f = d4(a)
        if o_f > a_f:
            self.fromAddress(other)
            self.toAddress(main)
            self.value(o_bal - a)
            return other.num - 1, main.num - 1, o_bal - a  # 输出顺序分别为from，to，diff
        elif o_f < a_f:
            if m_f < 2 * a_f:
                print('主账户%s余额不足' % self.chain.currency)
                return None, None, None
            if m_f > 2 * a_f:
                self.fromAddress(main)
                self.toAddress(other)
                self.value(a - o_bal)
                return main.num - 1, other.num - 1, a - o_bal
        elif o_f == a_f:
            return None, None, None

    def estGasfee(self):
        gasfee = self.params['gas'] * self.params['gasPrice']
        gasfee = Web3.fromWei(gasfee, 'ether')
        return gasfee


class WriteContract(TxParams):
    def __init__(self, chain: Chain, token: Contract):
        TxParams.__init__(self, chain)
        self.chainId()
        self.token = token

    def transfer(self, to_acc: Account, value):
        value_wei = Web3.toWei(value, 'ether')
        self.params = self.token.contract.functions.transfer(to_acc.address, value_wei).buildTransaction(self.params)

    def evenlySend(self, amount, main: Account, other: Account):
        """
        将主账户的主网货币,以amount为参数,均匀发送到其他账户,生成:
        'from', 'to' 三个参数,并返回参考值:'value'
        """
        a = d18(amount)
        m_bal = self.token.balance(main)
        o_bal = self.token.balance(other)
        m_f = d4(m_bal)
        o_f = d4(o_bal)
        a_f = d4(a)
        if o_f > a_f:
            self.fromAddress(other)
            self.toAddress(main)
            self.value(o_bal - a)
            return other.num - 1, main.num - 1, o_bal - a  # 输出顺序分别为from，to，diff
        elif o_f < a_f:
            if m_f < 2 * a_f:
                print('主账户%s余额不足' % self.chain.currency)
                return None, None, None
            if m_f > 2 * a_f:
                self.fromAddress(main)
                self.toAddress(other)
                self.value(a - o_bal)
                return main.num - 1, other.num - 1, a - o_bal
        elif o_f == a_f:
            return None, None, None


# ######################################################################################################################
#
# 交易函数
#
# ######################################################################################################################
def estGasfee(gas, gasprice):
    """预估交易费用"""
    gasfee = gas * Web3.toWei(gasprice, 'gwei')
    gasfee = Web3.fromWei(gasfee, 'ether')
    return gasfee


@retry(wait_fixed=1500, stop_max_attempt_number=10)
def searchBykey(chain: Chain, his_dict: dict, key):
    gasprice = his_dict[key]['gasPrice']
    gasused = chain.web3.eth.get_transaction_receipt(his_dict[key]['txhash'])['gasUsed']
    gasfee = gasused * gasprice
    gasfee = Web3.fromWei(gasfee, 'ether')
    return gasfee


def getGasfee(chain: Chain, his_dict: dict):
    """读取字典中的交易哈希，获得实际交易费用"""
    total_gasfee = 0
    for key in his_dict.keys():
        gasfee = searchBykey(chain=chain, his_dict=his_dict, key=key)
        total_gasfee += gasfee
    return total_gasfee


def outputTxHistory(his_dict: dict):
    """将历史交易文件存入json文件"""
    his_json = json.dumps(his_dict)
    now = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime(time.time()))
    with open('data/historiacltransaction/' + now + '_txparams.json', 'w') as json_file:
        json_file.write(his_json)
        json_file.close()


def countAsset(accounts: readAccount, token_list):
    """"""
    for acc in accounts:
        print('%s中有：' % acc)
        for token in token_list:
            if token.__class__.__name__ == 'Chain':
                print('         %s个%s.' % (token.balance(acc), token.currency))
            elif token.__class__.__name__ == 'Contract':
                print('         %s个%s.' % (token.balance(acc), token.symbol))


def singleSend(chain: Chain, from_account: Account, to_account: Account, gas, gasprice, value, nonce, data):
    """
    主网货币一对一交易
    """
    tx = TxParams(chain)
    tx.chainId()
    tx.fromAddress(from_account)
    tx.toAddress(to_account)
    tx.gas(gas)
    tx.gasPrice(gasprice)
    # 以下变量均可为None
    tx.getNonce(nonce)
    if value is None:
        tx.value(0)
    else:
        tx.value(value)
    if data is None:
        pass
    else:
        tx.data(data)
    signed_tx = chain.web3.eth.account.signTransaction(tx.params, from_account.key)  # 对交易进行签名
    tx_hash = chain.web3.toHex(chain.web3.eth.sendRawTransaction(signed_tx.rawTransaction))  # 发送交易并获取交易哈希
    print(str(from_account), '-->', str(to_account), value, chain.currency)
    print(tx_hash)
    tx.txHash(tx_hash)
    return tx.params


def multiSend(chain: Chain, accounts: readAccount, loop_times: int, main_serial: int, amount, gas, gasprice):
    """
    主网货币的多重发送
    """
    limit = min(len(accounts), loop_times, 1000)
    m = main_serial - 1
    main = accounts[m]
    history_tx = {}
    from_nonce = {}  # 变更fromaddress的nonce
    for k in range(limit):
        from_nonce[accounts[k].address] = None
    for k in range(limit):  # 交易循环
        if k == m:  # 跳过主账户
            continue
        other = accounts[k]
        tx = TxParams(chain)  # 生成交易字典
        (f, t, diff) = tx.evenlySend(amount, main, other)  # 根据amount生成from，to，value
        if f is None:  # 交易条件不支持则跳过
            continue
        else:  # 可以进行交易则调整nonce
            if from_nonce[accounts[f].address] is None:  # 如果发送地址在本轮循环中没有发送过交易，则获取nonce
                from_nonce[accounts[f].address] = tx.getNonce(None)
            else:  # 发送过则顺序加1并赋值（oec特色）
                from_nonce[accounts[f].address] += 1
            nonce = from_nonce[accounts[f].address]
            gasfee = estGasfee(gas, gasprice)  # 估算交易费用
            value = 0
            if f == k:  # 由其他账户发起交易则从转账总额中预先扣除交易费用
                value = diff - gasfee
            elif f == m:
                value = diff
            tx = singleSend(chain, accounts[f], accounts[t], gas, gasprice, value, nonce, None)
            history_tx[k] = tx  # 记录历史交易参数
    outputTxHistory(his_dict=history_tx)
    print('交易参数已储存，正在计算gasfee......')
    totalgasfee = getGasfee(chain=chain, his_dict=history_tx)
    print('本轮交易共用去gasfee：%s 个 %s' % (totalgasfee, chain.currency))


def singleTokenSend(chain: Chain, token: Contract, function: str, from_account: Account, to_account: Account,
                    gasprice, value, nonce):
    """
    根据传入信息与合约交互后生成交易字典，签名并发送交易，返回包含交易哈希的交易字典
    """
    tx = WriteContract(chain, token)
    tx.chainId()
    tx.fromAddress(from_account)
    tx.gasPrice(gasprice)
    tx.getNonce(nonce)
    tx.value(0)
    if function == 'transfer':
        tx.transfer(to_account, value)
    signed_tx = chain.web3.eth.account.signTransaction(tx.params, from_account.key)  # 对交易进行签名
    tx_hash = chain.web3.toHex(chain.web3.eth.sendRawTransaction(signed_tx.rawTransaction))  # 发送交易并获取交易哈希
    print(str(from_account), '-->', str(to_account), value, token.symbol)
    print(tx_hash)
    tx.txHash(tx_hash)
    tx.method(function)
    return tx.params


def multiTokenSend(chain: Chain, token: Contract, function: str, accounts: readAccount, loop_times: int,
                   main_serial: int, amount, gasprice):
    """
    简单的多重发送
    """
    limit = min(len(accounts), loop_times, 1000)
    m = main_serial - 1
    main = accounts[m]
    history_tx = {}
    from_nonce = {}  # 变更fromaddress的nonce
    for k in range(limit):
        from_nonce[accounts[k].address] = None
    for k in range(limit):  # 交易循环
        if k == m:  # 跳过主账户
            continue
        other = accounts[k]
        tx = WriteContract(chain, token)  # 生成交易字典
        (f, t, diff) = tx.evenlySend(amount, main, other)  # 根据amount生成from，to，value
        if f is None:  # 交易条件不支持则跳过
            continue
        else:  # 可以进行交易则调整nonce
            if from_nonce[accounts[f].address] is None:  # 如果发送地址在本轮循环中没有发送过交易，则获取nonce
                from_nonce[accounts[f].address] = tx.getNonce(None)
            else:  # 发送过则顺序加1并赋值（oec特色）
                from_nonce[accounts[f].address] += 1
            nonce = from_nonce[accounts[f].address]
            value = 0
            if f == k:  # 由其他账户发起交易则从转账总额中预先扣除交易费用
                value = diff
            elif f == m:
                value = diff
            tx = singleTokenSend(chain, token, function, accounts[f], accounts[t], gasprice, value, nonce)
            history_tx[k] = tx  # 记录历史交易参数
    outputTxHistory(his_dict=history_tx)
    print('交易参数已储存，正在计算gasfee......')
    totalgasfee = getGasfee(chain=chain, his_dict=history_tx)
    print('本轮交易共用去gasfee：%s 个 %s' % (totalgasfee, chain.currency))

