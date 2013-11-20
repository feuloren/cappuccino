# -*- coding:utf-8 -*-

import os.path
import unicodedata
from escpos import *
import settings
from threading import Lock

where_am_i = os.path.dirname(__file__)

printing = Lock()

def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

def is_printer_present():
    try:
        p = printer.Usb(*settings.caisse_usb)
        return True
    except Exception:
        return False

def get_path_entete_billet(billetterie):
    path = os.path.join(where_am_i, '..', 'billetteries',
                        'header-'+str(billetterie)+'.png')
    if os.path.isfile(path):
        return path
    else:
        # on essaye de télécharger depuis le site du polar
        return os.path.join(where_am_i, 'logo-header.png')

def print_billet(num, nom, type, code):
    # On attend déjà que les autres impressions soient finies
    printing.acquire()

    p = printer.Usb(*settings.caisse_usb)
    p.hw('init')
    p.text(constants.TXT_ALIGN_CT)
    p.image(get_path_entete_billet(''))

    p.text('\x1d\x21\x00') # taille 1x
    p.text('\n\n')
    p.text(constants.TXT_ALIGN_LT)
    p.text(remove_accents(nom))
    p.text('\n')
    p.text(remove_accents(type))
    p.text('\n\n')
    p.text(constants.TXT_ALIGN_CT)

    # on veut imprimer un code barre CODE128 mais c'est la galère
    p.text(constants.BARCODE_TXT_OFF)
    p.text(constants.BARCODE_HEIGHT)
    p.text(constants.BARCODE_WIDTH)
    p.text('\x1d\x6b\x49\x0c') # type CODE128 + 12 octets de données
    p.text('\x7b\x42') # CODE A
    p.text(str(code))
    p.text('\n')

    p.text('\x1d\x62\x01') # text smoothing
    p.text('\x1d\x21\x44') # taille 5x
    p.text(str(num))
    p.cut()

    printing.release() # c'est fini !

def ouvrir_caisse():
    """Ouvre la caisse qui est connectée sur le port série de l'imprimante"""
    p = printer.Usb(*settings.caisse_usb)
    p.cashdraw(2)
    p.cashdraw(2)
