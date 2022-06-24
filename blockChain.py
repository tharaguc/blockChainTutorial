import hashlib
from importlib.metadata import requires
import json
from time import time
from textwrap import dedent
from uuid import uuid4
from flask import Flask, jsonify, request

class BlochChain (object):
	def __init__(self):
		self.chain = []
		self.current_transactions = []
		self.newBlock(previous_hash=1, proof=100)

	def newBlock(self, proof, previous_hash=None):
		block = {
			'index': len(self.chain) + 1,
			'timestamp': time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1])
		}
		self.current_transactions = []
		self.chain.append(block)
		return block

	def new_transaction(self, sender, recipient, amount):
		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount,
		})
		return self.lastBlock['index'] + 1

	def proof_of_work(self, lastProof):
		proof = 0
		while self.valid_proof(lastProof, proof) is False:
			proof += 1
		return proof

	@staticmethod
	def valid_proof(lastProof, proof):
		guess = f'{lastProof}{proof}'.encode()
		guessHash = hashlib.sha256(guess).hexdigest()
		return guessHash[:4] == "0000"

	@staticmethod
	def hash(block):
		block_string = json.dumps(block, sort_keys=True)
		return hashlib.sha256(block_string).hexdigest()

	@property
	def lastBlock(self):
		pass

#---------------------#

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockChain = BlochChain()

@app.route('/transactions/new', methods=['POST'])
def new_transactions():
	json = request.get_json()

	required = ['sender', 'recipient', 'amount']
	if not all(k in json for k in required):
		return 'Missing.', 400
	
	index = blockChain.new_transaction(json['sender'], json['recipient'], json['amount'])
	res = {
		'message': f'Add to {index}.'
	}
	return jsonify(res), 201

@app.route('/mine', methods=['GET'])
def mine():
	lastBlock = blockChain.lastBlock
	lastProof = lastBlock['proof']
	proof = blockChain.proof_of_work(lastProof)

	blockChain.new_transaction()
	return 'Mine a new block.'

@app.route('/chain', methods=['GET'])
def fullChain():
	res = {
		'chain': blockChain.chain,
		'length': len(blockChain.chain),
	}
	return jsonify(res), 200

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)