from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3
import pandas as pd
import binascii


def generateAccountbyMnemonic():
    """通过助记词生成账户,并以csv格式存入data文件夹"""
    mnemonic = str(input('请输入助记词以生成账户: '))
    total = int(input('请输入需要生成的账户总量: '))
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
    print('一共生成%s个账号,其中前5个账号为:' % total)
    print(accounts[0:5])
    accounts.to_csv('./data/accounts.csv')
    with open("data/mnemonic.txt", "w") as f:
        f.write(mnemonic)
    print('助记词与生成的账户已储存.')
    return


def validAccount(addr, key):
    """检测是否为有效账户：私钥是否能生成对应地址"""
    private_key_bytes = binascii.unhexlify(key)
    valid_addr = Bip44.FromAddressPrivKey(private_key_bytes, Bip44Coins.ETHEREUM).PublicKey().ToAddress()
    if addr == valid_addr:
        return True
    else:
        return False


def generateAccountbyInput():
    address_list = []
    private_key_list = []
    input('请将数据输入"手动输入地址私钥"的Excel文件中.\n    输入后请按任意键确认')
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
    print('一共导入%s个账户,其中前5个账户为:' % total)
    print(accounts[0:5])
    accounts.to_csv('./data/accounts.csv')
    print('导入的账户已储存.')
    return


class Account:
    """
    账户类,储存:账户序号--num,账户地址--address,账户私钥--private_key.
    """

    def __init__(self, num, address, private_key):
        self.num = num
        self.address = address
        self.key = private_key

    def __str__(self):
        return 'Account_%s' % self.num


def readAccount():
    df = pd.DataFrame(pd.read_csv('./data/accounts.csv'))
    total = len(df.index)
    account_list = []
    for k in range(total):
        num = k+1
        addr = df['address'][k]
        key = df['private_key'][k]
        account = Account(num, addr, key)
        account_list.append(account)
    account_tuple = tuple(account_list)
    return account_tuple
