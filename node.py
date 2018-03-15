#!/usr/bin/env python
# pylint: disable=C0103,C0111

import os
import re

from flask import Flask, jsonify, request

from uclcoin import Block, BlockChain, BlockchainException, Transaction

CHAIN_FILE = './chain.db'
if not os.path.isfile(CHAIN_FILE):
    with open(CHAIN_FILE, 'w'):
        pass

blockchain = BlockChain()
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
    pending_txns = [dict(t) for t in blockchain.pending_transactions]
    return jsonify({'transactions': pending_txns}), 200


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
def add_transaction():
    try:
        transaction = request.get_json(force=True)
        if not re.match(r'[\da-f]{66}$', transaction['destination']):
            return jsonify({'message': 'Invalid address'}), 400
        if transaction['amount'] < 0.00001:
            return jsonify({'message': 'Invalid amount. Minimum allowed amount is 0.00001'}), 400
        if 0 > transaction['fee'] < 0.00001:
            return jsonify({'message': 'Invalid fee. Minimum allowed fee is 0.00001 or zero'}), 400
        transaction = Transaction.from_dict(transaction)
        blockchain.add_transaction(transaction)
        blockchain.save_to_file(CHAIN_FILE)
        return jsonify({'message': f'Pending transaction {transaction.tx_hash} added to the Blockchain'}), 201
    except (KeyError, TypeError, ValueError):
        return jsonify({'message': f'Invalid transacton format'}), 400
    except BlockchainException as bce:
        return jsonify({'message': f'Transaction rejected: {bce.message}'}), 400


@app.route('/avgtimes', methods=['GET'])
def get_averages():
    if len(blockchain.blocks) < 101:
        return jsonify({'message': f'Not enough blocks'}), 400
    last_time = blockchain.blocks[-101].timestamp
    times = []
    for block in blockchain.blocks[-100:]:
        times.append(block.timestamp - last_time)
        last_time = block.timestamp
    response = {
        'last001': blockchain.blocks[-1].timestamp - blockchain.blocks[-2].timestamp,
        'last005': sum(times[-5:]) / 5,
        'last010': sum(times[-10:]) / 10,
        'last050': sum(times[-50:]) / 50,
        'last100': sum(times[-100:]) / 100,
        'lastIndex': blockchain.blocks[-1].index
    }
    return jsonify(response), 200


@app.route('/ranking', methods=['GET'])
def get_ranking():
    ranking = dict()
    for block in blockchain.blocks[1:]:
        cbt = block.transactions[-1]
        ranking[cbt.destination] = ranking.get(cbt.destination, 0) + 10
    ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    return jsonify(ranking), 200


if __name__ == '__main__':
    app.run()
