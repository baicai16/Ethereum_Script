from generation import Account, readAccount
from contract import MainNet, Contract
from retrying import retry
from params import TxParams, WriteContract
from web3 import Web3
import time
import json


def estGasfee(gas, gasprice):
    """预估交易费用"""
    gasfee = gas * Web3.toWei(gasprice, 'gwei')
    gasfee = Web3.fromWei(gasfee, 'ether')
    return gasfee


@retry(wait_fixed=1500, stop_max_attempt_number=10)
def searchBykey(net: MainNet, his_dict: dict, key):
    gasprice = his_dict[key]['gasPrice']
    gasused = net.web3.eth.get_transaction_receipt(his_dict[key]['txhash'])['gasUsed']
    gasfee = gasused * gasprice
    gasfee = Web3.fromWei(gasfee, 'ether')
    return gasfee


def getGasfee(net: MainNet, his_dict: dict):
    """读取字典中的交易哈希，获得实际交易费用"""
    total_gasfee = 0
    for key in his_dict.keys():
        gasfee = searchBykey(net=net, his_dict=his_dict, key=key)
        total_gasfee += gasfee
    return total_gasfee


def outputTxHistory(his_dict: dict):
    """将历史交易文件存入json文件"""
    his_json = json.dumps(his_dict)
    now = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime(time.time()))
    with open('data/historiacltransaction/' + now + '_txparams.json', 'w') as json_file:
        json_file.write(his_json)


def singleSend(net: MainNet, from_account: Account, to_account: Account, gas, gasprice, value, nonce, data):
    """
    这是最基础的交易类型，变更data即可变为
    根据传入信息生成交易字典，签名并发送交易，返回包含交易哈希的交易字典
    """
    tx = TxParams(net)
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
    signed_tx = net.web3.eth.account.signTransaction(tx.params, from_account.key)  # 对交易进行签名
    tx_hash = net.web3.toHex(net.web3.eth.sendRawTransaction(signed_tx.rawTransaction))  # 发送交易并获取交易哈希
    print(str(from_account), '-->', str(to_account), value, net.currency)
    print(tx_hash)
    tx.txHash(tx_hash)
    return tx.params


def multiSend(net: MainNet, accounts: readAccount, loop_times: int, main_serial: int, amount, gas, gasprice):
    """
    简单的多重发送
    """
    limit = min(len(accounts), loop_times, 100)
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
        tx = TxParams(net)  # 生成交易字典
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
            tx = singleSend(net, accounts[f], accounts[t], gas, gasprice, value, nonce, None)
            history_tx[k] = tx  # 记录历史交易参数
    outputTxHistory(his_dict=history_tx)
    print('交易参数已储存，正在计算gasfee......')
    totalgasfee = getGasfee(net=net, his_dict=history_tx)
    print('本轮交易共用去gasfee：%s 个 %s' % (totalgasfee, net.currency))


def singleTokenSend(net: MainNet, token: Contract, function: str, from_account: Account, to_account: Account,
                    gasprice, value, nonce):
    """
    根据传入信息与合约交互后生成交易字典，签名并发送交易，返回包含交易哈希的交易字典
    """
    tx = WriteContract(net, token)
    tx.chainId()
    tx.fromAddress(from_account)
    tx.gasPrice(gasprice)
    tx.getNonce(nonce)
    tx.value(0)
    if function == 'transfer':
        tx.transfer(to_account, value)
    signed_tx = net.web3.eth.account.signTransaction(tx.params, from_account.key)  # 对交易进行签名
    tx_hash = net.web3.toHex(net.web3.eth.sendRawTransaction(signed_tx.rawTransaction))  # 发送交易并获取交易哈希
    print(str(from_account), '-->', str(to_account), value, token.symbol)
    print(tx_hash)
    tx.txHash(tx_hash)
    tx.method(function)
    return tx.params


def multiTokenSend(net: MainNet, token: Contract, function: str, accounts: readAccount, loop_times: int,
                   main_serial: int, amount, gasprice):
    """
    简单的多重发送
    """
    limit = min(len(accounts), loop_times, 100)
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
        tx = WriteContract(net, token)  # 生成交易字典
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
            tx = singleTokenSend(net, token, function, accounts[f], accounts[t], gasprice, value, nonce)
            history_tx[k] = tx  # 记录历史交易参数
    outputTxHistory(his_dict=history_tx)
    print('交易参数已储存，正在计算gasfee......')
    totalgasfee = getGasfee(net=net, his_dict=history_tx)
    print('本轮交易共用去gasfee：%s 个 %s' % (totalgasfee, net.currency))
