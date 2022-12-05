from typing import Callable, Coroutine

from ipv8.types import Peer

from descan.eva.exceptions import TransferException
from descan.eva.result import TransferResult

TransferCompleteCallback = Callable[[TransferResult], Coroutine]
TransferErrorCallback = Callable[[Peer, TransferException], Coroutine]
TransferRequestCallback = Callable[[Peer, bytes], Coroutine]
