# -*- coding:utf-8 -*-

import smartcard.System
from smartcard.util import *
from smartcard.scard import *
from smartcard.ReaderMonitoring import ReaderMonitor, ReaderObserver
from smartcard.CardMonitoring import CardMonitor, CardObserver
from threading import Event

APDU_COMMAND = [0xFF, 0xCA, 0x00, 0x00, 0x00] # commande pour récupérer l'identifiant de l'étudiant

class Observer(CardObserver):
    def __init__(self, *args, **kwargs):
        super(Observer, self).__init__(*args, **kwargs)
        # Liste des requêtes en attent, normalement il n'y en a qu'une seule à la fois
        self.events = []
        # On ne veut pas louper d'évènement
        # donc au cas où personne ne soit connecté quand une carte est ajoutée
        # on l'ajoute à la file d'attente
        self.waiting = []

    def add_event(self, event):
        self.events.append(event)
        if self.waiting:
            self.send(self.waiting.pop())

    def update(self, observable, (addedcards, removedcards)):
        if addedcards:
            conn = addedcards[0].createConnection()
            conn.connect()
            # On récupère l'identifiant et on le met sous la forme qui nous intéresse
            response, sw1, sw2 = conn.transmit( APDU_COMMAND )
            card_id = ''.join([hex(x)[2:].upper() for x in response])
            self.send({'added':toHexString(addedcards[0].atr),
                       'etu':card_id})
        elif removedcards:
            self.send({'removed':toHexString(removedcards[0].atr)})

    def send(self, card):
        # On envoie la reponse à tous les évènements connectés
        if not self.events:
            self.waiting.insert(0, card)
        else:
            while self.events:
                self.events.pop().set(card)

    def reset(self):
        # Tout le monde dégage
        self.waiting = []
        while self.events:
            self.events.pop().set(False)

class ObserverEvent:
    def __init__(self):
        self.event = Event()
        self.card = None

    def set(self, card):
        self.card = card
        self.event.set()

    def wait(self, timeout=None):
        return self.event.wait(timeout)

class PCSC:
    def __init__(self):
        cardmonitor = CardMonitor()
        self.cardobserver = Observer()
        cardmonitor.addObserver(self.cardobserver)

    def is_reader_present(self):
        import smartcard.System # pour raffraichir la liste des lecteurs...
        return len(smartcard.System.readers()) >= 1

    def wait_for_smartcard(self):
        # wait for a card to arrive
        card_event = ObserverEvent()
        self.cardobserver.add_event(card_event)
        if card_event.wait(60): # une carte est arrivée (ou un reset)
            return card_event.card
        else: # timeout
            return False

    def reset(self):
        self.cardobserver.reset()

pcsc = PCSC()
