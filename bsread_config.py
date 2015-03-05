#!/usr/bin/env python

from CaChannel import CaChannel, CaChannelException

if __name__ == "__main__":

    try:
        chan = CaChannel('ARIDI-PCT:CURRENT')
        chan.searchw()
        # chan.putw(12)
        print chan.getw()
    except CaChannelException as e:
        print e.status
