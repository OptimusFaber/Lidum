from tonsdk.contract.wallet import Wallets, WalletVersionEnum

from ..config import LIDUM_MNEMONIC

LIDUM_WALLET = Wallets.from_mnemonics(mnemonics=LIDUM_MNEMONIC, version=WalletVersionEnum.v4r2, workchain=0)[3]
LIDUM_WALLET_ADDRESS = LIDUM_WALLET.address.to_string(True, True, True)
