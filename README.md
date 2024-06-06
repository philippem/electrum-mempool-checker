# electrum-mempool-checker

Retrieves mempool transactions from bitcoin core, then checks that they are known by an electrum server.

Prints information about missing transactions.

### Requires

1. bitcoin core daemon, any chain, providing rpc with user/password
2. electrum daemon

### Usage

#### Create a virtualenv
```
python --virtualenv --python=python3 ./venv
source ./venv/activate
pip install -r requirements.txt
```

#### Running

```
 % python check.py --bitcoin-rpc-host 127.0.0.1 --bitcoin-rpc-port 8332 --bitcoin-rpc-user rpcuser --bitcoin-rpc-password rpcpassword --electrum-host 127.0.0.1 --electrum-port 50001
2024-06-06T13:01:53-0700 calling getrawmempool(verbose=True)
2024-06-06T13:02:07-0700 retrieved 128843 mempool transactions in 13.9 seconds
2024-06-06T13:02:07-0700 retrieving transactions from electrs using blockchain.transaction.get
2024-06-06T13:02:12-0700 retrieved=24303 pending=103540 missing=0 (0.00000000%)
2024-06-06T13:02:17-0700 retrieved=49244 pending=78598 missing=1 (0.00002031%)
2024-06-06T13:02:22-0700 retrieved=81423 pending=46419 missing=1 (0.00001228%)
2024-06-06T13:02:27-0700 retrieved=112765 pending=15077 missing=1 (0.00000887%)
2024-06-06T13:02:32-0700 retrieved=128842 pending=0 missing=1 (0.00000776%)
-2854.733811855316 {'fees': {'base': Decimal('0.00009483'), 'modified': Decimal('0.00009483'), 'ancestor': Decimal('0.00012444'), 'descendant': Decimal('0.00009483')}, 'vsize': 327, 'weight': 1305, 'fee': Decimal('0.00009483'), 'modifiedfee': Decimal('0.00009483'), 'time': 1717701298, 'height': 846778, 'descendantcount': 1, 'descendantsize': 327, 'descendantfees': 9483, 'ancestorcount': 2, 'ancestorsize': 468, 'ancestorfees': 12444, 'wtxid': '7665bc51764aa510cc8d79b971209d51247a4ae8e23fdc67f525ffdc2763f9c4', 'depends': ['6ff10bbfcc66c20fb572bcc9fda2582f5717bf610d9ff28334217efec50f287e'], 'spentby': [], 'bip125-replaceable': True, 'unbroadcast': False}
```
