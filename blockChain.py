import hashlib
import json
from time import time

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

	@staticmethod
	def hash(block):
		block_string = json.dumps(block, sort_keys=True)
		return hashlib.sha256(block_string).hexdigest()

	@property
	def lastBlock(self):
		pass