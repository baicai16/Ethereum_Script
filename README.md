# Ethereum-multiple-operations-by-Python
通过python实现Ethereum以及类似网络下的批量操作，包括主网货币转账、合约交互
## 1、generation
生成账户，账户包括序号、地址、私钥三个属性
生成方式有导入助记词与直接输入地址-私钥对两种方式
为了防止误操作，去掉了生成助记词的功能
## 2、contract
有两个功能分别是生成连接主网的端口与生成连接合约的接口
### 2.1 MainNet
与主网连接，目前可连接主网有ethereum，bsc，oec，matic，fantom
### 2.2 Contract
目前记录数据的合约有OEC下的USDT、WOKT、CELT
## 3、params
生成交易参数字典
## 4、transaction
交易的具体实现，包括主网货币的一对一、一对多转账，合约的一对一、一对多交互。
