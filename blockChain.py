import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse
import requests
from flask import Flask, jsonify, request

class BlochChain (object):
	def __init__(self):
		self.chain = []
		self.nodes = set()
		self.current_transactions = []
		self.newBlock(previous_hash=1, proof=100)

	def resister_node(self, adress):
		parsedURL = urlparse(adress)

		if parsedURL.netloc:
			self.nodes.add(parsedURL.netloc)
		elif parsedURL.path:
			self.nodes.add(parsedURL.path)
		else:
			raise ValueError('Invalid URL')

	def valid_chain(self, chain):
		lastBlock = chain[0]
		currentIndex = 1

		while currentIndex < len(chain):
			block = chain[currentIndex]
			print(f'{lastBlock}')
			print(f'{block}')
			print("=============")

			lastBlockHash = self.hash(lastBlock)
			if block['previous_hash'] != lastBlockHash:
				return False
			if not self.valid_proof(lastBlock['proof'], block['proof'], lastBlockHash):
				return False
			
			lastBlock = block
			currentIndex += 1
		
		return True

	def resolve_conflicts(self):
		neighbours = self.nodes
		newChain = None

		maxLength = len(self.chain)

		for node in neighbours:
			response = requests.get(f'http://{node}/chain')

			if response.status_code == 200:
				length = response.json()['length']
				chain = response.json()['chain']
				if length > maxLength and self.valid_chain(chain):
					maxLength = length
					newChain = chain
		
		if newChain:
			self.chain = newChain
			return True
		
		return False


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
	def valid_proof(lastProof, proof, lastHash):
		guess = f'{lastProof}{proof}{lastHash}'.encode()
		guessHash = hashlib.sha256(guess).hexdigest()
		return guessHash[:4] == "0000"

	@staticmethod
	def hash(block):
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	@property
	def lastBlock(self):
		return self.chain[-1]

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
	proof = blockChain.proof_of_work(lastBlock)

	blockChain.new_transaction(
		sender="0",
		recipient=node_identifier,
		amount=1,
	)

	previous_hash = blockChain.hash(lastBlock)
	block = blockChain.newBlock(proof, previous_hash)

	res = {
		'message': '新しいブロックを採掘しました',
		'index': block['index'],
		'transactions': block['transactions'],
		'proof': block['proof'],
		'previous_hash': block['previous_hash'],
	}

	return jsonify(res), 200

@app.route('/chain', methods=['GET'])
def fullChain():
	res = {
		'chain': blockChain.chain,
		'length': len(blockChain.chain),
	}
	return jsonify(res), 200

@app.route('/nodes/register', methods=['POST'])
def node_register():
	print("err")
	values = request.get_json()

	nodes = values.get('nodes')
	if nodes is None:
		return "Error: 無効なノードリストです", 400
	
	for node in nodes:
		blockChain.resister_node(node)

	res = {
		'message': 'ノードが追加されました',
		'chain': blockChain.chain
	}
	return jsonify(res), 200

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
	replaced = blockChain.resolve_conflicts()

	if replaced:
		res = {
			'message': 'チェーンが置き換えられました',
			'chain': blockChain.chain
		}
	else:
		res = {
			'message': 'チェーンが確認されました',
			'chain': blockChain.chain
		}

	return jsonify(res), 200


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=3001)