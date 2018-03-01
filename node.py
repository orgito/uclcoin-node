#!python

import re

from flask import Flask, jsonify
from uclcoin import Block, BlockChain, Transaction

blockchain = BlockChain()

app = Flask(__name__)


@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    if not re.match(r'[\da-f]{66}$', address):
        return jsonify({'message': 'Invalid address'}), 400

    balance = blockchain.get_balance(address)
    return jsonify({'balance': balance}), 200


@app.route('/balance_unconfirmed/<address>', methods=['GET'])
def get_balance_unconfirmed(address):
    if not re.match(r'[\da-f]{66}$', address):
        return jsonify({'message': 'Invalid address'}), 400

    balance = blockchain.get_balance_unconfirmed(address)
    return jsonify({'unconfirmed_balance': balance}), 200


@app.route('/block/<index>', methods=['GET'])
def get_block(index):
    if index == 'last':
        block = blockchain.get_latest_block()
    else:
        block = blockchain.get_block_by_index(int(index))
    if not block:
        return jsonify({'message': 'Block not found'}), 404

    return jsonify(dict(block)), 200


@app.route('/block/minable/<address>', methods=['GET'])
def get_minable_block(address):
    if not re.match(r'[\da-f]{66}$', address):
        return jsonify({'message': 'Invalid address'}), 400

    block = blockchain.get_minable_block(address)
    return jsonify(dict(block)), 200
