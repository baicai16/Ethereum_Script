from web3 import Web3
from decimal import *
from contract import MainNet
from generation import Account
from contract import Contract


# 针对未开源合约的交易参数获取函数
# def getTokenData(net: MainNet, token: Contract, function, from_account: Account, to_account: Account, gas, gasprice,
#                  value, nonce):
#     """获取与合约交互的参数"""
#     tx = TxParams(net)
#     tx.chainId()
#     tx.fromAddress(from_account.address)
#     tx.getNonce(nonce)
#     tx.value(0)
#     tx.gas(gas)
#     tx.gasPrice(gasprice)
#     tx.toAddress(token.address)
#     if function == 'transfer':
#         methodid = '0xa9059cbb'
#         to_addr = to_account.address
#         value_wei = Web3.toWei(value, 'ether')
#         topic1 = '{:0>64}'.format(to_addr[2:].lower())
#         topic2 = '{:0>64}'.format(hex(value_wei)[2:])
#         data = methodid + topic1 + topic2
#         tx.data(data)
#     return tx

def d18(num):
    return Decimal(num).quantize(Decimal('.{:0>18}'.format(1)), rounding=ROUND_DOWN)


def d4(num):
    return Decimal(num).quantize(Decimal('.{:0>4}'.format(1)), rounding=ROUND_DOWN)


class TxParams:
    def __init__(self, net: MainNet):
        self.params = {}
        self.net = net

    def fromAddress(self, acc: Account):
        self.params['from'] = Web3.toChecksumAddress(acc.address)

    def getNonce(self, nonce):
        if nonce is None:
            self.params['nonce'] = self.net.web3.eth.getTransactionCount(self.params['from'])
            return self.params['nonce']
        else:
            self.params['nonce'] = nonce

    def toAddress(self, acc: Account):
        self.params['to'] = Web3.toChecksumAddress(acc.address)

    def chainId(self):
        self.params['chainId'] = self.net.chainId

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
        'from', 'to' 三个参数,并返回参考值:'value'
        """
        a = d18(amount)
        m_bal = self.net.balance(main.address)
        o_bal = self.net.balance(other.address)
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
                print('主账户%s余额不足' % self.net.currency)
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
    def __init__(self, net: MainNet, token: Contract):
        TxParams.__init__(self, net)
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
        m_bal = self.token.balance(main.address)
        o_bal = self.token.balance(other.address)
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
                print('主账户%s余额不足' % self.net.currency)
                return None, None, None
            if m_f > 2 * a_f:
                self.fromAddress(main)
                self.toAddress(other)
                self.value(a - o_bal)
                return main.num - 1, other.num - 1, a - o_bal
        elif o_f == a_f:
            return None, None, None
            
