
""" Main function """

def main(argsv):
    from apollon import loadChain, getChainObject
    loadChain('')
    b_chain = getChainObject()


    #b_chain.startMining("ADDRESS")
    b_chain.startWebController()
    b_chain.startDashboard()


if __name__ == "__main__": 
    # The system information is output
    import os, platform, sys, multiprocessing
    from apollon import VERSION
    print('Host Platform:', platform.system())
    print('Version:', VERSION)
    print('CPU Cores:', multiprocessing.cpu_count())
    
    # It checks if it is a valid Python version
    import sys
    if sys.version_info <= (3,): 
        print('Python version invalid')
        exit(0)

    # It is checked if all required packages are available
    print('Checked installed Python modules#')
    # ECDSA
    try: import ecdsa; print(' > ECSA: Module was installed')
    except ImportError: print(' > ECSA: was no such module installed'); exit(1)
    # Base58
    try: import base58; print(' > Base58: Module was installed')
    except ImportError: print(' > Base58: was no such module installed'); exit(1)
    # Base64
    try: import base64; print(' > Base64: Module was installed')
    except ImportError: print(' > Base64: was no such module installed'); exit(1)
    # Web3
    try: import web3; print(' > PyWeb3: Module was installed')
    except ImportError: print(' > PyWeb3: was no such module installed'); exit(1)
    # SQLITE
    try: import sqlite3; print(' > SQLite: Module was installed')
    except ImportError: print(' > SQLite: was no such module installed'); exit(1)
    # Flask
    try: import flask; print(' > Flask: Module was installed')
    except ImportError: print(' > Flask: was no such module installed'); exit(1)
    # Threading
    try: import threading; print(' > Threading: Module was installed')
    except ImportError: print(' > Threading: was no such module installed'); exit(1)
    # Hashlib
    try: import hashlib; print(' > Hashlib: Module was installed')
    except ImportError: print('There was no such module installed'); exit(1)
    # Struct
    try: import struct; print(' > Struct: Module was installed')
    except ImportError: print('There was no such module installed'); exit(1)
    # Binascii
    try: import binascii; print(' > Binascii: Module was installed')
    except ImportError: print('There was no such module installed'); exit(1)
    # PyCryptonight
    try: import pycryptonight; print(' > PyCryptonight: Module was installed')
    except ImportError: print('There was no such module installed'); exit(1)
    # time
    try: import time; print(' > Time: Module was installed')
    except ImportError: print('There was no such module installed'); exit(1)
    # Socket
    try: import socket; print(' > Socket: Module was installed')
    except ImportError: print('There was no such module installed'); exit(1)
    
    # It is checked if a Service.config was submitted
    arg_list = list()
    for i in sys.argv[1:]:
        # It is checked if it is the config file
        print(i)

    # The main function is called
    main(arg_list)
