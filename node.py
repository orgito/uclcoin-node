#!python

import os
import re

from flask import Flask, jsonify, request
from uclcoin import Block, BlockChain, Transaction, BlockchainException

CHAIN_FILE = './chain.db'
if not os.path.isfile(CHAIN_FILE):
    with open(CHAIN_FILE, 'w'):
        pass

blockchain = BlockChain()
blockchain.MINIMUM_HASH_DIFFICULTY = 5

blockchain.load_from_file(CHAIN_FILE)

app = Flask(__name__)


@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    if not re.match(r'[\da-f]{66}$', address):
        return jsonify({'message': 'Invalid address'}), 400

    balance = blockchain.get_balance(address)
    return jsonify({'balance': balance}), 200


@app.route('/pending_transactions', methods=['GET'])
def pending_transactions():
    pending_transactions = [dict(t) for t in blockchain.pending_transactions]
    return jsonify({'transactions': pending_transactions}), 200


@app.route('/block/<index>', methods=['GET'])
def get_block(index):
    block = None
    if index == 'last':
        block = blockchain.get_latest_block()
    elif index.isdigit():
        block = blockchain.get_block_by_index(int(index))
    if not block:
        return jsonify({'message': 'Block not found'}), 404

    return jsonify(dict(block)), 200


@app.route('/block', methods=['POST'])
def add_block():
    try:
        block = request.get_json(force=True)
        block = Block.from_dict(block)
        blockchain.add_block(block)
        blockchain.save_to_file(CHAIN_FILE)
        return jsonify({'message': f'Block #{block.index} added to the Blockchain'}), 201
    except (KeyError, TypeError, ValueError):
        return jsonify({'message': f'Invalid block format'}), 400
    except BlockchainException as bce:
        return jsonify({'message': f'Block rejected: {bce.message}'}), 400


@app.route('/block/minable/<address>', methods=['GET'])
def get_minable_block(address):
    if not re.match(r'[\da-f]{66}$', address):
        return jsonify({'message': 'Invalid address'}), 400

    block = blockchain.get_minable_block(address)
    response = {
        'difficulty': blockchain.calculate_hash_difficulty(),
        'block': dict(block)
    }
    return jsonify(response), 200


@app.route('/transaction', methods=['POST'])
def transaction():
    try:
        transaction = request.get_json(force=True)
        transaction = Transaction.from_dict(transaction)
        blockchain.add_transaction(transaction)
        blockchain.save_to_file(CHAIN_FILE)
        return jsonify({'message': f'Pending transaction {transaction.tx_hash} added to the Blockchain'}), 201
    except (KeyError, TypeError, ValueError):
        return jsonify({'message': f'Invalid transacton format'}), 400
    except BlockchainException as bce:
        return jsonify({'message': f'Transaction rejected: {bce.message}'}), 400


if __name__ == '__main__':
    app.run()
